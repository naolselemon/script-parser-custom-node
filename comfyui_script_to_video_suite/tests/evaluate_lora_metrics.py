import sys
import os
import time
import json
import torch
import statistics
from safetensors.torch import load_file

# --- 1. SETUP COMFYUI BACKEND CONNECTION ---
# We need to add the ComfyUI root directory to sys.path so we can import 'folder_paths'
current_dir = os.path.dirname(os.path.abspath(__file__))
# Assuming structure: ComfyUI/custom_nodes/script-parser.../tests/
comfy_root = os.path.abspath(os.path.join(current_dir, "../../../.."))

if comfy_root not in sys.path:
    sys.path.insert(0, comfy_root)

try:
    import folder_paths
    import comfy.utils
    print(f"✅ Connected to ComfyUI Backend at: {comfy_root}")
except ImportError:
    print(f"❌ Error: Could not find ComfyUI backend at {comfy_root}")
    sys.exit(1)

# --- CONFIGURATION ---
# The specific LoRA you want to benchmark
TARGET_LORA_NAME = "isaac_15.safetensors" 
OUTPUT_FILE = "lora_performance_report.json"

def analyze_weights(state_dict):
    """
    Performs mathematical analysis on the LoRA weights to determine signal strength.
    """
    total_params = 0
    all_means = []
    
    for key, tensor in state_dict.items():
        # Convert to float for calculation
        t = tensor.float()
        total_params += t.numel()
        all_means.append(t.abs().mean().item())

    # Signal Strength: The average magnitude of the weights.
    # If this is 0, the LoRA does nothing. If it's too high (>1), it might burn the image.
    avg_signal = statistics.mean(all_means) if all_means else 0
    return total_params, avg_signal

def evaluate_loader():
    print(f"\n📊 Starting Performance Profile for: {TARGET_LORA_NAME}\n")
    
    metrics = {
        "lora_name": TARGET_LORA_NAME,
        "path_resolution_ms": 0,
        "load_time_ms": 0,
        "file_size_mb": 0,
        "parameter_count": 0,
        "signal_strength": 0,
        "tensor_device": "cpu", # Loading to CPU for safety during test
        "status": "FAIL"
    }

    # --- TEST 1: PATH RESOLUTION (ComfyUI API) ---
    t0 = time.time()
    # This uses the REAL ComfyUI logic to hunt through folders
    lora_path = folder_paths.get_full_path("loras", TARGET_LORA_NAME)
    t1 = time.time()
    
    metrics["path_resolution_ms"] = (t1 - t0) * 1000
    
    if lora_path is None:
        print(f"❌ Error: ComfyUI could not find '{TARGET_LORA_NAME}'. Check filename.")
        return metrics

    print(f"✅ Path Resolved: {lora_path}")
    print(f"   ⏱️ Time: {metrics['path_resolution_ms']:.4f} ms")

    # Get File Size
    size_mb = os.path.getsize(lora_path) / (1024 * 1024)
    metrics["file_size_mb"] = round(size_mb, 2)

    # --- TEST 2: I/O & PARSING SPEED ---
    print(f"\n⚙️  Benchmarking Load Speed ({metrics['file_size_mb']} MB)...")
    
    try:
        t0 = time.time()
        # This simulates exactly what comfy.utils.load_torch_file does
        if lora_path.endswith(".safetensors"):
            lora_sd = load_file(lora_path, device="cpu")
        else:
            lora_sd = torch.load(lora_path, map_location="cpu")
        t1 = time.time()
        
        load_time = (t1 - t0) * 1000
        metrics["load_time_ms"] = load_time
        print(f"✅ Loaded into Memory")
        print(f"   ⏱️ Time: {load_time:.2f} ms")
        
        # Calculate Throughput
        throughput = metrics["file_size_mb"] / (load_time / 1000)
        print(f"   🚀 Throughput: {throughput:.2f} MB/s")

    except Exception as e:
        print(f"❌ Load Failed: {e}")
        return metrics

    # --- TEST 3: WEIGHT INTEGRITY CHECK ---
    print(f"\n🧮 Analyzing Tensor Integrity...")
    try:
        params, signal = analyze_weights(lora_sd)
        metrics["parameter_count"] = params
        metrics["signal_strength"] = signal
        metrics["status"] = "SUCCESS"
        
        print(f"   Total Parameters: {params:,}")
        print(f"   Signal Strength (Mean Abs): {signal:.6f}")
        
        if signal == 0:
            print("   ⚠️ WARNING: LoRA weights are all zero! This file is empty/broken.")
        elif signal > 0.1:
            print("   ⚠️ WARNING: Signal is unusually high. Might cause artifacts.")
        else:
            print("   ✅ Weight range looks healthy.")

    except Exception as e:
        print(f"❌ Analysis Failed: {e}")

    # --- SAVE REPORT ---
    with open(OUTPUT_FILE, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n📄 Report saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    evaluate_loader()