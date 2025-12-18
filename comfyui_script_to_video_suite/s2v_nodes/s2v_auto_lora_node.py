import json
import folder_paths
import comfy.sd
import os
import re
from .gemini_relay_client import ask_gemini_via_relay

class AutoLoraLoader_S2V:
    """
    Analyzes an image prompt using Gemini to extract character names.
    Matches names against a Smart Map (Hardcoded + Auto-scanned files).
    Outputs a LORA_STACK.
    """

    _cached_map = None  # Class-level cache

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_prompt": ("STRING", {"multiline": True, "dynamicPrompts": False}),
                "lora_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.1}),
            },
        }

    RETURN_TYPES = ("LORA_STACK",)
    RETURN_NAMES = ("lora_stack",)
    FUNCTION = "process_auto_loras"
    CATEGORY = "Script To Video Suite"

    @staticmethod
    def create_map_from_lora_folder():
        """
        Builds a map of 'clean_name' -> 'relative/path/filename.safetensors'.
        HANDLES SUBFOLDERS AUTOMATICALLY.
        """
        print("📂 AutoLoRA: Scanning LoRA folder (and subfolders) for dynamic mapping...")
        auto_map = {}
        
        # 1. Get the list of ALL LoRAs (Recursive)
        # ComfyUI returns relative paths, e.g. ['isaac.safetensors', 'anime/style_v1.safetensors']
        available_loras = folder_paths.get_filename_list("loras")
        print("################################", available_loras)
        for relative_path in available_loras:
            # 2. Extract just the filename for cleaning
            # e.g. "characters/scifi/isaac_v1.safetensors" -> "isaac_v1.safetensors"
            filename_only = os.path.basename(relative_path)
            name_no_ext = os.path.splitext(filename_only)[0]
            
            # 3. Regex Cleaning (Remove 'lora', versions, underscores)
            patterns_to_remove = [
                r'\blora\b', r'\bloras\b', r'^lora_', r'^loras_', r'_lora\b', r'_loras\b',
                r'v\d+\b', r'_v\d+\b', r'version\d+\b', r'_version\d+\b',
                r'rev\d+\b', r'_rev\d+\b', r'final\b', r'last\b', r'end\b',
                r'put_loras_here'
            ]
            
            clean_name = name_no_ext
            for pattern in patterns_to_remove:
                clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)
            
            # Remove underscores and extra spaces -> "isaac v1" -> "isaac"
            clean_name = re.sub(r'[_-]+', ' ', clean_name).strip().lower()

            # 4. Map the clean name to the FULL relative path
            if clean_name and len(clean_name) > 1:
                if clean_name not in auto_map:
                    # Key: "isaac" -> Value: "characters/scifi/isaac_v1.safetensors"
                    auto_map[clean_name] = relative_path
                
                # OPTIONAL: Also map the raw filename just in case logic was too aggressive
                raw_key = name_no_ext.lower()
                if raw_key not in auto_map:
                    auto_map[raw_key] = relative_path

        return auto_map

    def build_smart_lora_map(self):
        """
        Builds the final map. Hardcoded entries overwrite Auto-scanned entries.
        """
        if self._cached_map is not None:
            return self._cached_map

        # 1. Get Auto Map (Recursively scanned)
        AUTO_MAP = self.create_map_from_lora_folder()
        
        # 2. Define Hardcoded Map (Highest Priority)
        # Use simple filenames or relative paths if you know them
        HARDCODED_MAP = {
            "isaac": "isaac_15.safetensors",
            # If Isaac was in a folder, you could write: "isaac": "chars/isaac_15.safetensors"
        }

        # 3. Merge (Hardcoded wins)
        SMART_MAP = AUTO_MAP.copy()
        for char, filename in HARDCODED_MAP.items():
            SMART_MAP[char] = filename
            print(f"🛡️ AutoLoRA: Enforcing hardcoded map '{char}' -> '{filename}'")

        self._cached_map = SMART_MAP
        print(f"✅ AutoLoRA: SmartMap ready with {len(SMART_MAP)} entries.")
        return SMART_MAP

    def process_auto_loras(self, image_prompt, lora_strength):
        LORA_MAP = self.build_smart_lora_map()

        system_instruction = (
            "You are an entity extraction assistant. "
            "Identify the main character names in the text below. "
            "Return ONLY a valid JSON list of strings. "
            "Example output: [\"Isaac\", \"Neo\"]. "
            "If no specific characters are found, return []. "
            "Ignore generic terms like 'man', 'woman', 'soldier'. "
        )

        full_query = f"{system_instruction}\n\nText to analyze: {image_prompt}"
        print(f"🕵️ AutoLoRA: Analyzing prompt: {image_prompt[:50]}...")

        character_names = []
        try:
            response_text = ask_gemini_via_relay(full_query)
            if response_text.startswith("Error:"):
                print(f"❌ AutoLoRA: Relay Error - {response_text}")
                return ([],)

            cleaned_json = response_text.replace("```json", "").replace("```", "").strip()
            character_names = json.loads(cleaned_json)

            if not isinstance(character_names, list):
                return ([],)

        except Exception as e:
            print(f"⚠️ AutoLoRA: Extraction failed ({e}). Loading 0 LoRAs.")
            return ([],)

        if not character_names:
            print("ℹ️ AutoLoRA: No characters found.")
            return ([],)

        print(f"🤖 AutoLoRA: Gemini found: {character_names}")

        # Get actual files on disk to verify existence (includes subfolders)
        files_on_disk = folder_paths.get_filename_list("loras")
        lora_stack = []

        for char_name in character_names:
            clean_name = char_name.lower().strip()
            
            if clean_name in LORA_MAP:
                target_filename = LORA_MAP[clean_name]
                
                # Check if file physically exists before adding to stack
                if target_filename in files_on_disk:
                    print(f"✅ AutoLoRA: Mapping '{char_name}' -> '{target_filename}'")
                    lora_stack.append((target_filename, lora_strength, lora_strength))
                else:
                    print(f"❌ AutoLoRA: Mapped '{char_name}' to '{target_filename}', but file is missing!")
            else:
                print(f"ℹ️ AutoLoRA: Character '{char_name}' not found in LoRA map.")

        return (lora_stack,)


# --- APPLICATOR NODE ---

class LoraStackApplicator_S2V:
    """
    Takes the LORA_STACK and applies the actual files to the Model/CLIP.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora_stack": ("LORA_STACK",),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP")
    RETURN_NAMES = ("model", "clip")
    FUNCTION = "apply_stack"
    CATEGORY = "Script To Video Suite"

    def apply_stack(self, model, clip, lora_stack):
        if not lora_stack:
            return (model, clip)

        print(f"🔥 Applicator: Applying {len(lora_stack)} LoRAs...")

        for lora_name, strength_model, strength_clip in lora_stack:
            # get_full_path automatically resolves subfolders given the relative path
            lora_path = folder_paths.get_full_path("loras", lora_name)
            if lora_path is None:
                print(f"❌ Error: LoRA file not found: {lora_name}")
                continue
            
            print(f"   -> Loading: {lora_name}")
            model, clip = comfy.sd.load_lora_for_models(
                model, clip, lora_path, strength_model, strength_clip
            )

        return (model, clip)