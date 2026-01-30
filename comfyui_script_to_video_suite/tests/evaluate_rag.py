import sys
import os
import json
import time
import statistics
from datetime import datetime

# --- SETUP PATHS (To find your RAG modules) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
suite_root = os.path.dirname(current_dir) # Up one level
rag_root = os.path.join(suite_root, "rag_system", "scene-consistency-rag-systems")
src_path = os.path.join(rag_root, "src")

if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import RAG Modules
try:
    from pipeline import RAGPipeline
    from prompt_injection import SceneConsistencyEngine
    print("✅ RAG Modules imported successfully.")
except ImportError as e:
    print(f"❌ Critical Error: Could not import RAG modules. Check paths.\n{e}")
    sys.exit(1)

# --- CONFIGURATION ---
CHARS_DIR = os.path.join(rag_root, "data", "characters")
LOCS_DIR = os.path.join(rag_root, "data", "locations")
OUTPUT_FILE = "rag_evaluation_report.json"

# --- GROUND TRUTH DATASET ---
# This is the "Answer Key". You define the input text and WHO it should find.
TEST_CASES = [
    {
        "text": "Isaac walked into the room looking tired.",
        "expected_char_names": ["Isaac"], # Expected Keywords
        "type": "single_entity"
    },
    {
        "text": "Gertie handed the device to Isaac near the scanner.",
        "expected_char_names": ["Gertie", "Isaac"],
        "type": "multi_entity"
    },
    {
        "text": "The sun set over the horizon, casting long shadows.",
        "expected_char_names": [], # Should find nothing
        "type": "negative_test"
    },
    # Add more specific test cases here later
]

def initialize_engine():
    print("⚙️  Initializing RAG Engine...")
    start_time = time.time()
    
    pipeline = RAGPipeline()
    
    # Load Data
    characters = []
    if os.path.exists(CHARS_DIR):
        from pathlib import Path
        for f in Path(CHARS_DIR).glob("*.json"):
            d = pipeline.load_json_data(str(f))
            if d: characters.extend(d if isinstance(d, list) else [d])
    
    locations = []
    if os.path.exists(LOCS_DIR):
        from pathlib import Path
        for f in Path(LOCS_DIR).glob("*.json"):
            d = pipeline.load_json_data(str(f))
            if d: locations.extend(d if isinstance(d, list) else [d])

    # Build Indices
    pipeline.build_indices(characters=characters, locations=locations, rebuild=False)
    
    engine = SceneConsistencyEngine(
        rag_pipeline=pipeline,
        characters_dir=CHARS_DIR,
        locations_dir=LOCS_DIR
    )
    
    load_time = time.time() - start_time
    print(f"✅ Engine ready in {load_time:.2f} seconds.")
    return engine, load_time

def evaluate():
    engine, init_time = initialize_engine()
    
    results = []
    latencies = []
    total_cases = len(TEST_CASES)
    successful_retrievals = 0
    
    print(f"\n🧪 Starting Evaluation on {total_cases} test cases...\n")

    for i, case in enumerate(TEST_CASES):
        input_text = case["text"]
        expected = [name.lower() for name in case["expected_char_names"]]
        
        # Measure Latency
        t0 = time.time()
        
        # 1. Extraction
        entities = engine.extract_entities(input_text)
        
        # 2. Retrieval
        context = engine.retrieve_context(input_text, entities)
        
        # 3. Enrichment (To get the final resolved names)
        # We look at what the engine actually decided to retrieve
        retrieved_chars = [name.lower() for name in context.character_context.keys()] # IDs usually contain the name
        
        duration = (time.time() - t0) * 1000 # ms
        latencies.append(duration)
        
        # Validation Logic
        # Check if every expected name matches partially with retrieved IDs
        # e.g. Expected "Isaac" matches retrieved "char_isaac_001"
        hits = 0
        misses = []
        
        for exp in expected:
            found = False
            for ret in retrieved_chars:
                if exp in ret: # Simple substring match
                    found = True
                    break
            if found:
                hits += 1
            else:
                misses.append(exp)
        
        # Determine Pass/Fail
        is_success = (len(misses) == 0)
        
        # Special case for negative tests (expecting nothing)
        if not expected and not retrieved_chars:
            is_success = True
        elif not expected and retrieved_chars:
            is_success = False # False Positive (Hallucination)

        if is_success:
            successful_retrievals += 1
            status_icon = "✅"
        else:
            status_icon = "❌"

        print(f"{status_icon} Case {i+1}: '{input_text[:30]}...' | Latency: {duration:.1f}ms")
        if not is_success:
            print(f"   Expected: {expected} | Retrieved: {retrieved_chars}")

        results.append({
            "input": input_text,
            "type": case["type"],
            "expected": expected,
            "retrieved_ids": retrieved_chars,
            "success": is_success,
            "latency_ms": duration
        })

    # --- CALCULATE METRICS ---
    accuracy = (successful_retrievals / total_cases) * 100
    avg_latency = statistics.mean(latencies)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_cases": total_cases,
        "accuracy_percent": accuracy,
        "avg_latency_ms": avg_latency,
        "init_time_sec": init_time,
        "details": results
    }
    
    # Save Report
    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"\n📊 EVALUATION COMPLETE")
    print(f"   Accuracy: {accuracy:.2f}%")
    print(f"   Avg Retrieval Latency: {avg_latency:.2f} ms")
    print(f"   Report saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    evaluate()