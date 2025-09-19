#!/usr/bin/env python3
"""
Quick training test with a small model to verify the pipeline works
"""

import os
import subprocess
import sys

def run_training_test():
    """Run a quick training test"""
    print("🧪 Running quick training test...")
    
    # Test with small model and limited data
    cmd = [
        "python3", "train_legal_model.py",
        "--model_name", "distilbert-base-uncased",  # Very small model
        "--epochs", "1",
        "--batch_size", "1", 
        "--max_train_samples", "50",
        "--learning_rate", "5e-5",
        "--output_dir", "models/legal-test-small",
        "--max_length", "512"
    ]
    
    print(f"🚀 Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 min timeout
        
        if result.returncode == 0:
            print("✅ Quick training test passed!")
            print("📊 Training output:")
            print(result.stdout[-500:])  # Last 500 chars
            return True
        else:
            print("❌ Quick training test failed!")
            print("📊 Error output:")
            print(result.stderr[-500:])  # Last 500 chars
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Training test timed out (10 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def main():
    print("🏛️  Legal LLM Quick Training Test")
    print("=" * 50)
    
    # Check if we have the required files
    required_files = [
        "train_legal_model.py",
        "data/processed/train.jsonl",
        "data/processed/validation.jsonl"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    # Run the test
    success = run_training_test()
    
    if success:
        print("\n🎉 Quick test successful!")
        print("\n📝 Next steps for full training:")
        print("1. Use a proper Qwen model: --model_name Qwen/Qwen2.5-7B-Instruct")
        print("2. Increase training data: --max_train_samples 5000")
        print("3. Train for more epochs: --epochs 3-5")
        print("4. Use larger batch size if you have GPU: --batch_size 4-8")
        print("5. Monitor with wandb: --use_wandb")
    else:
        print("\n❌ Test failed. Check the error messages above.")
        print("\n💡 Try with an even smaller model if needed:")
        print("   --model_name prajjwal1/bert-tiny")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)