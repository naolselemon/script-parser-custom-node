import folder_paths
import os

class MultiLoraLoader_S2V:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "lora_stack": ("LORA_STACK",), 
            }
        }

    RETURN_TYPES = ("WANVIDLORA",)
    RETURN_NAMES = ("loras_list",)
    FUNCTION = "prepare_loras"
    CATEGORY = "Script To Video Suite"

    def prepare_loras(self, lora_stack):
        if not lora_stack:
            print("⚠️ Empty lora_stack: No LoRA configurations provided.")
            return (None,)

        print(f"🔥 MultiLora: Processing stack with {len(lora_stack)} items...")

        loras_list = []

        for lora_name, strength_model, strength_clip in lora_stack:
            #  LoRA file path
            resolved_path = folder_paths.get_full_path("loras", lora_name)
            
            # Fallback: check if lora_name is already an absolute path
            if resolved_path is None and os.path.exists(lora_name):
                resolved_path = lora_name

            if resolved_path is None:
                print(f"❌ LoRA file not found: {lora_name}")
                continue

            # Build configuration dictionary 
            lora_config = {
                "path": resolved_path,
                "strength": strength_model,  
                "name": os.path.splitext(os.path.basename(lora_name))[0],
                "merge_loras": True,
                "low_mem_load": False,
                "blocks": {},
                "layer_filter": ""
            }
            
            loras_list.append(lora_config)
            print(f"   ✅ Added: {lora_name} (Strength: {strength_model})")

        if not loras_list:
            print("⚠️ No valid LoRAs found in stack.")
            return (None,)

        print(f"✅ Prepared {len(loras_list)} LoRA configuration(s)")
        return (loras_list,)