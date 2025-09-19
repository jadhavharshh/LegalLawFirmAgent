#!/usr/bin/env python3
"""
Setup script for Legal LLM training environment
Checks dependencies and data availability
"""

import sys
import subprocess
import importlib
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'torch', 'transformers', 'datasets', 'peft', 'accelerate'
    ]
    
    missing_packages = []
    installed_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            installed_packages.append(package)
            print(f"✅ {package} - installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - not installed")
    
    return missing_packages, installed_packages

def check_data():
    """Check if processed data is available"""
    data_dir = Path("data/processed")
    required_files = ["train.jsonl", "validation.jsonl", "combined_legal_instructions.jsonl"]
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return False
    
    missing_files = []
    for file in required_files:
        file_path = data_dir / file
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"✅ {file} - {size_mb:.2f} MB")
        else:
            missing_files.append(file)
            print(f"❌ {file} - not found")
    
    return len(missing_files) == 0

def install_missing_packages(packages):
    """Install missing packages"""
    if not packages:
        return True
    
    print(f"\n📦 Installing missing packages: {', '.join(packages)}")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements_training.txt"
        ])
        print("✅ Package installation completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Package installation failed: {e}")
        return False

def test_data_loading():
    """Test loading a sample of the training data"""
    try:
        import json
        data_file = Path("data/processed/train.jsonl")
        
        if not data_file.exists():
            print("❌ Training data not found")
            return False
        
        # Read first few samples
        samples = []
        with open(data_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 3:  # Just test first 3 samples
                    break
                samples.append(json.loads(line))
        
        print(f"✅ Successfully loaded {len(samples)} training samples")
        
        # Show sample structure
        if samples:
            print("\n📋 Sample data structure:")
            sample = samples[0]
            for key, value in sample.items():
                print(f"  {key}: {str(value)[:100]}..." if len(str(value)) > 100 else f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data loading test failed: {e}")
        return False

def main():
    print("🏛️  Legal LLM Training Setup")
    print("=" * 50)
    
    # Check dependencies
    print("\n1️⃣  Checking dependencies...")
    missing, installed = check_dependencies()
    
    if missing:
        print(f"\n🔧 Missing packages detected. Installing...")
        if not install_missing_packages(missing):
            print("❌ Failed to install packages. Please install manually:")
            print(f"   pip install -r requirements_training.txt")
            return False
    
    # Check data
    print("\n2️⃣  Checking training data...")
    data_ok = check_data()
    
    if not data_ok:
        print("\n❌ Training data not found or incomplete.")
        print("🔧 Run the preprocessing script first:")
        print("   python3 preprocess_legal_data.py")
        return False
    
    # Test data loading
    print("\n3️⃣  Testing data loading...")
    if not test_data_loading():
        return False
    
    print("\n✅ Setup check completed successfully!")
    print("\n🚀 Ready to start training!")
    print("\nNext steps:")
    print("1. Test data processing: python3 train_legal_model.py --test_only")
    print("2. Start training: python3 train_legal_model.py --epochs 2 --max_train_samples 1000")
    print("3. Full training: python3 train_legal_model.py --epochs 5")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)