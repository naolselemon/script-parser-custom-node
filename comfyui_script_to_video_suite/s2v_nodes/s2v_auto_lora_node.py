import json
import folder_paths
from .gemini_relay_client import ask_gemini_via_relay

class AutoLoraLoader_S2V:
    """
    Analyzes an image prompt using Gemini to extract character names.
    It matches found names against a HARDCODED list of LoRA files.
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

    def process_auto_loras(self, image_prompt, lora_strength):
        
        # --- CONFIGURATION: HARDCODED LORA MAPPING ---
        # Format: "Character Name (lowercase)": "Actual Filename.safetensors"
        LORA_MAP = {
            "isaac": "isaac_15.safetensors",
            # Add more here later, e.g., "neo": "neo_v1.safetensors"
        }
        # ---------------------------------------------
        # TODO: Find better lora maping methods 
        
        system_instruction = (
            "You are an entity extraction assistant. "
            "Identify the main character names in the text below. "
            "Return ONLY a valid JSON list of strings. "
            "Example output: [\"Isaac\", \"Neo\"] "
            "If no specific characters are found, return []. "
            "Do not add markdown formatting, explanations, or code blocks."
        )
        # TODO: make system instruction more robust and also add validation techniques like regex expression.

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