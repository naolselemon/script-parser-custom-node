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
        print("Executing 'Prompt Unpacker' (JSON Mode)...")
        
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





class SmartSequencer_S2V:
    """
    Node #4b (Improved): Automatically iterates through the prompt lists.
    - No external 'Primitive' node needed.
    - Internal counter tracks progress.
    - Automatically wraps around when it reaches the end.
    """
    
    _current_index = 0

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_prompts": ("PROMPTS_LIST",),
                "video_prompts": ("PROMPTS_LIST",),
                "reset_counter": ("BOOLEAN", {"default": False, "label_on": "Reset on next run", "label_off": "Continue counting"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "INT",)
    RETURN_NAMES = ("image_prompt", "video_prompt", "current_index", "total_panels",)
    FUNCTION = "execute_sequence"
    CATEGORY = "Script To Video Suite/Execution"

    def execute_sequence(self, image_prompts: list, video_prompts: list, reset_counter: bool):
        total_panels = len(image_prompts)
        
        if not image_prompts:
            print("❌ Smart Sequencer: Input list is empty.")
            return ("", "", 0, 0)
        
        if len(image_prompts) != len(video_prompts):
            raise ValueError(f"❌ Mismatch: {len(image_prompts)} images vs {len(video_prompts)} videos.")

        if reset_counter:
            print("🔄 Smart Sequencer: Manual Reset Triggered.")
            SmartSequencer_S2V._current_index = 0

        idx = SmartSequencer_S2V._current_index % total_panels
        
        i_prompt = image_prompts[idx]
        v_prompt = video_prompts[idx]

        print(f"🎬 Smart Sequencer: Processing Panel #{idx + 1} of {total_panels}")

        # 5. Increment for the *next* run
        SmartSequencer_S2V._current_index += 1

        return (i_prompt, v_prompt, idx, total_panels)