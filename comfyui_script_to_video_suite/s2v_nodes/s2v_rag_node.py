import sys
import os
import re

current_dir = os.path.dirname(os.path.abspath(__file__))
rag_root_path = os.path.join(
    os.path.dirname(current_dir), 
    "rag_system", 
    "scene-consistency-rag-systems"
)
src_path = os.path.join(rag_root_path, "src")

if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import logic 
RAG_IMPORT_ERROR = None
try:
    from pipeline import RAGPipeline
    from prompt_injection import SceneConsistencyEngine
    RAG_AVAILABLE = True # To handle errors later 
except ImportError as e:
    # save the error to throw it later when the user clicks "Queue".
    RAG_AVAILABLE = False
    RAG_IMPORT_ERROR = str(e)
    print(f"⚠️ RAG Node Warning: Could not import RAG modules. Error: {e}")

# Global Cache
_RAG_ENGINE_CACHE = None

class RagConsistencyNode_S2V:
    """
    Injects character and location details into the storyboard using RAG.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "storyboard_text": ("STRING", {"multiline": True}),
                "enable_rag": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("enriched_storyboard",)
    FUNCTION = "enrich_storyboard"
    CATEGORY = "Script To Video Suite/RAG"

    def _initialize_engine(self):
        global _RAG_ENGINE_CACHE
        if _RAG_ENGINE_CACHE is not None:
            return _RAG_ENGINE_CACHE

        print("📚 S2V RAG: Initializing Pipeline...")
        
        chars_dir = os.path.join(rag_root_path, "data", "characters")
        locs_dir = os.path.join(rag_root_path, "data", "locations")

        pipeline = RAGPipeline()
        
        # Load Data safely
        characters = []
        if os.path.exists(chars_dir):
            from pathlib import Path
            for f in Path(chars_dir).glob("*.json"):
                d = pipeline.load_json_data(str(f))
                if d: characters.extend(d if isinstance(d, list) else [d])
        else:
            print("Warning characters folder doesn't exist")
        
        locations = []
        if os.path.exists(locs_dir):
            from pathlib import Path
            for f in Path(locs_dir).glob("*.json"):
                d = pipeline.load_json_data(str(f))
                if d: locations.extend(d if isinstance(d, list) else [d])
        else:
            print("Warning locations folder doesn't exist")
        

        print(f"📚 S2V RAG: Indexing {len(characters)} chars and {len(locations)} locations...")
        pipeline.build_indices(characters=characters, locations=locations, rebuild=False)

        engine = SceneConsistencyEngine(
            rag_pipeline=pipeline,
            characters_dir=chars_dir,
            locations_dir=locs_dir
        )
        
        _RAG_ENGINE_CACHE = engine
        return engine

    def enrich_storyboard(self, storyboard_text, enable_rag):
        # 1. CRITICAL: Check for Input
        if not storyboard_text or not storyboard_text.strip():
            error_msg = "❌ FATAL ERROR: Input 'storyboard_text' is empty! Check the previous node."
            print(error_msg)
            raise ValueError(error_msg)

        # 2. CRITICAL: Check for RAG Import Errors
        if not RAG_AVAILABLE:
            error_msg = f"❌ FATAL ERROR: RAG Modules failed to load.\nReason: {RAG_IMPORT_ERROR}\n\nTroubleshooting:\n1. Check if 'rag_system' folder exists.\n2. Run 'pip install rich sentence-transformers faiss-cpu'."
            print(error_msg)
            # This turns the node RED and stops execution
            raise ImportError(error_msg)
            
        if not enable_rag:
            print("RAG Node: RAG is disabled via toggle. Passing text through.")
            return (storyboard_text,)

        print("🧠 S2V RAG: Starting enrichment process...")
        
        # 3. Try to initialize engine 
        try:
            engine = self._initialize_engine()
        except Exception as e:
            error_msg = f"FATAL ERROR: Failed to initialize RAG Engine.\nError: {e}"
            print(error_msg)
            raise RuntimeError(error_msg)

        # Split storyboard into panels
        panels = re.split(r'\s*--- PANEL BREAK ---\s*|(?=PANEL\s+\d+)', storyboard_text)
        
        enriched_panels = []
        
        for p in panels:
            p = p.strip()
            if not p: continue
            
            if not p.startswith("PANEL"):
                enriched_panels.append(p)
                continue

            print(f"   -> Enriching: {p[:30]}...")
            
            entities = engine.extract_entities(p)
            context = engine.retrieve_context(p, entities)
            
            dummy_shot = {"description": p, "actions": {}, "camera": {}, "metadata": {}}
            enriched_shot = engine.process_shot(dummy_shot, entities=entities, context=context)

            rag_text_block = ""
            
            if enriched_shot.rag_characters:
                rag_text_block += "\n[CHARACTER CONTEXT]:\n"
                for name, desc in enriched_shot.rag_characters.items():
                    rag_text_block += f"- {name}: {desc}\n"
            
            if enriched_shot.rag_locations:
                rag_text_block += "\n[LOCATION CONTEXT]:\n"
                for name, desc in enriched_shot.rag_locations.items():
                    rag_text_block += f"- {name}: {desc}\n"

            final_panel_text = f"{p}\n{rag_text_block}"
            enriched_panels.append(final_panel_text)

        final_output = "\n\n--- PANEL BREAK ---\n\n".join(enriched_panels)
        
        print("✅ S2V RAG: Enrichment Complete.")
        return (final_output,)