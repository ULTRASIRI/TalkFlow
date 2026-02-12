#!/usr/bin/env python
"""
TalkFlow System Verification Script
Checks system requirements and dependencies
"""
import sys
import os
from pathlib import Path
import subprocess

def print_header(text):
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print('=' * 60)

def print_check(name, status, details=""):
    symbol = "✓" if status else "✗"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{symbol}{reset} {name}")
    if details:
        print(f"  → {details}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    required = (3, 9)
    status = version >= required
    details = f"Python {version.major}.{version.minor}.{version.micro}"
    if not status:
        details += f" (requires {required[0]}.{required[1]}+)"
    return status, details

def check_pip():
    """Check if pip is available"""
    try:
        import pip
        details = f"pip {pip.__version__}"
        return True, details
    except ImportError:
        return False, "pip not found"

def check_venv():
    """Check if running in virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    details = "Virtual environment active" if in_venv else "Not in virtual environment (recommended)"
    return True, details  # Not critical, just informational

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'websockets',
        'numpy',
        'torch'
    ]
    
    installed = []
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            installed.append(package)
        except ImportError:
            missing.append(package)
    
    status = len(missing) == 0
    if status:
        details = f"All {len(installed)} core packages installed"
    else:
        details = f"Missing: {', '.join(missing)}"
    
    return status, details

def check_optional_dependencies():
    """Check optional but recommended packages"""
    optional_packages = {
        'faster_whisper': 'ASR (Whisper)',
        'argostranslate': 'Translation',
        'piper': 'TTS'
    }
    
    results = []
    for package, description in optional_packages.items():
        try:
            __import__(package)
            results.append((True, f"{description}: installed"))
        except ImportError:
            results.append((False, f"{description}: not installed (models will download on first use)"))
    
    return results

def check_directory_structure():
    """Check if required directories exist"""
    base_dir = Path(__file__).parent
    required_dirs = [
        'backend',
        'backend/pipeline',
        'backend/utils',
        'frontend',
        'models'
    ]
    
    missing = []
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            missing.append(dir_name)
    
    status = len(missing) == 0
    if status:
        details = "All required directories present"
    else:
        details = f"Missing: {', '.join(missing)}"
    
    return status, details

def check_models_directory():
    """Check models directory structure"""
    base_dir = Path(__file__).parent
    models_dir = base_dir / 'models'
    
    if not models_dir.exists():
        return False, "Models directory not found"
    
    subdirs = ['whisper', 'argos', 'piper']
    existing = []
    missing = []
    
    for subdir in subdirs:
        subdir_path = models_dir / subdir
        if subdir_path.exists():
            existing.append(subdir)
        else:
            missing.append(subdir)
    
    if len(existing) == len(subdirs):
        details = "All model subdirectories present"
        status = True
    else:
        details = f"Missing: {', '.join(missing)}"
        status = False
    
    return status, details

def check_port_availability():
    """Check if default port is available"""
    import socket
    
    port = int(os.getenv('TALKFLOW_PORT', '8000'))
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True, f"Port {port} is available"
    except OSError:
        return False, f"Port {port} is in use"

def check_memory():
    """Check available system memory"""
    try:
        import psutil
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        available_gb = mem.available / (1024**3)
        
        status = total_gb >= 8
        details = f"{total_gb:.1f}GB total, {available_gb:.1f}GB available"
        if not status:
            details += " (8GB+ recommended)"
        
        return status, details
    except ImportError:
        return True, "psutil not installed (cannot check memory)"

def main():
    print_header("TalkFlow System Verification")
    
    print("\n📋 System Requirements")
    
    # Python version
    status, details = check_python_version()
    print_check("Python Version", status, details)
    
    # pip
    status, details = check_pip()
    print_check("pip", status, details)
    
    # Virtual environment
    status, details = check_venv()
    print_check("Virtual Environment", status, details)
    
    print("\n📦 Dependencies")
    
    # Core dependencies
    status, details = check_dependencies()
    print_check("Core Packages", status, details)
    
    if not status:
        print("\n  Install with: pip install -r requirements.txt")
    
    # Optional dependencies
    print("\n  Optional Packages:")
    for status, details in check_optional_dependencies():
        print(f"  {'✓' if status else '○'} {details}")
    
    print("\n📁 Project Structure")
    
    # Directory structure
    status, details = check_directory_structure()
    print_check("Required Directories", status, details)
    
    # Models directory
    status, details = check_models_directory()
    print_check("Models Directory", status, details)
    
    if not status:
        print("  Run: mkdir -p models/{whisper,argos,piper}")
    
    print("\n🔧 System Configuration")
    
    # Port availability
    status, details = check_port_availability()
    print_check("Port Availability", status, details)
    
    # Memory
    status, details = check_memory()
    print_check("System Memory", status, details)
    
    print("\n" + "=" * 60)
    print("\n✅ Verification Complete!")
    print("\nNext steps:")
    print("  1. Fix any issues marked with ✗")
    print("  2. Run: python run.py")
    print("  3. Open: http://localhost:8000")
    print("\nFor detailed instructions, see QUICKSTART.md")
    print()

if __name__ == "__main__":
    main()
