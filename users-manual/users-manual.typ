// -------------------------
// GLOBAL PAGE SETTINGS & STYLING
// -------------------------

#set document(title: "ComfyUI Script-to-Video Suite Manual", author: "iCog Labs")

// Color Palette
#let brand-primary = rgb("#2e3b4e")
#let brand-accent = rgb("#4a90e2")
#let brand-light = rgb("#f5f7fa")
#let line-color = rgb("#d3dce6")

#set page(
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
  header: context {
    if counter(page).get().first() > 1 {
      align(right)[
        #text(8pt, fill: luma(120), font: "Arial")[ComfyUI Script-to-Video Suite | User Manual]
      ]
    }
  },
  footer: context {
    align(center)[
      #text(10pt, font: "Arial", weight: "bold", fill: brand-primary)[
        --- #counter(page).display() ---
      ]
    ]
  },
  background: context {
    if counter(page).get().first() > 1 {
      // Left and right vertical lines
      place(
        top + left,
        dx: 1cm,
        dy: 0cm,
        rect(width: 1.5pt, height: 100%, fill: brand-accent)
      )
      place(
        top + right,
        dx: -1cm,
        dy: 0cm,
        rect(width: 1.5pt, height: 100%, fill: brand-accent)
      )
    }
  }
)

#set text(
  font: ("Libertinus Serif", "Arial"),
  size: 11pt,
  fill: rgb("#333333"),
  fallback: false
)

#set heading(numbering: "1.1.")
#show heading: it => block(
  above: 1.5em, 
  below: 1em,
  text(fill: brand-primary, weight: "bold")[
    #if it.level == 1 {
      text(size: 18pt)[#it]
    } else if it.level == 2 {
      text(size: 14pt)[#it]
    } else {
      text(size: 12pt)[#it]
    }
  ]
)

#set par(justify: true, leading: 0.75em)
#show link: it => text(fill: brand-accent)[#it]

// -------------------------
// COVER PAGE
// -------------------------

#align(center + horizon)[
  #block(
    fill: brand-light,
    inset: 3em,
    radius: 1em,
    stroke: 2pt + brand-accent
  )[
    #text(size: 28pt, weight: "black", fill: brand-primary)[ComfyUI Script-to-Video Suite]
    
    #v(1em)
    #text(size: 18pt, weight: "light", fill: gray)[Official User Manual]
    
    #v(3em)
    #text(size: 12pt)[
      A structured automation pipeline that converts long-form PDF scripts into cinematic storyboard panels and optimized prompts for AI-based image and video generation.
    ]
  ]
]

#pagebreak()

// -------------------------
// MAIN CONTENT 
// -------------------------

// We use 2 columns for the main content to fit within 2 pages efficiently
#show: rest => columns(2, gutter: 2em)[#rest]

= Core Pipeline Overview

To generate a complete video sequence from a PDF script, the core nodes must be connected in the following specific execution order. Maintaining this sequence ensures correct dependency resolution and prevents downstream processing errors.

#v(1em)

#rect(fill: brand-light, stroke: 1pt + line-color, radius: 4pt, inset: 10pt)[
  #text(weight: "bold", fill: brand-primary)[Order of Execution:]
  1. PDF Chunker (S2V)
  2. Storyboard Generator (S2V)
  3. Prompt Generator (S2V)
  4. Prompt Unpacker (S2V)
  5. Iterative Executor (S2V)
]

#v(1em)

== Pipeline Architecture Flow

The workflow acts as an automated funnel, translating documents into visual data. Below is the input/output relationship between the nodes:

