import json
import os
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
        return f"ERROR: Prompt file not found at {file_path}. Please make sure '{filename}' is in the same directory as the node's Python script."
    except Exception as e:
        return f"ERROR: Could not read prompt file. Reason: {e}"

SYSYTEM_PROMPT = load_prompt_from_file("fighting_scene_classifier_prompt.txt")


class FightingSceneDetector_S2V:
    """
    Analyzes video prompts using LLM(Gemini) to detect fighting/action scenes.
    Returns BOOLEAN (is_fighting) and optional debug string.
    """

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")
    

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required" : {
                "video_prompt" : ("STRING", {"multiline" : True}),
            }
        }
    

    RETURN_TYPES = ("BOOLEAN")
    RETURN_NAMES = ("is_fighting")
    FUNCTION = "detect_fighting_scene"
    CATEGORY = "Script To Video Suite/FightDetection"

    def detect_fighting_scene(self, video_prompt: str):
        
        if not video_prompt or not video_prompt.strip():
            msg = "Empty prompt -> no fighting"
            print(f"⚠️ WARNING: {msg}")
            return False
        
        full_query = f" {SYSYTEM_PROMPT}\n\n Scene: {video_prompt.strip()}"

        print(f"ANALYZING: {video_prompt[:50]}...")

        try:
            response = ask_gemini_via_relay(
                full_query,
            )

            if response.startswith("Error:"):
                print(f"❌ ERROR from Gemini Relay: {response}")
                return False
            
            cleaned = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)

            return bool(data.get("is_fighting", False))

        except Exception as e:
            print(f"⚠️ Detection failed: {str(e)}")
            return False