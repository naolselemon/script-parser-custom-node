"""
This node, "Storyboard Generator (S2V)", is the second core of the pipeline.
It takes the text chunks from the PDF Chunker and a master prompt, then iterates
through each chunk, calling a language model (via a relay) to generate a structured
storyboard. It then combines and de-duplicates the results.
"""
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

STORYBOARD_PROMPT_TEMPLATE = load_prompt_from_file("storyboard_master_prompt.txt")


class StoryboardGenerator:
    """
    A custom node that iterates through script chunks, calls an LLM to generate
    storyboard panels for each, and then combines and de-duplicates the results.
    """
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        """
        Defines the input widgets for the node.
        - chunks: The list of text chunks from the PDFChunker.
        - master_prompt: A multi-line text field pre-filled with the master prompt.
        """
        return {
            "required": {
                "chunks": ("CHUNKS",),
                "master_prompt": ("STRING", {
                    "default": STORYBOARD_PROMPT_TEMPLATE,
                    "multiline": True
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("storyboard_text",)
    FUNCTION = "generate_storyboard"
    CATEGORY = "Script To Video Suite"

    def _post_process_storyboard(self, raw_text: str) -> str:
        """Helper function to clean up and de-duplicate storyboard panels."""
        panel_delimiter = "--- PANEL BREAK ---"
        all_panels_raw = raw_text.split(panel_delimiter)
        
        final_panels = []
        seen_panels = set() # Use the whole panel for a more robust de-duplication

        for panel_block in all_panels_raw:
            panel_block = panel_block.strip()
            if not panel_block: 
                print("missed a panel")
                continue

            if panel_block not in seen_panels:
                final_panels.append(panel_block)
                seen_panels.add(panel_block)
                # TODO : deduplication only happens when there is 100% similarity which is inefficient, find another method. 
                
        print(f"De-duplication complete. Kept {len(final_panels)} unique panels from {len(all_panels_raw)} total.")
        return f"\n\n{panel_delimiter}\n\n".join(final_panels)

    def generate_storyboard(self, chunks: list[str], master_prompt: str):
        print("Executing 'Storyboard Generator' node...")
        all_responses = []
        chunk_count = len(chunks)

        for i, chunk_content in enumerate(chunks):
            print(f"Processing chunk {i+1}/{chunk_count} via relay...")
            
            full_prompt = f"{master_prompt}\n\n{chunk_content}"
            
            response_text = ask_gemini_via_relay(full_prompt)
            
            if response_text.startswith("Error:"):
                # 1. Create a clear, comprehensive error message.
                error_message = f"❌ FATAL ERROR on chunk {i+1}/{chunk_count}: The relay server failed. The process will be stopped.\n\n--> Reason: {response_text}"
                
                # 2. Print the error to the console for debugging.
                print(error_message)
                
                # 3. Raise an Exception. 
                raise Exception(error_message)
            
            # This line is only reached if the request was successful.
            all_responses.append(response_text)
        
        raw_storyboard_output = "\n".join(all_responses)
        final_storyboard = self._post_process_storyboard(raw_storyboard_output)
        
        print("✅ Storyboard generation complete.")
        return (final_storyboard,)