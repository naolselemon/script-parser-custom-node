import json
import folder_paths
import os
import re
from .gemini_relay_client import ask_gemini_via_relay

class AutoLoraLoader_S2V:
    

    _cached_map = None  
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
        Uses ComfyUI's internal scanner to handle subfolders automatically.
        """
        print("AutoLoRA: Scanning LoRA folder for dynamic mapping...")
        auto_map = {}
        
        # Get list of all LoRAs (includes subfolders like 'characters/isaac.safetensors')
        available_loras = folder_paths.get_filename_list("loras")
        print(available_loras)
        for relative_path in available_loras:
            
            filename_only = os.path.basename(relative_path)
            name_no_ext = os.path.splitext(filename_only)[0]
            
          
            patterns_to_remove = [
                r'\blora\b', r'\bloras\b', r'^lora_', r'^loras_', r'_lora\b', r'_loras\b',
                r'v\d+\b', r'_v\d+\b', r'version\d+\b', r'_version\d+\b',
                r'rev\d+\b', r'_rev\d+\b', r'final\b', r'last\b', r'end\b',
                r'put_loras_here'
            ]
            
            clean_name = name_no_ext
            for pattern in patterns_to_remove:
                clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)
            
            
            clean_name = re.sub(r'[_-]+', ' ', clean_name).strip().lower()

            
            if clean_name and len(clean_name) > 1:
                if clean_name not in auto_map:
                    auto_map[clean_name] = relative_path
                
                raw_key = name_no_ext.lower()
                if raw_key not in auto_map:
                    auto_map[raw_key] = relative_path

        return auto_map

    def build_smart_lora_map(self):
        """
        Builds the final map. Hardcoded entries take priority over Auto-scanned ones.
        """
        if self._cached_map is not None:
            return self._cached_map

        AUTO_MAP = self.create_map_from_lora_folder()
        
        HARDCODED_MAP = {
            "isaac": "isaac_15.safetensors",
            # "gertie": "characters/gertie_v1.safetensors"
        }

        SMART_MAP = AUTO_MAP.copy()
        for char, filename in HARDCODED_MAP.items():
            SMART_MAP[char] = filename
            print(f"AutoLoRA: Enforcing hardcoded map '{char}' -> '{filename}'")

        self._cached_map = SMART_MAP
        print(f"✅ AutoLoRA: SmartMap ready with {len(SMART_MAP)} entries.")
        return SMART_MAP

    def process_auto_loras(self, image_prompt, lora_strength):
        LORA_MAP = self.build_smart_lora_map()

        # System prompt for the Relay (Gemini)
        system_instruction = (
            "You are an entity extraction assistant. "
            "Identify the main character names in the text below. "
            "Return ONLY a valid JSON list of strings. "
            "Example output: [\"Isaac\", \"Neo\"]. "
            "If no specific characters are found, return []. "
            "Ignore generic terms like 'man', 'woman', 'soldier', 'robot'. "
            "Only return Proper Nouns."
        )

        full_query = f"{system_instruction}\n\nText to analyze: {image_prompt}"
        print(f"🕵️ AutoLoRA: Analyzing prompt: {image_prompt[:50]}...")

        character_names = []
        try:
            # Call Gemini
            response_text = ask_gemini_via_relay(full_query)
            
            if response_text.startswith("Error:"):
                print(f"❌ AutoLoRA: Relay Error - {response_text}")
                return ([],)

            # Parse JSON
            cleaned_json = response_text.replace("```json", "").replace("```", "").strip()
            character_names = json.loads(cleaned_json)

            if not isinstance(character_names, list):
                print(f"⚠️ AutoLoRA: LLM returned valid JSON but not a list: {character_names}")
                return ([],)

        except Exception as e:
            print(f"⚠️ AutoLoRA: Extraction failed ({e}). Loading 0 LoRAs.")
            return ([],)

        if not character_names:
            print("ℹ️ AutoLoRA: No characters found in text.")
            return ([],)

        print(f"🤖 AutoLoRA: Gemini found entities: {character_names}")

        # Verify files exist before adding to stack
        files_on_disk = folder_paths.get_filename_list("loras")
        lora_stack = []

        for char_name in character_names:
            clean_name = char_name.lower().strip()
            
            if clean_name in LORA_MAP:
                target_filename = LORA_MAP[clean_name]
                
                if target_filename in files_on_disk:
                    print(f"✅ AutoLoRA: Mapping '{char_name}' -> '{target_filename}'")
                    # Stack Format: (filename, model_strength, clip_strength)
                    lora_stack.append((target_filename, lora_strength, lora_strength))
                else:
                    print(f"❌ AutoLoRA: Mapped '{char_name}' to '{target_filename}', but file is missing from disk!")
            else:
                print(f"ℹ️ AutoLoRA: Character '{char_name}' found in text, but no matching LoRA file in map.")
        print(lora_stack)
        return (lora_stack,)