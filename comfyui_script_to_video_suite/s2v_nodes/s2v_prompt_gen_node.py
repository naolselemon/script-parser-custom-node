import re
import os
import json 
from .gemini_relay_client import ask_gemini_via_relay

# 1. Hardcoded fallback to ensure the node never crashes if the text file is missing
INTERNAL_FALLBACK_PROMPT = """You are an expert Prompt Engineer for anime visuals. 
Your task is to process this storyboard and return a SINGLE JSON OBJECT.
Structure: {"meta_summary": "...", "panels": [{"panel_number": 1, "image_prompt": "...", "video_prompt": "..."}]}"""

def load_master_prompt_from_file() -> str:
    """Helper to try and load the prompt file lazily."""
    filename = "prompt_generation_meta_prompt.txt"
    file_path = os.path.join(os.path.dirname(__file__), filename)
    
    if not os.path.exists(file_path):
        return INTERNAL_FALLBACK_PROMPT
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return INTERNAL_FALLBACK_PROMPT

class PromptGenerator:
    """
    A custom node that takes a full storyboard, breaks it into batches,
    calls an LLM to process each batch, and COMBINES the JSON results 
    into a single valid JSON output.
    """
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "storyboard_text": ("STRING", {"multiline": True}),
                "master_prompt": ("STRING", {
                    "default": load_master_prompt_from_file(),
                    "multiline": True
                }),
                "batch_size": ("INT", {"default": 50, "min": 10, "max": 200, "step": 10}),
            },
            "optional": {
                "debug_mode": ("BOOLEAN", {"default": False}),
                "debug_filepath": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("final_prompts",)
    FUNCTION = "generate_prompts_in_batches"
    CATEGORY = "Script To Video Suite"

    def _split_storyboard_into_panels(self, storyboard_text: str) -> list[str]:
        """Splits the full storyboard into a list of individual panel strings."""
        panels = re.split(r'\s*--- PANEL BREAK ---\s*|(?=PANEL\s+\d+)', storyboard_text)
        cleaned_panels = [p.strip() for p in panels if p.strip() and p.startswith("PANEL")]
        print(f"✅ Storyboard split into {len(cleaned_panels)} individual panels.")
        return cleaned_panels

    def generate_prompts_in_batches(self, storyboard_text: str, master_prompt: str, batch_size: int, debug_mode: bool = False, debug_filepath: str = ""):
        
        # --- DEBUG MODE LOGIC ---
        if debug_mode:
            print("💡 DEBUG MODE IS ON. Loading from file.")
            try:
                if not os.path.exists(debug_filepath):
                    raise FileNotFoundError(f"Debug file not found: {debug_filepath}")
                with open(debug_filepath, 'r', encoding='utf-8') as f:
                    storyboard_text = f.read()
            except Exception as e:
                raise ValueError(f"❌ DEBUG ERROR: {e}")
        else:
            print("Executing 'Prompt Generator' node in normal mode...")
        
        if not storyboard_text or not storyboard_text.strip():
            raise ValueError("❌ FATAL ERROR: Input 'storyboard_text' is empty!")

        all_panels = self._split_storyboard_into_panels(storyboard_text)
        if not all_panels:
            print("⚠️ WARNING: No valid panels found. Returning empty.")
            return ("",)

        # --- PREPARE DATA STRUCTURES FOR MERGING ---
        merged_meta_summary = ""
        merged_panels_list = []
        total_batches = (len(all_panels) + batch_size - 1) // batch_size

        for i in range(0, len(all_panels), batch_size):
            batch_num = (i // batch_size) + 1
            print(f"\n--- Processing Batch {batch_num}/{total_batches} ---")
            
            batch_of_panels = all_panels[i:i + batch_size]
            batch_storyboard_text = "\n\n--- PANEL BREAK ---\n\n".join(batch_of_panels)
            
            full_prompt = f"{master_prompt}\n\n--- STORYBOARD TO PROCESS ---\n\n{batch_storyboard_text}"
            response_text = ask_gemini_via_relay(full_prompt)
            
            if response_text.startswith("Error:"):
                raise Exception(f"❌ FATAL ERROR on Batch {batch_num}: {response_text}")

            try:
                cleaned_json_text = response_text.replace("```json", "").replace("```", "").strip()
                batch_data = json.loads(cleaned_json_text)
                
                if batch_num == 1:
                    merged_meta_summary = batch_data.get("meta_summary", "No summary provided.")
                
                batch_panels = batch_data.get("panels", [])
                if isinstance(batch_panels, list):
                    merged_panels_list.extend(batch_panels)
                else:
                    raise ValueError(f"Batch {batch_num} 'panels' is not a list.")

            except json.JSONDecodeError as e:
                raise Exception(f"❌ JSON PARSE ERROR on Batch {batch_num}: {e}")

        final_structure = {
            "meta_summary": merged_meta_summary,
            "panels": merged_panels_list
        }
        return (json.dumps(final_structure, indent=2),)