# s2v_executor_nodes.py
import re

# Helper function to parse prompts from a section
def _parse_prompts_from_section(section_text: str) -> list[str]:
    matches = re.findall(r"PANEL\s+\d+:\s*(.*)", section_text, re.IGNORECASE)
    return [match.strip() for match in matches]

class PromptUnpacker:
    """
    Node #4a: Parses the full text from the PromptGenerator into clean, 
    usable lists of prompts, ready for iteration.
    """
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return { "required": { "prompt_text": ("STRING", {"multiline": True}), } }

    RETURN_TYPES = ("PROMPTS_LIST", "PROMPTS_LIST", "STRING",)
    RETURN_NAMES = ("image_prompts", "video_prompts", "meta_summary",)
    FUNCTION = "unpack_prompts"
    CATEGORY = "Script To Video Suite/Execution"

    def unpack_prompts(self, prompt_text: str):
        print("Executing 'Prompt Unpacker' node...")
        if not prompt_text or not prompt_text.strip():
            print("⚠️ WARNING: Input prompt_text is empty.")
            return ([], [], "")

        sections = re.split(r'###\s*(META SCENE SUMMARY|IMAGE GENERATION PROMPTS|VIDEO GENERATION \(I2V\) PROMPTS)\s*', prompt_text, flags=re.IGNORECASE)
        
        meta_summary, image_prompts, video_prompts = "", [], []

        for i in range(1, len(sections), 2):
            header = sections[i].strip().upper()
            content = sections[i+1].strip()
            
            if "META SCENE SUMMARY" in header:
                meta_summary = content
            elif "IMAGE GENERATION PROMPTS" in header:
                image_prompts = _parse_prompts_from_section(content)
            elif "VIDEO GENERATION (I2V) PROMPTS" in header:
                video_prompts = _parse_prompts_from_section(content)
        
        print(f"✅ Unpacked {len(image_prompts)} image prompts and {len(video_prompts)} video prompts.")
        # We are returning native Python lists here.
        return (image_prompts, video_prompts, meta_summary)

class IterativeExecutor:
    """
    Node #4b: The 'for loop'. Takes lists of prompts and serves them one by one,
    either manually by index or iteratively in a loop.
    """
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_prompts": ("PROMPTS_LIST",),
                "video_prompts": ("PROMPTS_LIST",),
                "mode": (["manual", "iterative"],),
                "index": ("INT", {"default": 0, "min": 0, "step": 1}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "INT",)
    RETURN_NAMES = ("image_prompt", "video_prompt", "current_index", "total_panels",)
    FUNCTION = "execute"
    CATEGORY = "Script To Video Suite/Execution"

    def execute(self, image_prompts: list, video_prompts: list, mode: str, index: int):
        print(f"Executing 'Iterative Executor' in '{mode}' mode...")
        total_panels = len(image_prompts)
        
        if total_panels == 0:
            return ("", "", 0, 0)
        
        current_index = 0
        if mode == 'manual':
            # In manual mode, we respect the user's index, but prevent crashes.
            current_index = index % total_panels
        else: # iterative mode
            # In iterative mode, the 'index' input acts as the loop counter.
            current_index = index % total_panels
        
        current_image_prompt = image_prompts[current_index]
        current_video_prompt = video_prompts[current_index] if current_index < len(video_prompts) else ""

        print(f"--> Serving prompts for Panel #{current_index + 1}/{total_panels}")
        return (current_image_prompt, current_video_prompt, current_index, total_panels)