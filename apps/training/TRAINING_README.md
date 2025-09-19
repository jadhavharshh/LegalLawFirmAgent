# Legal Law Firm Agent - Model Training

This directory contains scripts and data for fine-tuning LLMs on Indian legal datasets for your Legal Law Firm Agent project.

## 📁 Project Structure

```
apps/training/
├── data/
│   ├── legal_qa/                    # Raw Kaggle datasets
│   └── processed/                   # Processed JSONL files
│       ├── train.jsonl              # Training data (13,178 samples)
│       ├── validation.jsonl         # Validation data (1,465 samples)
│       └── combined_legal_instructions.jsonl
├── models/                          # Output directory for trained models
├── preprocess_legal_data.py         # Data preprocessing script
├── train_legal_model.py             # Main training script
├── setup_training.py                # Environment setup checker
├── quick_train_test.py              # Quick test with small model
├── requirements_training.txt        # Python dependencies
├── TRAINING_README.md              # Quick reference guide
└── Explanation.md                   # Comprehensive documentation
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Install dependencies
pip install -r requirements_training.txt

# Verify setup
python3 setup_training.py
```

### 2. Data Processing (Already Done)
The Indian legal QA datasets have been processed into instruction format:
- **Constitution QA**: 4,082 samples + 100 variations
- **IPC QA**: 2,267 samples  
- **CrPC QA**: 8,194 samples
- **Total**: 14,643 instruction-formatted samples

### 3. Quick Test Training
```bash
# Test with small model (recommended first step)
python3 quick_train_test.py
```

### 4. Full Training Options

#### Option A: Start with Medium Model
```bash
python3 train_legal_model.py \
  --model_name microsoft/DialoGPT-medium \
  --epochs 2 \
  --max_train_samples 2000 \
  --batch_size 2 \
  --output_dir models/legal-medium-test
```

#### Option B: Use Qwen Model (Requires More RAM/GPU)
```bash
python3 train_legal_model.py \
  --model_name Qwen/Qwen2.5-7B-Instruct \
  --epochs 3 \
  --max_train_samples 5000 \
  --batch_size 1 \
  --output_dir models/legal-qwen-lora
```

#### Option C: Full Training
```bash
python3 train_legal_model.py \
  --model_name Qwen/Qwen2.5-7B-Instruct \
  --epochs 5 \
  --batch_size 2 \
  --output_dir models/legal-qwen-full \
  --use_wandb
```

## 📊 Dataset Details

### Processed Data Format
Each sample has the instruction format:
```json
{
  "instruction": "Answer the following question about the Indian Constitution:",
  "input": "What is the fundamental right to equality?",
  "output": "Article 14 guarantees equality before law..."
}
```

### Dataset Sources
- **akshatgupta7/llm-fine-tuning-dataset-of-indian-legal-texts** (Kaggle)
- Covers: Indian Constitution, IPC, CrPC
- Format: Question-Answer pairs optimized for LLM fine-tuning

## ⚙️ Configuration Options

### Model Arguments
- `--model_name`: HuggingFace model name
- `--max_length`: Maximum sequence length (default: 1024)

### Training Arguments  
- `--epochs`: Number of training epochs
- `--batch_size`: Training batch size
- `--learning_rate`: Learning rate (default: 2e-4)
- `--max_train_samples`: Limit training samples for testing

### LoRA Arguments
- `--lora_rank`: LoRA rank (default: 8)
- `--lora_alpha`: LoRA alpha (default: 16)

## 🔧 Hardware Requirements

### Minimum (CPU Training)
- 8GB RAM
- Small models (DialoGPT-medium, BERT variants)
- Batch size: 1-2

### Recommended (GPU Training)
- 16GB+ GPU VRAM (RTX 4090, A100)  
- Qwen 7B models with LoRA
- Batch size: 4-8

### For Qwen3 8B via Ollama
If you're using Ollama locally:
1. Export Ollama model to HuggingFace format
2. Use `--model_path` to point to local model
3. Enable `--use_local_model`

## 📈 Monitoring Training

### With Weights & Biases
```bash
# Enable W&B logging
python3 train_legal_model.py --use_wandb

# View training at https://wandb.ai
```

### Without W&B
Training logs will show:
- Loss curves
- Learning rate schedule  
- Memory usage
- Training speed

## 🧪 Testing Trained Model

After training, test your model:
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Load base model
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

# Load LoRA weights
model = PeftModel.from_pretrained(model, "models/legal-qwen-lora")

# Test prompt
prompt = "### Instruction:\nAnswer the following question about the Indian Constitution:\n\n### Input:\nWhat is Article 21?\n\n### Response:\n"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_length=200, do_sample=True, temperature=0.7)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)
```

## 📝 Next Steps

1. **Test Training Pipeline**: Run `quick_train_test.py` first
2. **Start Small**: Use DialoGPT-medium for initial testing
3. **Scale Up**: Move to Qwen models once pipeline is verified
4. **Evaluate**: Test model responses on legal questions
5. **Deploy**: Integrate trained model with your Legal Agent system

## 🆘 Troubleshooting

### Memory Issues
- Reduce `--batch_size` to 1
- Reduce `--max_length` to 512
- Use smaller model variants
- Enable gradient checkpointing (already enabled)

### Training Slow
- Use GPU if available
- Increase `--batch_size` if memory allows
- Use mixed precision (fp16 enabled by default)

### Model Loading Errors
- Check model name spelling
- Ensure internet connection for HuggingFace downloads
- Try smaller models for testing

## 📚 Resources

- [Qwen Model Documentation](https://huggingface.co/Qwen)
- [LoRA Fine-tuning Guide](https://huggingface.co/docs/peft/conceptual_guides/lora)
- [Transformers Training](https://huggingface.co/docs/transformers/training)
- [Indian Legal Datasets](https://www.kaggle.com/datasets/akshatgupta7/llm-fine-tuning-dataset-of-indian-legal-texts)

---

**Ready to train your Legal LLM! 🏛️⚖️🤖**