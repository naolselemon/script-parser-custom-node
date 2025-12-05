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

# the class below may not function as it is intended to be, so please use the one above if required. 
class ListSwitch_S2V:
    """
    A specific switch for the Chunker output.
    - Workflow Mode: Passes the list of chunks through unchanged.
    - Manual Mode: Takes your text and wraps it in a list (as if it were 1 chunk)
      so the next node can process it.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "generated_list": ("*",), 
                "manual_text": ("STRING", {"multiline": True, "default": ""}),
                "use_manual": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("selected_list",)
    FUNCTION = "switch_logic"
    CATEGORY = "Script To Video Suite/Logic"

    def switch_logic(self, generated_list, manual_text, use_manual):
        if use_manual:
            print(" List Switch: Using MANUAL input. Converting text to single-item list.")
            return ([manual_text],)
        else:
            print(f"🔄 List Switch: Passing through generated list data.")
            return (generated_list,)
            