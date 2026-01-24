import json
import os
import folder_paths
from .gemini_relay_client import ask_gemini_via_relay



def load_prompt_from_file(filename: str) -> str:
    """
    Loads text content from a file located in the same directory as this script.
    
    Args:
        filename: The name of the text file to load.
        
    Returns:
        The content of the file as a string, or an error message if not found.
    """
    
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, filename)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise f"ERROR: Prompt file not found at {file_path}. Please make sure '{filename}' is in the same directory as the node's Python script."
    except Exception as e:
        raise f"ERROR: Could not read prompt file. Reason: {e}"

SYSTEM_PROMPT = load_prompt_from_file("fighting_scene_classifier_prompt.txt")


class FightingSceneDetector_S2V:
    """
    Detects if a given text input describes a fighting scene. 
    Uses Gemini via a relay server to classify the scene.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("condition",)
    FUNCTION = "detect_fighting_scene"
    CATEGORY = "Script To Video Suite/FightDetection"

    def detect_fighting_scene(self, input: str):

        if not input or not input.strip():
            print("⚠️ Empty prompt → no fighting")
            return (False,)

        full_query = f"{SYSTEM_PROMPT}\n\n{input.strip()}"

        print(f"ANALYZING: {input[:50]}...")

        try:
            response = ask_gemini_via_relay(full_query)

            if response.startswith("Error:"):
                print(f"❌ Gemini error: {response}")
                return (False,)

            cleaned = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)

            return (bool(data.get("is_fighting", False)),)

        except Exception as e:
            print(f"⚠️ Detection failed: {e}")
            return (False,)

        


class DragonBallLoRAConditional_S2V:
    """
    Loads a specified LoRA if the condition is True.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "condition": ("BOOLEAN", {"forceInput": True}),
                "lora_name": (folder_paths.get_filename_list("loras"),),
            }
        }

    RETURN_TYPES = ("LORA",)
    RETURN_NAMES = ("lora",)
    FUNCTION = "load_lora_conditional"
    CATEGORY = "Script To Video Suite/FightDetection"

    def load_lora_conditional(self, condition: bool, lora_name: str):

        if not condition:
            print("Condition is False → no LoRA loaded")
            return (None,)

        print(f"✅ Loading LoRA: {lora_name}")
        return (lora_name,)
