class StringSwitch_S2V:
    """
    A logic gate that allows switching between workflow output and manual entry.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "manual_input": ("STRING", {"multiline": True, "default": ""}),
                "use_manual": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "generated_input": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("selected_string",)
    FUNCTION = "switch_logic"
    CATEGORY = "Script To Video Suite/Logic"

    def switch_logic(self, manual_input, use_manual, generated_input=None):
        if use_manual:
            if not manual_input or not manual_input.strip():
                error_msg = "❌ FATAL ERROR: 'use_manual' is True, but 'manual_input' is empty. Please provide text."
                print(error_msg)
                raise ValueError(error_msg)
            print("🔧 S2V Switch: Using MANUAL input.")
            return (manual_input,)
        
        if generated_input is None:
            raise ValueError("❌ FATAL ERROR: Switch is in Workflow Mode, but nothing is connected to 'generated_input'!")

        return (generated_input,)

            