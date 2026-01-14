import folder_paths
import comfy.utils
import comfy.sd
import os

class MultiLoraLoader_S2V:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("*",), 
                "clip": ("*",), 
                "lora_stack": ("LORA_STACK",), 
            }
        }

    RETURN_TYPES = ("WANVIDEOMODEL", "WANVIDEOTEXTEMBEDS")
    RETURN_NAMES = ("wan_model", "wan_t5_clip")
    FUNCTION = "load_loras"
    CATEGORY = "Script To Video Suite"

    def load_loras(self, model, clip, lora_stack):
        if not lora_stack:
            return (model, clip)

        print(f"🔥 MultiLora: Processing stack with {len(lora_stack)} items...")

        work_model = model
        is_wrapper = False
        
        if hasattr(model, "model"):
            print("⚙️ MultiLora: Detected Wrapper. Patching internal model...")
            work_model = model.model
            is_wrapper = True
        
        current_model = work_model
        current_clip = clip

        for lora_name, strength_model, strength_clip in lora_stack:
            resolved_path = None
            
            resolved_path = folder_paths.get_full_path("loras", lora_name)
            
            if resolved_path is None and os.path.exists(lora_name):
                resolved_path = lora_name

            if resolved_path is None:
                print(f"❌ Error: LoRA file not found: {lora_name}")
                continue

            print(f"   -> Loading: {lora_name}")
            
            try:
                lora_sd = comfy.utils.load_torch_file(resolved_path)
                
                current_model, current_clip = comfy.sd.load_lora_for_models(
                    current_model, current_clip, lora_sd, strength_model, strength_clip
                )
            except Exception as e:
                print(f"❌ Error merging LoRA {lora_name}: {e}")
                continue

        if is_wrapper:
            # Update wrapper reference
            model.model = current_model
            return (model, current_clip)
        else:
            return (current_model, current_clip)