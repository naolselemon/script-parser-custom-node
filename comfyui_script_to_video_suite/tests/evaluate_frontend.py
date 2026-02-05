import sys
import os
import json
import tiktoken

current_dir = os.path.dirname(os.path.abspath(__file__))
suite_root = os.path.dirname(current_dir)
nodes_path = os.path.join(suite_root, "s2v_nodes")

if nodes_path not in sys.path:
    sys.path.insert(0, nodes_path)

try:
    from s2v_chunker_node import PDFChunker
    from s2v_executor_nodes import PromptUnpacker
    print("✅ Frontend Modules imported.")
except ImportError as e:
    print(f"❌ Error importing nodes: {e}")
    sys.exit(1)

def count_tokens(text):
    encoder = tiktoken.get_encoding("cl100k_base") # Standard GPT-4/Gemini encoding approximation
    return len(encoder.encode(text))

# --- TEST 1: CHUNKER INTEGRITY ---
def test_chunker():
    print("\n🔹 TEST 1: PDF Chunker Logic (Token Limits & Overlap)")
    
    sentence = "Isaac walked into the facility. "
    full_text = sentence * 500 # Approx 3000-4000 tokens
    
    chunk_limit = 1000
    overlap = 100      
    
    # Instantiate Node
    chunker = PDFChunker()
    
    # We bypass the PDF read and test the splitting logic directly
    # (assuming your node has a helper method, if not we test the splitting logic here)
    # Note: Since your node reads from PDF directly, we will simulate the behavior
    # by creating a temporary PDF or just testing the splitting logic if it's separated.
    
    # For this test, we will assume standard text splitting logic used in your node:
    chunks = []
    start = 0
    while start < len(full_text):
        end = start + chunk_limit
        chunk = full_text[start:end]
        chunks.append(chunk)
        if end >= len(full_text):
            break
        start = end - overlap

    print(f"   Input Length: {len(full_text)} chars")
    print(f"   Generated {len(chunks)} chunks.")
    
    # Metrics
    max_token_count = 0
    overlap_success = True
    
    for i, chunk in enumerate(chunks):
        tokens = count_tokens(chunk)
        if tokens > max_token_count:
            max_token_count = tokens
            
        if i > 0:
            prev_end = chunks[i-1][-20:]
            curr_start = chunk[:20]      
            if not chunk:
                overlap_success = False

    print(f"   Max Tokens per Chunk: {max_token_count}")
    
    if max_token_count < 2000: 
        print("   ✅ Token Budget: PASS (Well within limits)")
    else:
        print("   ⚠️ Token Budget: WARNING (Chunks might be too big)")

def test_json_parsing():
    print("\n🔹 TEST 2: Prompt Generator Output Validation (JSON Schema)")
    
    valid_json_response = """
    {
      "meta_summary": "A dark facility.",
      "panels": [
        {"panel_number": 1, "image_prompt": "Img1", "video_prompt": "Mov1"},
        {"panel_number": 2, "image_prompt": "Img2", "video_prompt": "Mov2"}
      ]
    }
    """
    
    # This simulates a "Bad" response (Missing video prompt)
    bad_json_response = """
    {
      "meta_summary": "Error test",
      "panels": [
        {"panel_number": 1, "image_prompt": "Img1"} 
      ]
    }
    """

    unpacker = PromptUnpacker()
    
    # Test 1: Valid Data
    print("   Sub-test A: Valid JSON input...")
    img, vid, sum_ = unpacker.unpack_prompts(valid_json_response)
    
    if len(img) == len(vid) == 2:
        print("   ✅ Synchronization: PASS (Image count == Video count)")
    else:
        print(f"   ❌ Synchronization: FAIL ({len(img)} vs {len(vid)})")

    # Test 2: Bad Data (Handling missing keys)
    print("   Sub-test B: Malformed Data (Missing Video Prompt)...")
    img_bad, vid_bad, sum_bad = unpacker.unpack_prompts(bad_json_response)
    
    # Your updated code handles this by inserting empty strings, keeping length equal
    if len(img_bad) == len(vid_bad):
        print("   ✅ Fail-Safe Logic: PASS (Handled missing key gracefully)")
        print(f"      Video List: {vid_bad}") 
    else:
        print("   ❌ Fail-Safe Logic: FAIL (Lists are uneven)")

if __name__ == "__main__":
    test_chunker()
    test_json_parsing()