#!/usr/bin/env python3

"""
Setup script for OCR Overlay System
Installs dependencies and checks system requirements
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f" {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f" {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f" {description} failed: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def check_tesseract():
    """Check if tesseract is installed"""
    print(" Checking tesseract installation...")
    try:
        result = subprocess.run("tesseract --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(" Tesseract is installed")
            print(f"Version: {result.stdout.split()[1]}")
            return True
        else:
            print(" Tesseract not found")
            return False
    except:
        print(" Tesseract not found")
        return False

def install_tesseract():
    """Install tesseract based on OS"""
    print(" Installing tesseract...")
    
    # Detect OS
    if sys.platform.startswith('linux'):
        # Try different package managers
        for cmd in [
            "sudo apt-get update && sudo apt-get install -y tesseract-ocr",
            "sudo yum install -y tesseract",
            "sudo pacman -S tesseract",
            "sudo dnf install -y tesseract"
        ]:
            if run_command(cmd, "Installing tesseract"):
                return True
    
    elif sys.platform == 'darwin':  # macOS
        if run_command("brew install tesseract", "Installing tesseract"):
            return True
    
    elif sys.platform.startswith('win'):  # Windows
        print(" Please install tesseract manually:")
        print("1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Add to PATH environment variable")
        return False
    
    print(" Unable to install tesseract automatically")
    print("Please install tesseract manually for your OS")
    return False

def main():
    """Main setup process"""
    print(" OCR Overlay System Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print(" Python 3.7 or higher is required")
        sys.exit(1)
    
    print(f" Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Install Python dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print(" Failed to install Python dependencies")
        sys.exit(1)
    
    # Check tesseract
    if not check_tesseract():
        print(" Tesseract OCR not found")
        response = input("Install tesseract automatically? (y/n): ").lower()
        if response == 'y':
            if not install_tesseract():
                print(" Setup incomplete - tesseract installation failed")
                sys.exit(1)
        else:
            print(" Setup incomplete - tesseract required for OCR")
            sys.exit(1)
    
    # Final check
    if check_tesseract():
        print("\n Setup completed successfully!")
        print("Usage: python ocr_overlay.py input_image.jpg")
    else:
        print("\n Setup incomplete")
        sys.exit(1)

if __name__ == "__main__":
    main()