

from .comfyui_script_to_video_suite.s2v_nodes.s2v_chunker_node import PDFChunker
from .comfyui_script_to_video_suite.s2v_nodes.s2v_storyboard_node import StoryboardGenerator
from .comfyui_script_to_video_suite.s2v_nodes.s2v_prompt_gen_node import PromptGenerator
from .comfyui_script_to_video_suite.s2v_nodes.s2v_executor_nodes import PromptUnpacker, IterativeExecutor

NODE_CLASS_MAPPINGS = {
    "PDFChunker_S2V": PDFChunker,
    "StoryboardGenerator_S2V": StoryboardGenerator,
    "PromptGenerator_S2V": PromptGenerator,
    "PromptUnpacker_S2V": PromptUnpacker,
    "IterativeExecutor_S2V": IterativeExecutor,
    "AutoLoraLoader_S2V": AutoLoraLoader_S2V,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDFChunker_S2V": "1. PDF Chunker (S2V)",
    "StoryboardGenerator_S2V": "2. Storyboard Generator (S2V)",
    "PromptGenerator_S2V": "3. Prompt Generator (S2V)",
    "PromptUnpacker_S2V": "4. Prompt Unpacker (S2V)",
    "IterativeExecutor_S2V": "5. Iterative Executor (S2V)",
    "AutoLoraLoader_S2V": "6. Gemini Auto LoRA Loader (S2V)",
}

# --- A confirmation message that your package was loaded ---
print('✅ Loaded Custom Nodes: Script-to-Video Suite')