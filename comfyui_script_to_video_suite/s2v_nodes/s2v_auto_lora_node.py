import json
import folder_paths
from .gemini_relay_client import ask_gemini_via_relay
import os
import re
class AutoLoraLoader_S2V:
    """
    Analyzes an image prompt using Gemini to extract character names.
    It matches found names against a HARDCODED and also loras listed in the loras folder.
    If no character is found, it loads nothing.
    """

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
        Build a map of character_name -> filename from all LoRA files on disk.
        Cleans filenames by removing version numbers, 'lora' prefixes/suffixes, and other noise.
        """
        auto_map = {}
        files_on_disk = folder_paths.get_filename_list("loras")
        
        for filename in files_on_disk:
            name = os.path.splitext(filename)[0]
            patterns_to_remove = [
                r'\blora\b', r'\bloras\b', r'^lora_', r'^loras_', r'_lora\b', r'_loras\b',
                r'v\d+\b', r'_v\d+\b', r'version\d+\b', r'rev\d+\b', r'final\b', r'last\b', r'end\b',
                r'[_-]?\d+$', r'put_loras_here'
            ]
            for pattern in patterns_to_remove:
                name = re.sub(pattern, '', name, flags=re.IGNORECASE)
            name = re.sub(r'[_-]+', ' ', name).strip()
            if name and len(name) > 1:
                key = name.lower()
                if key in auto_map:
                    print(f"⚠️  Collision detected: '{filename}' and '{auto_map[key]}' both map to character name '{key}'. Ignoring '{filename}'.")
                else:
                    auto_map[key] = filename
        return auto_map

    def build_smart_lora_map(self):
        """
        Build the final LoRA mapping (SMART_MAP) with deduplication:

        1. Hardcoded mappings take priority.
        2. Auto-mapped characters are added only if their filename isn't already used.
        3. Prevents duplicate filenames even if multiple characters would map to the same file.
        """
        AUTO_MAP = self.create_map_from_lora_folder()

        # --- CONFIGURATION: HARDCODED LORA MAPPING ---
        # Format: "Character Name (lowercase)": "Actual Filename.safetensors"
        HARDCODED_MAP = {
            "isaac": "isaac_15.safetensors",
            # Add more here later, e.g., "neo": "neo_v1.safetensors"
        }

        SMART_MAP = {}
        used_files = set(filename.lower() for filename in HARDCODED_MAP.values())

        # Add hardcoded entries
        for char_name, filename in HARDCODED_MAP.items():
            SMART_MAP[char_name] = filename
            print(f"🛡️  Using hardcoded '{char_name}' -> '{filename}'")

        # Add auto-mapped only if filename not already used
        for char_name, filename in AUTO_MAP.items():
            if filename.lower() not in used_files:
                SMART_MAP[char_name] = filename
                used_files.add(filename.lower())
                print(f"🔍 Auto-mapped '{char_name}' -> '{filename}'")

        print(f"✅ SmartMap: Final mapping has {len(SMART_MAP)} entries")
        return SMART_MAP

    def process_auto_loras(self, image_prompt, lora_strength):
        LORA_MAP = self.build_smart_lora_map()
        
        system_instruction = (
            "You are an entity extraction assistant. "
            "Identify the main character names in the text below. "
            "Return ONLY a valid JSON list of strings. "
            "Example output: [\"Isaac\", \"Neo\"] "
            "If no specific characters are found, return []. "
            "Do not add markdown formatting, explanations, or code blocks."
            "Ignore generic terms like 'man', 'woman', 'person', 'character'. "
            "If multiple mentions of same character, include only once. "
            "Do NOT hallucinate names not present. "
            "Do NOT include descriptions, attributes, or roles."
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
            # Validate JSON format using regex before parsing
            json_pattern = r'^\s*\[.*\]\s*$'
            if not re.match(json_pattern, cleaned_json):
                print(f"⚠️ AutoLoRA: Response doesn't match expected JSON list format: {cleaned_json}")
                return ([],)

            character_names = json.loads(cleaned_json)
            
            if not isinstance(character_names, list):
                print(f"⚠️ AutoLoRA: LLM returned valid JSON but not a list: {character_names}")
                return ([],)

        except Exception as e:
            #
            print(f"⚠️ AutoLoRA: Could not extract characters ({e}). Loading 0 LoRAs.")
            return ([],)

        if not character_names:
            print("ℹ️ AutoLoRA: No characters found in prompt. No LoRAs will be loaded.")
            return ([],)

        print(f"🤖 AutoLoRA: Gemini found: {character_names}")

       
        files_on_disk = folder_paths.get_filename_list("loras")
        lora_stack = []

        for char_name in character_names:
            clean_name = char_name.lower().strip()
            
            if clean_name in LORA_MAP:
                target_filename = LORA_MAP[clean_name]
                
                if target_filename in files_on_disk:
                    print(f"✅ AutoLoRA: Mapping '{char_name}' -> '{target_filename}'")
                    lora_stack.append((target_filename, lora_strength, lora_strength))
                else:
                    print(f"❌ AutoLoRA: Character '{char_name}' maps to '{target_filename}', but that file is missing from the models/loras folder!")
            else:
                print(f"ℹ️ AutoLoRA: Character '{char_name}' found, but not in LORA_MAP. Ignoring.")

        return (lora_stack,)
