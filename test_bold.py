
import sys
from unittest.mock import MagicMock

# Mock fitz module
mock_fitz = MagicMock()
sys.modules['fitz'] = mock_fitz

# Now we can import the node module
# We need to make sure the directory is in path
import os
sys.path.append('/home/naolselemon/Documents/03 iCog Labs/01 Long-form-AI-video-generation/script-parser-custom-node/comfyui_script_to_video_suite/s2v_nodes')

# Using importlib to load module from path if plain import fails due to package structure
import importlib.util
spec = importlib.util.spec_from_file_location("s2v_chunker_node", "/home/naolselemon/Documents/03 iCog Labs/01 Long-form-AI-video-generation/script-parser-custom-node/comfyui_script_to_video_suite/s2v_nodes/s2v_chunker_node.py")
s2v_chunker = importlib.util.module_from_spec(spec)
sys.modules["s2v_chunker_node"] = s2v_chunker
spec.loader.exec_module(s2v_chunker)

from s2v_chunker_node import PDFChunker

def test_extract_text_with_bold():
    # Setup mock document structure
    # page.get_text("dict") returns format:
    # {'blocks': [{'lines': [{'spans': [{'text': 'foo', 'flags': 0}, {'text': 'bar', 'flags': 16}]}]}]}
    
    mock_page = MagicMock()
    mock_dict = {
        'blocks': [
            {
                'lines': [
                    {
                        'spans': [
                            {'text': 'Normal text ', 'flags': 0},
                            {'text': 'Bold text', 'flags': 16}, # 16 is bold
                            {'text': ' Normal again.', 'flags': 0}
                        ]
                    }
                ]
            },
            {
                'lines': [
                    {
                        'spans': [
                            {'text': 'Second paragraph.', 'flags': 0}
                        ]
                    }
                ]
            }
        ]
    }
    mock_page.get_text.return_value = mock_dict
    
    # Mock doc context manager
    mock_doc = MagicMock()
    mock_doc.__iter__.return_value = [mock_page]
    mock_doc.__enter__.return_value = mock_doc
    mock_doc.__exit__.return_value = None
    
    mock_fitz.open.return_value = mock_doc
    
    # Instantiate and run
    chunker = PDFChunker()
    # We mock os.path.exists to pass the check
    with MagicMock() as mock_exists:
        with MagicMock() as mock_open:
            # We are mocking inside the class method usage of fitz.open, which we already mocked via sys.modules
            # But we also need to pass the file exists check
            original_exists = os.path.exists
            os.path.exists = lambda x: True
            
            try:
                result = chunker._extract_text_from_pdf("dummy.pdf")
            finally:
                os.path.exists = original_exists
    
    print("Extracted Text:")
    print(result)
    
    expected_segment = "Normal text **Bold text** Normal again."
    if expected_segment in result:
        print("✅ SUCCESS: Bold text was correctly wrapped.")
    else:
        print("❌ FAILURE: Bold text was NOT correctly wrapped.")

    if "**" in result:
         print("✅ SUCCESS: Markdown detected.")
    else:
         print("❌ FAILURE: No markdown detected.")

if __name__ == "__main__":
    test_extract_text_with_bold()
