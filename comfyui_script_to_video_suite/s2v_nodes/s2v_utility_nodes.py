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
            print("🔧 S2V Switch: Using MANUAL input.")
            return (manual_input,)
        
        if generated_input is None:
            print("⚠️ S2V Switch Warning: Workflow mode is ON, but nothing is connected to 'generated_input'. Returning empty string.")
            return ("",)

        print("🔄 S2V Switch: Using GENERATED input.")
        return (generated_input,)

            