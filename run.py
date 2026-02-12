#!/usr/bin/env python
"""
TalkFlow Launch Script
Convenient wrapper for starting the application
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env if exists
env_file = project_root / ".env"
if env_file.exists():
    print(f"Loading environment from {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value

# Import and run
from backend.main import main

if __name__ == "__main__":
    print("=" * 60)
    print("TalkFlow - Real-Time Translation")
    print("=" * 60)
    print()
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("ERROR: Python 3.9 or higher is required")
        sys.exit(1)
    
    # Display configuration
    print("Configuration:")
    print(f"  Host: {os.getenv('TALKFLOW_HOST', '127.0.0.1')}")
    print(f"  Port: {os.getenv('TALKFLOW_PORT', '8000')}")
    print(f"  Source Language: {os.getenv('SOURCE_LANGUAGE', 'en')}")
    print(f"  Target Language: {os.getenv('TARGET_LANGUAGE', 'es')}")
    print(f"  VAD Enabled: {os.getenv('VAD_ENABLED', 'true')}")
    print()
    
    # Check models directory
    models_dir = project_root / "models"
    if not models_dir.exists():
        print("WARNING: Models directory not found")
        print(f"Creating {models_dir}")
        models_dir.mkdir(exist_ok=True)
        (models_dir / "whisper").mkdir(exist_ok=True)
        (models_dir / "argos").mkdir(exist_ok=True)
        (models_dir / "piper").mkdir(exist_ok=True)
        print()
    
    print("Starting TalkFlow...")
    print("Open your browser to: http://127.0.0.1:8000")
    print()
    print("Press Ctrl+C to stop")
    print("-" * 60)
    print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nShutting down TalkFlow...")
        sys.exit(0)
