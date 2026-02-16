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
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora_stack": ("LORA_STACK",),  # now required
            }
        }
    
    RETURN_TYPES = ("MODEL", "CLIP")
    FUNCTION = "load_loras"
    CATEGORY = "Script To Video Suite"

    def load_loras(self, model, clip, lora_stack):
        result = (model, clip)

        # Apply loras from incoming stack
        for lora_path, strength_model, strength_clip in lora_stack:
            # Resolve full path in case AutoLoraLoader_S2V returned just a filename
            if not os.path.isabs(lora_path) and os.path.sep not in lora_path:
                resolved_path = folder_paths.get_full_path("loras", lora_path)
            else:
                resolved_path = lora_path

            lora_sd = comfy.utils.load_torch_file(resolved_path)
            result = comfy.sd.load_lora_for_models(result[0], result[1], lora_sd, strength_model, strength_clip)

        return result

