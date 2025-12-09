import json

class PromptUnpacker:
    """
    Node #4a: Parses the JSON output from PromptGenerator into clean, 
    usable lists of prompts, ready for iteration.
    """
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return { 
            "required": { 
                "prompt_text": ("STRING", {"multiline": True, "forceInput": True}), 
            } 
        }

    RETURN_TYPES = ("PROMPTS_LIST", "PROMPTS_LIST", "STRING",)
    RETURN_NAMES = ("image_prompts", "video_prompts", "meta_summary",)
    FUNCTION = "unpack_prompts"
    CATEGORY = "Script To Video Suite/Execution"

    def unpack_prompts(self, prompt_text: str):
        print("Executing 'Prompt Unpacker' JSON Mode...")
        
        if not prompt_text or not prompt_text.strip():
            error_message = "❌ FATAL ERROR: Input 'prompt_text' is empty! The Prompt Generator node returned nothing."
            print(error_message)
            raise ValueError(error_message)

        cleaned_text = prompt_text.replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(cleaned_text)
            
            meta_summary = data.get("meta_summary", "No summary provided.")
            
            panels = data.get("panels", [])
            
            if not isinstance(panels, list):
                print(f"❌ ERROR: 'panels' key is not a list. Got: {type(panels)}")
                return ([], [], meta_summary)

            image_prompts = []
            video_prompts = []

            for i, p in enumerate(panels):
                i_p = p.get("image_prompt", "")
                v_p = p.get("video_prompt", "")
                
                if i_p is None: i_p = ""
                if v_p is None: v_p = ""
                
                image_prompts.append(i_p)
                video_prompts.append(v_p)

            print(f"✅ Unpacked {len(image_prompts)} image prompts and {len(video_prompts)} video prompts.")
            
            return (image_prompts, video_prompts, meta_summary)

        except json.JSONDecodeError as e:
            error_msg = f"❌ FATAL ERROR: The LLM output was not valid JSON.\nParse Error: {e}\n\nSnippet: {cleaned_text[:200]}..."
            print(error_msg)
            raise ValueError(error_msg)

        except Exception as e:
            error_msg = f"❌ UNEXPECTED ERROR during unpacking: {e}"
            print(error_msg)
            raise ValueError(error_msg)


class IterativeExecutor:
    """
    Node #4b: The 'for loop'. Takes lists of prompts and serves them one by one,
    based on the index provided.
    """
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always re-run to ensure we catch index changes
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
        
        #  Validate Image prompts
        if not image_prompts or not isinstance(image_prompts, list):
            error_message = "FATAL ERROR: Executor received an empty or invalid 'image_prompts' list. Check the Unpacker node output."
            print(error_message)
            raise ValueError(error_message)
        
        # Validate Video prompts
        if not video_prompts or not isinstance(video_prompts, list):
            error_msg = "FATAL ERROR: No 'video_prompts' found! The Unpacker returned an empty list."
            print(error_msg)
            raise ValueError(error_msg)
        
        #  Synchronization Check (Crucial)
        if len(image_prompts) != len(video_prompts):
            error_msg = f"FATAL ERROR: Mismatch in prompt counts!\nImage Prompts: {len(image_prompts)}\nVideo Prompts: {len(video_prompts)}\n(The LLM likely failed to generate a video prompt for every panel.)"
            print(error_msg)
            raise ValueError(error_msg)

        total_panels = len(image_prompts)
        current_index = index % total_panels
        
        #  Retrieve Prompts
        current_image_prompt = image_prompts[current_index]
        current_video_prompt = video_prompts[current_index]

        # Safety check: Ensure video prompt list is aligned
        if not current_video_prompt:
            print(f"⚠️ WARNING: Panel #{current_index+1} has an empty video prompt.")

        print(f"--> Serving prompts for Panel #{current_index + 1}/{total_panels}")
        
        return (current_image_prompt, current_video_prompt, current_index, total_panels)