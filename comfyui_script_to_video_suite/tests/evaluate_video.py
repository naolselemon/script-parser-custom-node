import cv2
import numpy as np
import json
import os
import argparse
import torch
import matplotlib.pyplot as plt
import seaborn as sns
from skimage.metrics import structural_similarity as ssim
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from PIL import Image

class VideoEvaluator:
    def __init__(self, video_path):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        self.video_path = video_path
        self.video_name = os.path.basename(video_path)
        self.raw_frames = self._load_video_frames(video_path)
        self.gray_frames = [cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in self.raw_frames]
        
        # Load Identity Model (CLIP)
        print("💡 Loading Identity Consistency Model (CLIP)...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.id_model = SentenceTransformer('clip-ViT-B-32', device=device)

    def _load_video_frames(self, path):
        """Loads video into a list of RGB numpy arrays."""
        cap = cv2.VideoCapture(path)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret: break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cap.release()
        return frames

    def calculate_temporal_stability(self):
        """Measures Structural Similarity (SSIM) between frames."""
        print("📈 Calculating Temporal Stability (SSIM)...")
        scores = []
        for i in range(len(self.gray_frames) - 1):
            score = ssim(self.gray_frames[i], self.gray_frames[i+1])
            scores.append(float(score))
        return scores

    def calculate_motion_intensity(self):
        """Measures pixel displacement using Optical Flow."""
        print("📉 Calculating Motion Intensity (Optical Flow)...")
        motion_scores = []
        for i in range(len(self.gray_frames) - 1):
            flow = cv2.calcOpticalFlowFarneback(
                self.gray_frames[i], self.gray_frames[i+1], None, 
                0.5, 3, 15, 3, 5, 1.2, 0
            )
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            motion_scores.append(float(np.mean(mag)))
        return motion_scores

    def calculate_identity_persistence(self):
        """Compares every frame to the first frame using CLIP embeddings."""
        
        ref_image = Image.fromarray(self.raw_frames[0])
        ref_emb = self.id_model.encode(ref_image, convert_to_tensor=True)
        
        persistence_scores = []
        for frame in self.raw_frames:
            curr_image = Image.fromarray(frame)
            curr_emb = self.id_model.encode(curr_image, convert_to_tensor=True)
            score = util.cos_sim(ref_emb, curr_emb)
            persistence_scores.append(float(score.item()))
        return persistence_scores

    def run(self):
        stability = self.calculate_temporal_stability()
        motion = self.calculate_motion_intensity()
        identity = self.calculate_identity_persistence()
        
        metrics = {
            "metadata": {
                "filename": self.video_name,
                "frame_count": len(self.raw_frames),
                "timestamp": datetime.now().isoformat()
            },
            "averages": {
                "avg_stability_ssim": np.mean(stability),
                "avg_motion_intensity": np.mean(motion),
                "avg_identity_persistence": np.mean(identity)
            },
            "timeline": {
                "stability": stability,
                "motion": motion,
                "identity": identity
            }
        }
        return metrics

def save_visualizations(metrics, output_dir):
    sns.set_theme(style="darkgrid")
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
    
    name = metrics["metadata"]["filename"]
    
    sns.lineplot(data=metrics["timeline"]["stability"], ax=ax1, color="blue", linewidth=2)
    ax1.set_title(f"Temporal Stability (SSIM) - {name}")
    ax1.set_ylabel("Similarity (0-1)")
    ax1.set_ylim(0.7, 1.0)
    
    sns.lineplot(data=metrics["timeline"]["motion"], ax=ax2, color="red", linewidth=2)
    ax2.set_title("Motion Intensity (Optical Flow)")
    ax2.set_ylabel("Pixel Displacement")
    
    sns.lineplot(data=metrics["timeline"]["identity"], ax=ax3, color="green", linewidth=2)
    ax3.set_title("Identity Persistence (CLIP Alignment to Frame 0)")
    ax3.set_ylabel("Confidence (0-1)")
    ax3.set_xlabel("Frame Number")
    ax3.set_ylim(0.5, 1.0)

    plt.tight_layout()
    plot_path = os.path.join(output_dir, f"{name}_report.png")
    plt.savefig(plot_path)
    print(f"📊 Visualization saved: {plot_path}")

def main():
   
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    parser = argparse.ArgumentParser(description="Evaluate AI Video Quality Metrics")
    parser.add_argument("video", help="Path to the generated video file")
    parser.add_argument("--output", default="evaluation_results", help="Subfolder name inside tests/")
    args = parser.parse_args()

    # Construct final output path inside the tests directory
    if not os.path.isabs(args.output):
        final_output_dir = os.path.join(script_dir, args.output)
    else:
        final_output_dir = args.output

    if not os.path.exists(final_output_dir):
        os.makedirs(final_output_dir)

    try:
        evaluator = VideoEvaluator(args.video)
        results = evaluator.run()
        
        # Save JSON
        json_filename = f"{results['metadata']['filename']}.json"
        json_path = os.path.join(final_output_dir, json_filename)
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2)
        
        # Generate Graph
        save_visualizations(results, final_output_dir)
        
        print(f"\n✅ Evaluation Finished for {args.video}")
        print(f"   Avg Stability: {results['averages']['avg_stability_ssim']:.4f}")
        print(f"   Avg Identity Persistence: {results['averages']['avg_identity_persistence']:.4f}")
        print(f"   Results saved to: {final_output_dir}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()