#align(center)[
  #block(fill: rgb("#eef2f5"), inset: 8pt, radius: 4pt, stroke: 1pt + brand-accent)[
    #text(size: 9pt, weight: "bold")[1. PDF Chunker S2V] \
    *In:* `pdf_path`, `chunk_size` \
    *Out:* `chunks`
  ]
  #v(2pt)
  #text(size: 14pt, fill: brand-accent)[↓]
  #v(2pt)
  #block(fill: rgb("#eef2f5"), inset: 8pt, radius: 4pt, stroke: 1pt + brand-accent)[
    #text(size: 9pt, weight: "bold")[2. Storyboard Generator S2V] \
    *In:* `chunks`, `master_prompt` \
    *Out:* `storyboard_text`
  ]
  #v(2pt)
  #text(size: 14pt, fill: brand-accent)[↓]
  #v(2pt)
  #block(fill: rgb("#eef2f5"), inset: 8pt, radius: 4pt, stroke: 1pt + brand-accent)[
    #text(size: 9pt, weight: "bold")[3. Prompt Gen S2V] \
    *In:* `storyboard_text` \
    *Out:* `final_prompts`
  ]
  #v(2pt)
  #text(size: 14pt, fill: brand-accent)[↓]
  #v(2pt)
  #block(fill: rgb("#eef2f5"), inset: 8pt, radius: 4pt, stroke: 1pt + brand-accent)[
    #text(size: 9pt, weight: "bold")[4. Prompt Unpacker S2V] \
    *In:* `prompt_text` \
    *Out:* `image_prompts`, `video_prompts`
  ]
  #v(2pt)
  #text(size: 14pt, fill: brand-accent)[↓]
  #v(2pt)
  #block(fill: rgb("#eef2f5"), inset: 8pt, radius: 4pt, stroke: 1pt + brand-accent)[
    #text(size: 9pt, weight: "bold")[5. Iterative Executor S2V] \
    *In:* List inputs, `mode`, `index` \
    *Out:* Single `image_prompt`, `video_prompt` 
  ]
]

#v(1em)

= Core Nodes Reference

== PDF Chunker (S2V)
*Purpose:* Extracts and segments screenplay text into structured overlapping chunks.
*Inputs:*
- `pdf_path` – Path to source PDF.
- `chunk_size` – Character count per segment.
- `overlap_size` – Shared context between chunks.
*Outputs:*
- `chunks` – Ordered list of text segments.
*Config:* Recommended size is 2000-4000 characters with 10% overlap.

== Storyboard Generator (S2V)
*Purpose:* Transforms text chunks into cinematic storyboard panels using Gemini AI.
*Inputs:*
- `chunks` – Output from the PDF Chunker.
- `master_prompt` – Directs the AI on style.
*Outputs:*
- `storyboard_text` – Detailed scene breakdown including camera directions and dialogue.

== Prompt Generator (S2V)
*Purpose:* Converts storyboard panels into optimized prompts for models like WanVideo.
*Inputs:*
- `storyboard_text`
*Outputs:*
- `final_prompts` – Combined text block containing image prompts and video flow prompts.

== Prompt Unpacker (S2V)
*Purpose:* Parses the aggregated text from the Prompt Generator into clean, iterable Python lists.
*Inputs:*
- `prompt_text`
*Outputs:*
- `image_prompts` (List)
- `video_prompts` (List)
- `meta_summary` (String Context)

== Iterative Executor (S2V)
*Purpose:* Smartly sequences the generation of scenes to avoid GPU VRAM crashes.
*Inputs:*
- `image_prompts` & `video_prompts`
- `mode` (Manual / Auto)
*Outputs:*
- `image_prompt` & `video_prompt` (Single strings outputted one by one).

#colbreak()

= Enhancement Nodes (Optional)

These nodes can be injected into the main pipeline to improve visual consistency or automate post-processing.

== RAG Consistency Engine
*Purpose:* Injects predefined character and location data to ensure cross-scene visual consistency.
*Placement:* Between Storyboard Gen and Prompt Gen.
*Inputs:* `storyboard_text`, `enable_rag`.
*Outputs:* `enriched_storyboard`.

== Gemini Auto LoRA Loader
*Purpose:* Automatically detects character triggers within the active prompt and loads the correct LoRA model weights.
*Placement:* Before the main Model Loader or Sampler.
*Outputs:* `lora_stack` or `loras_list`.

== Fighting Scene Detector
*Purpose:* Identifies combat-intensive scene descriptions and conditionally activates high-motion LoRAs (like Dragon Ball styles).
*Outputs:* Boolean condition and targeted `lora`.

== Video Merger (S2V)
*Purpose:* Combines all rendered `.mp4` scene outputs into a single, cohesive master video file.
*Placement:* Final execution step after scenes are saved.
*Inputs:* `directory_path` (Output folder), `transition_duration`, `max_height`.
*Outputs:* `output_path` (Final MP4 file). 
*Behavior:* Handles crossfade transitions, resolution normalization, and audio leveling safely.

#v(2em)

#block(
  fill: rgb("#fff3cd"),
  stroke: 1pt + rgb("#ffeeba"),
  inset: 1em,
  radius: 0.5em
)[
  *⚠️ Pro-Tip for Stability:* \
  Always enable `force_offload` in your Text Encoders and Video Samplers when using the Iterative Executor. This clears memory between sequential generations and prevents Out-of-Memory (OOM) errors during long films.
]
