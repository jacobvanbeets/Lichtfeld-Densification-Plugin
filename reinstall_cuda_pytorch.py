#!/usr/bin/env python3
"""Post-install script to ensure CUDA PyTorch is installed instead of CPU-only version."""

import subprocess
import sys
import os
import shutil

def log(msg):
    print(f"[CUDA PyTorch Installer] {msg}", flush=True)

def find_uv():
    """Find uv executable in LichtFeld installation."""
    # Try in PATH first
    uv_in_path = shutil.which('uv')
    if uv_in_path:
        return uv_in_path
    
    # Search common locations relative to python executable
    # Plugin venv structure: .lichtfeld/plugins/<name>/.venv/Scripts/python.exe
    # LichtFeld structure: <lichtfeld_dir>/bin/uv.exe
    
    search_dirs = [
        # From venv, go up to find bin directory
        os.path.join(os.path.dirname(sys.executable), '..', '..', '..', '..', '..'),
        # Try user's home directory repos
        os.path.expanduser('~/repos'),
        # Try common Windows install locations
        'C:\\Program Files\\LichtFeld Studio',
        'C:\\Program Files (x86)\\LichtFeld Studio',
    ]
    
    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        # Search for uv.exe in this directory tree (max depth 3)
        for root, dirs, files in os.walk(search_dir):
            # Limit search depth
            depth = root[len(search_dir):].count(os.sep)
            if depth > 3:
                continue
            if 'uv.exe' in files:
                uv_path = os.path.join(root, 'uv.exe')
                if os.path.isfile(uv_path):
                    return os.path.abspath(uv_path)
    
    return None

def main():
    log("Checking PyTorch installation...")
    
    has_cuda = False
    pytorch_broken = False
    
    try:
        import torch
        has_cuda = torch.cuda.is_available()
        version = torch.__version__
        
        log(f"Current PyTorch: {version}")
        log(f"CUDA available: {has_cuda}")
        
        if has_cuda:
            log("CUDA PyTorch already installed - no action needed")
            return 0
            
        log("CPU-only PyTorch detected - reinstalling with CUDA support...")
        
    except OSError as e:
        if "shm.dll" in str(e) or "WinError 126" in str(e):
            log(f"PyTorch installation is broken (DLL error) - will reinstall with CUDA support...")
            pytorch_broken = True
        else:
            raise
    except ImportError:
        log("PyTorch not found - will install CUDA version...")
    
    # Find uv executable
    uv_path = find_uv()
    if not uv_path:
        log("ERROR: Could not find uv executable. Cannot reinstall PyTorch.")
        log("Please manually install CUDA PyTorch using:")
        log(f"  uv pip install torch>=2.6.0 torchvision>=0.21.0 --index-url https://download.pytorch.org/whl/cu128 --python {sys.executable}")
        return 1
    
    log(f"Found uv at: {uv_path}")
    
    # Uninstall existing torch/torchvision
    log("Uninstalling CPU-only PyTorch...")
    try:
        subprocess.run(
            [uv_path, "pip", "uninstall", "-y", "torch", "torchvision", "--python", sys.executable],
            check=False,
            capture_output=True
        )
    except Exception as e:
        log(f"Warning during uninstall: {e}")
    
    # Install CUDA version
    log("Installing CUDA PyTorch (CUDA 12.8 for RTX 5080 support)...")
    try:
        result = subprocess.run(
            [
                uv_path, "pip", "install",
                "torch>=2.6.0",
                "torchvision>=0.21.0",
                "--index-url", "https://download.pytorch.org/whl/cu128",
                "--python", sys.executable
            ],
            check=True,
            capture_output=True,
            text=True
        )
        log("CUDA PyTorch installed successfully!")
        
        # Verify installation
        import torch
        if torch.cuda.is_available():
            log(f"✓ Verified: PyTorch {torch.__version__} with CUDA {torch.version.cuda}")
            return 0
        else:
            log("⚠ Warning: CUDA still not available after installation")
            log("This may be due to incompatible CUDA drivers")
            return 1
            
    except subprocess.CalledProcessError as e:
        log(f"Error installing CUDA PyTorch: {e}")
        log(f"stdout: {e.stdout}")
        log(f"stderr: {e.stderr}")
        return 1
    except Exception as e:
        log(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
