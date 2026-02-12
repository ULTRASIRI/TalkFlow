#!/usr/bin/env python3
"""
TalkFlow Model Downloader
Automatically downloads required models for the application
"""
import os
import sys
import urllib.request
import json
from pathlib import Path

MODELS_DIR = Path(__file__).parent / "models"

# Piper TTS voices to download
PIPER_VOICES = {
    "en_US-lessac-medium": {
        "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
    },
    "es_ES-davefx-medium": {
        "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx",
        "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json"
    }
}

def download_file(url, destination):
    """Download a file with progress indicator"""
    print(f"Downloading {destination.name}...")
    
    def reporthook(blocknum, blocksize, totalsize):
        downloaded = blocknum * blocksize
        if totalsize > 0:
            percent = min(downloaded * 100 / totalsize, 100)
            sys.stdout.write(f"\r  Progress: {percent:.1f}%")
            sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, destination, reporthook)
        print("\n  ✓ Complete")
        return True
    except Exception as e:
        print(f"\n  ✗ Failed: {e}")
        return False

def download_piper_voice(voice_name, urls):
    """Download Piper voice files"""
    voice_dir = MODELS_DIR / "piper"
    voice_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nDownloading Piper voice: {voice_name}")
    
    # Download ONNX model
    onnx_path = voice_dir / f"{voice_name}.onnx"
    if onnx_path.exists():
        print(f"  ✓ {onnx_path.name} already exists")
    else:
        if not download_file(urls["onnx"], onnx_path):
            return False
    
    # Download JSON config
    json_path = voice_dir / f"{voice_name}.onnx.json"
    if json_path.exists():
        print(f"  ✓ {json_path.name} already exists")
    else:
        if not download_file(urls["json"], json_path):
            return False
    
    return True

def setup_directories():
    """Create required directories"""
    print("Setting up directories...")
    
    directories = [
        MODELS_DIR / "whisper",
        MODELS_DIR / "argos",
        MODELS_DIR / "piper"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}")

def check_whisper():
    """Check Whisper model (downloads automatically on first use)"""
    print("\nWhisper ASR:")
    print("  ℹ Models will download automatically on first use")
    print("  ℹ Location: ~/.cache/huggingface/hub/")
    print("  ℹ Size: ~500MB for 'small' model")

def check_argos():
    """Check Argos Translate"""
    print("\nArgos Translate:")
    print("  ℹ Language packs download automatically when selected")
    print("  ℹ Location: ~/.local/share/argos-translate/packages/")
    print("  ℹ Size: ~150MB per language pair")

def main():
    print("=" * 60)
    print("TalkFlow Model Downloader")
    print("=" * 60)
    
    # Setup directories
    setup_directories()
    
    # Check Whisper
    check_whisper()
    
    # Check Argos
    check_argos()
    
    # Download Piper voices
    print("\n" + "=" * 60)
    print("Piper TTS Voices")
    print("=" * 60)
    
    print("\nAvailable voices:")
    for i, voice in enumerate(PIPER_VOICES.keys(), 1):
        print(f"  {i}. {voice}")
    
    print("\nWhich voices would you like to download?")
    print("  1. English US (en_US-lessac-medium) - Recommended")
    print("  2. Spanish ES (es_ES-davefx-medium)")
    print("  3. Both")
    print("  4. Skip (download manually later)")
    
    choice = input("\nEnter choice [1-4]: ").strip()
    
    voices_to_download = []
    if choice == "1":
        voices_to_download = ["en_US-lessac-medium"]
    elif choice == "2":
        voices_to_download = ["es_ES-davefx-medium"]
    elif choice == "3":
        voices_to_download = list(PIPER_VOICES.keys())
    elif choice == "4":
        print("\nSkipping Piper voice download.")
        print("You can download voices manually from:")
        print("https://huggingface.co/rhasspy/piper-voices")
    else:
        print("Invalid choice. Skipping downloads.")
        voices_to_download = []
    
    # Download selected voices
    for voice_name in voices_to_download:
        success = download_piper_voice(voice_name, PIPER_VOICES[voice_name])
        if not success:
            print(f"\n✗ Failed to download {voice_name}")
            print("You can download it manually from:")
            print("https://huggingface.co/rhasspy/piper-voices")
    
    # Summary
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    
    print("\nModel Status:")
    print("  ✓ Directories created")
    
    piper_voices = list((MODELS_DIR / "piper").glob("*.onnx"))
    if piper_voices:
        print(f"  ✓ Piper voices: {len(piper_voices)} installed")
        for voice in piper_voices:
            print(f"    - {voice.stem}")
    else:
        print("  ⚠ Piper voices: None installed")
        print("    Run this script again or download manually")
    
    print("\n  ℹ Whisper: Will download on first use")
    print("  ℹ Argos: Will download when languages selected")
    
    print("\nNext steps:")
    print("  1. Ensure dependencies installed: pip install -r requirements.txt")
    print("  2. Start TalkFlow: python run.py")
    print("  3. Open browser: http://localhost:8000")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
