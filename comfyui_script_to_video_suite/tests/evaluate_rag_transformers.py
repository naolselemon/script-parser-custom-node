import sys
import os
import json
import time
import statistics
import torch
from sentence_transformers import SentenceTransformer, util

# --- SETUP PATHS (Same as before to find RAG) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
suite_root = os.path.dirname(current_dir)
rag_root = os.path.join(suite_root, "rag_system", "scene-consistency-rag-systems")
src_path = os.path.join(rag_root, "src")

if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from pipeline import RAGPipeline
    from prompt_injection import SceneConsistencyEngine
except ImportError:
    print("❌ Error: Could not import RAG modules.")
    sys.exit(1)

# --- CONFIGURATION ---
CHARS_DIR = os.path.join(rag_root, "data", "characters")
LOCS_DIR = os.path.join(rag_root, "data", "locations")
OUTPUT_FILE = "rag_semantic_score_report.json"

# --- TEST DATASET ---
TEST_CASES = [
    "Isaac looked at his cybernetic arm with disdain.",
    "Gertie adjusted her green headband nervously.",
    "The electrical power facility hummed with dark energy.",
    "A random cat walked across the fence.", # Should return nothing (Score 0)
]

class SemanticEvaluator:
    def __init__(self):
        print("⚖️  Loading Judge Model (all-MiniLM-L6-v2)...")
        # This model is fast and standard for semantic similarity
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        print(f"✅ Judge ready on {device}")

    def calculate_relevance(self, query_text, retrieved_context_list):
        """
        Calculates cosine similarity between the Query and the Retrieved Context.
        Returns a score: 0.0 (Irrelevant) to 1.0 (Exact Match).
        """
        if not retrieved_context_list:
            return 0.0

        # Combine all retrieved chunks into one block of text for comparison
        full_context = " ".join(retrieved_context_list)

        # Vectorize
        query_emb = self.model.encode(query_text, convert_to_tensor=True)
        context_emb = self.model.encode(full_context, convert_to_tensor=True)

        # Calculate Similarity
        score = util.cos_sim(query_emb, context_emb)
        return score.item()

def run_semantic_evaluation():
    # 1. Init RAG Engine
    print("⚙️  Initializing RAG Engine...")
    pipeline = RAGPipeline()
    
    # Load and Index Data
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

    pipeline.build_indices(characters=characters, locations=locations, rebuild=False)
    
    engine = SceneConsistencyEngine(
        rag_pipeline=pipeline,
        characters_dir=CHARS_DIR,
        locations_dir=LOCS_DIR
    )

    # 2. Init Judge
    judge = SemanticEvaluator()
    
    results = []
    scores = []

    print(f"\n📊 Starting Semantic Analysis on {len(TEST_CASES)} cases...\n")

    for query in TEST_CASES:
        # Run RAG
        entities = engine.extract_entities(query)
        context = engine.retrieve_context(query, entities)
        
        # Collect all retrieved text (Characters + Locations)
        retrieved_texts = []
        
        for chunks in context.character_context.values():
            retrieved_texts.extend(chunks)
        for chunks in context.location_context.values():
            retrieved_texts.extend(chunks)

        # Calculate Score
        similarity = judge.calculate_relevance(query, retrieved_texts)
        
        # Logic: If query has no entities, 0 is actually "Success" (No Hallucination).
        # If query HAS entities, we want High Score.
        has_entities = len(entities.characters) > 0 or len(entities.locations) > 0
        
        status = "⚪"
        if has_entities and similarity > 0.25: status = "✅ Good Match"
        elif has_entities and similarity <= 0.25: status = "⚠️ Low Relevance"
        elif not has_entities and similarity == 0: status = "✅ Clean Skip"

        print(f"Query: '{query[:40]}...'")
        print(f"   -> Entities Found: {len(entities.characters) + len(entities.locations)}")
        print(f"   -> Semantic Score: {similarity:.4f} {status}")
        print("-" * 50)

        results.append({
            "query": query,
            "entities_found": len(entities.characters) + len(entities.locations),
            "similarity_score": similarity,
            "retrieved_count": len(retrieved_texts)
        })
        
        # Only track score for positive cases for the average
        if has_entities:
            scores.append(similarity)

    # Summary
    avg_score = statistics.mean(scores) if scores else 0
    print(f"\n📈 Average Relevance Score (Positive Cases): {avg_score:.4f}")
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Report saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_semantic_evaluation()