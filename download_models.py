"""
╔══════════════════════════════════════════════════════════════════╗
║  Google HAI-DEF — Smallest Per Modality Downloader              ║
║  Downloads only the smallest model from each modality           ║
╚══════════════════════════════════════════════════════════════════╝

SETUP:
  1. pip install huggingface_hub
  2. Get a token at https://huggingface.co/settings/tokens (read access)
  3. Visit EACH gated model page and accept the license agreement
  4. Set your token below or via environment variable HF_TOKEN

USAGE:
  python download_hai_def_models.py                  # Download all (smallest per modality)
  python download_hai_def_models.py --list           # List selected models
  python download_hai_def_models.py --token hf_xxx   # Pass token via CLI
  python download_hai_def_models.py --skip-gguf      # Skip GGUF downloads
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================
# CONFIGURATION — HuggingFace token
# ============================================================
# Reads from environment variable HF_TOKEN by default.
# Override here only if you can't set an env var:
HF_TOKEN = os.environ.get("HF_TOKEN")

# Output directory
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_models")
# ============================================================

try:
    from huggingface_hub import snapshot_download, hf_hub_download
except ImportError:
    print("Error: 'huggingface_hub' is required.")
    print("  pip install huggingface_hub")
    sys.exit(1)


# ============================================================
# SMALLEST MODEL PER MODALITY — Selection Rationale
# ============================================================
#
#  Modality                       All candidates                       → Selected (smallest)
#  ─────────────────────────────  ───────────────────────────────────  ──────────────────────────
#  Image-Text-to-Text             27b-it, 4b-pt, 4b-it, 1.5-4b-it   → medgemma-1.5-4b-it (~8 GB)
#  Text Generation                27b-text-it, txgemma-2b/9b/27b     → txgemma-2b-predict (~5 GB)
#  Zero-Shot Image Classification medsiglip-448                       → medsiglip-448 (~1.7 GB)
#  Image Classification           cxr-foundation, path, derm          → cxr-foundation (~300 MB)
#  Image Feature Extraction       hear-pytorch                        → hear-pytorch (~600 MB)
#  Automatic Speech Recognition   medasr                              → medasr (~1 GB)
#
#  Total estimated: ~17 GB
# ============================================================

MODELS = {
    # ── Image-Text-to-Text → smallest + latest: 1.5-4B ─────
    "medgemma-1.5-4b-it": {
        "repo_id": "google/medgemma-1.5-4b-it",
        "desc": "MedGemma 1.5 4B Instruct — Latest multimodal clinical model",
        "modality": "Image-Text-to-Text",
        "params": "4B",
        "gated": True,
        "size_hint": "~8 GB",
    },

    # ── Text Generation → smallest: 2B ───────────────────────
    "txgemma-2b-predict": {
        "repo_id": "google/txgemma-2b-predict",
        "desc": "TxGemma 2B Predict — Therapeutic property prediction",
        "modality": "Text Generation",
        "params": "2B",
        "gated": True,
        "size_hint": "~5 GB",
    },

    # ── Zero-Shot Image Classification → only one ────────────
    "medsiglip-448": {
        "repo_id": "google/medsiglip-448",
        "desc": "MedSigLIP — Medical image+text embeddings (X-ray, derm, path, CT/MRI)",
        "modality": "Zero-Shot Image Classification",
        "params": "0.9B",
        "gated": True,
        "size_hint": "~1.7 GB",
    },

    # ── Image Classification → smallest of CXR/Path/Derm ─────
    "cxr-foundation": {
        "repo_id": "google/cxr-foundation",
        "desc": "CXR Foundation — Chest X-ray embeddings (language-aligned)",
        "modality": "Image Classification",
        "params": "-",
        "gated": True,
        "size_hint": "~300 MB",
    },

    # ── Image Feature Extraction (Audio) → only one ──────────
    "hear-pytorch": {
        "repo_id": "google/hear-pytorch",
        "desc": "HeAR PyTorch — Health Acoustic Representations",
        "modality": "Image Feature Extraction",
        "params": "-",
        "gated": True,
        "size_hint": "~600 MB",
        "note": "Pre-trained on 300M 2-second audio clips (coughs, breaths).",
    },

    # ── Automatic Speech Recognition → only one ──────────────
    "medasr": {
        "repo_id": "google/medasr",
        "desc": "MedASR — Medical Automatic Speech Recognition",
        "modality": "Automatic Speech Recognition",
        "params": "-",
        "gated": True,
        "size_hint": "~1 GB",
    },
}

# ── Optional: GGUF quantized fallback for CPU/low-VRAM ───────
GGUF_MODELS = {
    "gemma-2-2b-it-gguf": {
        "repo_id": "bartowski/gemma-2-2b-it-GGUF",
        "filename": "gemma-2-2b-it-Q4_K_M.gguf",
        "desc": "Gemma 2B IT (Q4_K_M) — GGUF for llama.cpp CPU inference",
        "modality": "GGUF Quantized",
        "gated": False,
        "size_hint": "~1.5 GB",
    },
}


def get_token(cli_token: Optional[str] = None) -> Optional[str]:
    """Resolve HF token from CLI flag or environment."""
    token = cli_token or HF_TOKEN
    if not token:
        print("⚠  No HuggingFace token detected.")
        print("   All HAI-DEF models are gated and REQUIRE a token + license acceptance.")
        print("   → Set env var:    set HF_TOKEN=hf_yourtoken  (Windows)")
        print("                     export HF_TOKEN=hf_yourtoken  (Linux/Mac)")
        print("   → Get a token:    https://huggingface.co/settings/tokens\n")
        return None
    print(f"  🔑 Token found: ****{token[-4:]}")
    return token


def download_snapshot(key: str, info: dict, token: Optional[str], base_dir: str) -> bool:
    """Download a full model repo via snapshot_download."""
    repo_id = info["repo_id"]
    local_dir = os.path.join(base_dir, key)
    marker = os.path.join(local_dir, ".download_complete")

    print_header(key, info)

    if os.path.exists(marker):
        print(f"  ✓ Already downloaded. Delete {marker} to re-download.")
        return True

    if info.get("gated", True) and not token:
        print(f"  ✗ Skipped — gated model, no token set.")
        print(f"    → Accept license: https://huggingface.co/{repo_id}")
        return False

    try:
        print(f"  ⏳ Downloading to: {local_dir}")
        snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            token=token,
            local_dir_use_symlinks=False,
        )
        Path(marker).write_text(f"Downloaded from {repo_id}\n")
        print(f"  ✓ Success!")
        return True
    except Exception as e:
        return handle_error(e, repo_id)


def download_gguf(key: str, info: dict, token: Optional[str], base_dir: str) -> bool:
    """Download a single GGUF file."""
    repo_id = info["repo_id"]
    filename = info["filename"]
    gguf_dir = os.path.join(base_dir, "gguf")
    os.makedirs(gguf_dir, exist_ok=True)

    print_header(key, info)

    dest_path = os.path.join(gguf_dir, filename)
    if os.path.exists(dest_path):
        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        print(f"  ✓ Already exists ({size_mb:,.0f} MB). Skipping.")
        return True

    try:
        print(f"  ⏳ Downloading {filename}...")
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=gguf_dir,
            local_dir_use_symlinks=False,
            token=token,
        )
        print(f"  ✓ Success!")
        return True
    except Exception as e:
        return handle_error(e, repo_id)


def print_header(key: str, info: dict):
    print(f"\n{'─'*64}")
    print(f"  {info['desc']}")
    print(f"  Repo:     {info['repo_id']}")
    print(f"  Modality: {info['modality']}")
    params = info.get('params', '-')
    size = info.get('size_hint', '?')
    gated = 'Yes' if info.get('gated', True) else 'No'
    print(f"  Params:   {params:<10}  Size: {size:<12}  Gated: {gated}")
    if info.get("note"):
        print(f"  Note:     {info['note']}")
    print(f"{'─'*64}")


def handle_error(e: Exception, repo_id: str) -> bool:
    msg = str(e)
    print(f"  ✗ Failed: {msg[:250]}")
    if "403" in msg or "gated" in msg.lower():
        print(f"    → Accept the license: https://huggingface.co/{repo_id}")
    elif "401" in msg:
        print(f"    → Invalid/expired token: https://huggingface.co/settings/tokens")
    elif "404" in msg:
        print(f"    → Repo not found — may have been renamed or removed.")
    return False


def list_models():
    print("\n  SELECTED MODELS (smallest per modality):")
    print(f"  {'─'*58}")
    for key, info in MODELS.items():
        gated = "🔒" if info.get("gated") else "🔓"
        print(f"    {gated} {info['modality']:<36} → {key}")
        print(f"       {info['desc']}")
        print(f"       {info.get('params', '-')} params, {info.get('size_hint', '?')}")
        print()
    for key, info in GGUF_MODELS.items():
        print(f"    🔓 {info['modality']:<36} → {key}")
        print(f"       {info['desc']}")
        print(f"       {info.get('size_hint', '?')}")
        print()
    print(f"  Total: {len(MODELS)} full models + {len(GGUF_MODELS)} GGUF ≈ 17 GB estimated")


def main():
    parser = argparse.ArgumentParser(description="Download smallest HAI-DEF model per modality")
    parser.add_argument("--list", action="store_true", help="List selected models")
    parser.add_argument("--token", type=str, default=None, help="HuggingFace token")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    parser.add_argument("--skip-gguf", action="store_true", help="Skip GGUF downloads")
    args = parser.parse_args()

    global BASE_DIR
    if args.output_dir:
        BASE_DIR = os.path.abspath(args.output_dir)

    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  HAI-DEF Downloader — Smallest Model Per Modality              ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    print(f"║  Models: {len(MODELS)} full + {len(GGUF_MODELS)} GGUF   Estimated total: ~17 GB         ║")
    print(f"║  Output: {str(BASE_DIR)[:53]:<53} ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    if args.list:
        list_models()
        return

    token = get_token(args.token)
    os.makedirs(BASE_DIR, exist_ok=True)

    results = {}

    # Download full models (smallest per modality)
    for key, info in MODELS.items():
        results[key] = download_snapshot(key, info, token, BASE_DIR)

    # Download GGUF
    if not args.skip_gguf:
        for key, info in GGUF_MODELS.items():
            results[key] = download_gguf(key, info, token, BASE_DIR)

    # ── Summary ──────────────────────────────────────────────
    succeeded = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    print(f"\n\n{'═'*64}")
    print("  SUMMARY")
    print(f"{'═'*64}")
    for key, success in results.items():
        status = "✓" if success else "✗"
        info = MODELS.get(key, GGUF_MODELS.get(key, {}))
        modality = info.get("modality", "")
        print(f"  {status}  {modality:<36} {key}")

    print(f"\n  ✓ Succeeded: {succeeded}  |  ✗ Failed/Skipped: {failed}")
    print(f"  📁 Location: {BASE_DIR}")

    if failed:
        print("\n  For gated models, you must:")
        print("  1. Set HF_TOKEN (script, env var, or --token)")
        print("  2. Accept each model's license:")
        for key, success in results.items():
            if not success:
                repo = MODELS.get(key, GGUF_MODELS.get(key, {})).get("repo_id", "")
                print(f"     → https://huggingface.co/{repo}")

    # Save manifest
    manifest_path = os.path.join(BASE_DIR, "download_manifest.json")
    manifest = {
        "selection": "smallest_per_modality",
        "base_dir": BASE_DIR,
        "models": {
            k: {
                "success": v,
                "repo_id": MODELS.get(k, GGUF_MODELS.get(k, {})).get("repo_id"),
                "modality": MODELS.get(k, GGUF_MODELS.get(k, {})).get("modality"),
            }
            for k, v in results.items()
        },
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n  📄 Manifest: {manifest_path}")

    if not args.skip_gguf:
        print("\n  To run GGUF models: pip install llama-cpp-python")


if __name__ == "__main__":
    main()