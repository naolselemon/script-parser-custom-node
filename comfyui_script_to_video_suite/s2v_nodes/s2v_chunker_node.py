"""
This node, "PDF Chunker (S2V)", is the starting point of the Script-to-Video pipeline.
It takes the path to a PDF file, extracts all its text content, and then splits that
text into smaller, manageable chunks. This is crucial for processing large scripts
that would otherwise exceed the context limits of language models. each chunk will be processed separetly by the llm
"""




import os
import fitz  # PyMuPDF
from docling.document_converter import DocumentConverter

class PDFChunker:
    """
    A custom node that extracts text from a PDF and splits it into overlapping chunks.
    This allows for processing of arbitrarily long scripts.
    """
    
    # Add documentation that will be visible in some ComfyUI frontends
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # A simple mechanism to suggest reloading when the code changes.
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        """
        Defines the input widgets for the node.
        - pdf_path: The absolute path to the PDF script file.
        - chunk_size: The target character length for each chunk.
        - overlap_size: The number of characters from the end of one chunk to include at the beginning of the next, to maintain context.
        """
        return {
            "required": {
                "pdf_path": ("STRING", {"default": "/path/to/your/script.pdf"}),
                "chunk_size": ("INT", {"default": 4000, "min": 500, "max": 16000, "step": 100}),
                "overlap_size": ("INT", {"default": 400, "min": 0, "max": 8000, "step": 50}),
            }
        }

    RETURN_TYPES = ("CHUNKS", "STRING", "INT")
    RETURN_NAMES = ("chunks", "debug_text_output", "chunk_count")
    FUNCTION = "process_pdf"
    CATEGORY = "Script To Video Suite"

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Uses Docling to extract structured Markdown text."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at '{pdf_path}'")
        
        try:
            
            converter = DocumentConverter()
            
            
            result = converter.convert(pdf_path)
            
            
            markdown_output = result.document.export_to_markdown()
            
            return markdown_output
            
        except Exception as e:
            raise IOError(f"Docling failed to process PDF. Reason: {e}")

    def _chunk_text(self, text: str, chunk_size: int, overlap_size: int) -> list[str]:
        """Helper function to split text into smaller, overlapping chunks."""
        if overlap_size >= chunk_size:
            overlap_size = chunk_size - 1
            print(f"Warning: Overlap size was >= chunk size. Adjusting to {overlap_size} to prevent errors.")

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap_size
        return chunks #lists of chunks 

    def process_pdf(self, pdf_path: str, chunk_size: int, overlap_size: int):
        print("Executing 'PDF Chunker' node...")
        
        raw_text = self._extract_text_from_pdf(pdf_path)
        script_chunks = self._chunk_text(raw_text, chunk_size, overlap_size)
        chunk_count = len(script_chunks)
        
        print(f"✅ PDF processed into {chunk_count} chunks.")
        
        # Create the debug string for visual inspection in other nodes
        debug_text = f"Total Chunks: {chunk_count}\n\n"
        debug_text += "\n\n--- CHUNK BREAK ---\n\n".join(script_chunks)
        
        # Return the list of chunks, the debug text, and the count
        return (script_chunks, debug_text, chunk_count)