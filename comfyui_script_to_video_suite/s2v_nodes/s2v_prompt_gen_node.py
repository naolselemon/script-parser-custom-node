import re
import os
import json 
from .gemini_relay_client import ask_gemini_via_relay

def load_master_prompt_from_file(filename: str) -> str:
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, filename)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"ERROR: Prompt file not found at {file_path}. Please make sure '{filename}' is in the same directory as the node's Python script."
    except Exception as e:
        return f"ERROR: Could not read prompt file. Reason: {e}"

PROMPT_GENERATION_META_PROMPT = load_master_prompt_from_file("prompt_generation_meta_prompt.txt")

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
                    "default": PROMPT_GENERATION_META_PROMPT,
                    "multiline": True
                }),
                "batch_size": ("INT", {"default": 50, "min": 10, "max": 200, "step": 10}),
            },
           
            "optional": {
                "debug_mode": ("BOOLEAN", {"default": False}),
                "debug_filepath": ("STRING", {"default": "C:\\path\\to\\your\\debug_storyboard.txt"}),
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
            print("💡 DEBUG MODE IS ON. Ignoring 'storyboard_text' input and loading from file.")
            try:
                if not os.path.exists(debug_filepath):
                    raise FileNotFoundError(f"Debug file not found at path: {debug_filepath}")
                
                with open(debug_filepath, 'r', encoding='utf-8') as f:
                    storyboard_text = f.read()
                print(f"✅ Successfully loaded debug data from: {debug_filepath}")
            except Exception as e:
                error_message = f"❌ DEBUG ERROR: Failed to load file. Reason: {e}"
                print(error_message)
                raise e 
        else:
            print("Executing 'Prompt Generator' node in normal mode...")
        
        if not storyboard_text or not storyboard_text.strip():
            error_message = " FATAL ERROR: Input 'storyboard_text' is empty!"
            print(error_message) 
            raise ValueError(error_message)

        all_panels = self._split_storyboard_into_panels(storyboard_text)
        if not all_panels:
            print("⚠️ WARNING: No valid panels found in storyboard text. Aborting.")
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

            print(f"Sending batch of {len(batch_of_panels)} panels ({len(batch_storyboard_text)} chars) to relay...")
            
            full_prompt = f"{master_prompt}\n\n--- STORYBOARD TO PROCESS ---\n\n{batch_storyboard_text}"
            
            response_text = ask_gemini_via_relay(full_prompt)
            
            # Basic error check
            if response_text.startswith("Error:"):
                error_message = f"❌ FATAL ERROR on Batch {batch_num}: The relay failed.\n--> Reason: {response_text}"
                print(error_message)
                print("This is a debug message")
                raise Exception(error_message)

            # --- JSON PARSING & MERGING LOGIC ---
            try:
                # 1. Clean markdown code blocks if Gemini added them
                cleaned_json_text = response_text.replace("```json", "").replace("```", "").strip()
                
                # 2. Parse the batch JSON
                batch_data = json.loads(cleaned_json_text)
                
                # 3. Extract Summary (Only need it from the first batch)
                if batch_num == 1:
                    merged_meta_summary = batch_data.get("meta_summary", "No summary provided.")
                
                # 4. Extract Panels and append to master list
                batch_panels = batch_data.get("panels", [])
                if isinstance(batch_panels, list):
                    merged_panels_list.extend(batch_panels)
                    print(f"✅ Batch {batch_num}: Successfully extracted {len(batch_panels)} panels.")
                else:
                    error_message = f"❌ FATAL ERROR on Batch {batch_num}: 'panels' key is not a list. Halting processing.\n--> Raw value: {repr(batch_panels)}"
                    print(error_message)
                    raise Exception(error_message)

            except json.JSONDecodeError as e:
                print(f"❌ JSON PARSE ERROR on Batch {batch_num}: {e}")
                print(f"Raw response was: {response_text[:100]}...")
                # We raise exception here because if one batch fails, the array alignment breaks
                raise Exception(f"Batch {batch_num} returned invalid JSON. Check console for details.")

        # --- FINAL ASSEMBLY ---
        final_structure = {
            "meta_summary": merged_meta_summary,
            "panels": merged_panels_list
        }
        final_output_string = json.dumps(final_structure, indent=2)
        print(f"✅ All batches complete. Total panels merged: {len(merged_panels_list)}")
        return (final_output_string,)