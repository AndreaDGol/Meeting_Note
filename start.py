#!/usr/bin/env python3
"""
Startup script for Handwritten Notes Processing Agents
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_tesseract():
    """Check if Tesseract OCR is installed"""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Tesseract OCR: {version}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ Tesseract OCR not found")
    print("Please install Tesseract OCR:")
    if platform.system() == "Darwin":  # macOS
        print("  brew install tesseract")
    elif platform.system() == "Linux":
        print("  sudo apt-get install tesseract-ocr")
    elif platform.system() == "Windows":
        print("  Download from: https://github.com/UB-Mannheim/tesseract/wiki")
    return False

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Set up environment file if it doesn't exist"""
    env_file = Path('.env')
    env_example = Path('env.example')
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        with open(env_example, 'r') as f:
            content = f.read()
        with open(env_file, 'w') as f:
            f.write(content)
        print("✅ .env file created")
        print("⚠️  Please edit .env file and add your OpenAI API key")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️  No environment template found")

def create_directories():
    """Create necessary directories"""
    directories = ['uploads', 'processed', 'static']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Directories created")

def main():
    """Main startup function"""
    print("🚀 Starting Handwritten Notes Processing Agents Setup")
    print("=" * 60)
    
    # Check requirements
    if not check_python_version():
        sys.exit(1)
    
    if not check_tesseract():
        print("\n⚠️  Tesseract OCR is required for OCR functionality")
        print("   You can continue without it, but OCR features won't work")
        response = input("Continue anyway? (y/N): ").lower()
        if response != 'y':
            sys.exit(1)
    
    # Setup
    create_directories()
    setup_environment()
    
    if not install_dependencies():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your OpenAI API key (optional but recommended)")
    print("2. Run: python main.py")
    print("3. Open your browser to: http://localhost:8000")
    print("\n🎉 Happy note processing!")

if __name__ == "__main__":
    main()


