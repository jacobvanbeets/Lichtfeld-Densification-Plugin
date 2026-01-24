#!/usr/bin/env python3
"""Post-install script to ensure CUDA PyTorch is installed instead of CPU-only version."""

import subprocess
import sys

def log(msg):
    print(f"[CUDA PyTorch Installer] {msg}", flush=True)

def main():
    log("Checking PyTorch installation...")
    
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
        
    except ImportError:
        log("PyTorch not found - will install CUDA version...")
    
    # Uninstall existing torch/torchvision
    log("Uninstalling CPU-only PyTorch...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "torch", "torchvision"],
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
                sys.executable, "-m", "pip", "install",
                "torch>=2.6.0",
                "torchvision>=0.21.0",
                "--index-url", "https://download.pytorch.org/whl/cu128"
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
