#!/usr/bin/env python3
"""
Legal LLM Fine-tuning Script for Qwen3 8B
Uses LoRA/QLoRA for efficient fine-tuning on Indian legal datasets
"""

import os
import json
import torch
import argparse
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime

# Transformers and training libraries
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset, load_dataset
import wandb


@dataclass
class ModelArguments:
    """Model configuration arguments"""
    model_name: str = "microsoft/DialoGPT-medium"  # Use smaller model for testing
    model_path: str = ""  # Local path to model if using Ollama export
    use_local_model: bool = False  # Use local Ollama model
    max_length: int = 1024  # Maximum sequence length
    

@dataclass 
class DataArguments:
    """Data configuration arguments"""
    data_dir: str = "data/processed"
    train_file: str = "train.jsonl"
    validation_file: str = "validation.jsonl" 
    max_train_samples: int = None  # Limit training samples for testing


@dataclass
class LoraArguments:
    """LoRA configuration arguments"""
    lora_rank: int = 8  # LoRA rank
    lora_alpha: int = 16  # LoRA alpha
    lora_dropout: float = 0.1  # LoRA dropout
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj", "k_proj", "o_proj"])


class LegalLLMTrainer:
    """Trainer for Legal LLM fine-tuning"""
    
    def __init__(self, model_args: ModelArguments, data_args: DataArguments, 
                 lora_args: LoraArguments):
        self.model_args = model_args
        self.data_args = data_args
        self.lora_args = lora_args
        self.data_dir = Path(data_args.data_dir)
        
        # Setup device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🚀 Using device: {self.device}")
        
        # Initialize components
        self.tokenizer = None
        self.model = None
        self.train_dataset = None
        self.val_dataset = None
    
    def load_tokenizer_and_model(self):
        """Load tokenizer and model"""
        print(f"📚 Loading model: {self.model_args.model_name}")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_args.model_name,
                trust_remote_code=True,
                padding_side="right"
            )
            
            # Add pad token if not exists
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model with quantization for memory efficiency
            model_kwargs = {
                "trust_remote_code": True,
                "torch_dtype": torch.float16,
                "device_map": "auto",
            }
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_args.model_name,
                **model_kwargs
            )
            
            print(f"✅ Model loaded successfully")
            print(f"📊 Model parameters: {self.model.num_parameters():,}")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("💡 Make sure you have the model downloaded or use a different model_name")
            raise e
    
    def setup_lora(self):
        """Setup LoRA configuration"""
        print("🔧 Setting up LoRA configuration...")
        
        lora_config = LoraConfig(
            r=self.lora_args.lora_rank,
            lora_alpha=self.lora_args.lora_alpha,
            target_modules=self.lora_args.target_modules,
            lora_dropout=self.lora_args.lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )
        
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
        
        print("✅ LoRA setup complete")
    
    def load_datasets(self):
        """Load and prepare training datasets"""
        print("📁 Loading datasets...")
        
        train_file = self.data_dir / self.data_args.train_file
        val_file = self.data_dir / self.data_args.validation_file
        
        if not train_file.exists():
            raise FileNotFoundError(f"Training file not found: {train_file}")
        if not val_file.exists():
            raise FileNotFoundError(f"Validation file not found: {val_file}")
        
        # Load datasets
        dataset_files = {
            "train": str(train_file),
            "validation": str(val_file)
        }
        
        raw_datasets = load_dataset("json", data_files=dataset_files)
        
        print(f"📊 Train samples: {len(raw_datasets['train'])}")
        print(f"📊 Validation samples: {len(raw_datasets['validation'])}")
        
        # Limit samples if specified
        if self.data_args.max_train_samples:
            raw_datasets["train"] = raw_datasets["train"].select(range(self.data_args.max_train_samples))
            print(f"🔍 Limited to {self.data_args.max_train_samples} training samples")
        
        # Store raw datasets for later tokenization
        self.raw_train_dataset = raw_datasets["train"]
        self.raw_val_dataset = raw_datasets["validation"]
        
        print("✅ Datasets loaded (tokenization will happen after model loading)")
    
    def tokenize_datasets(self):
        """Tokenize the datasets after model and tokenizer are loaded"""
        if self.tokenizer is None:
            raise ValueError("Tokenizer not loaded. Call load_tokenizer_and_model() first.")
        
        print("🔤 Tokenizing datasets...")
        
        # Tokenize datasets
        self.train_dataset = self.raw_train_dataset.map(
            self.preprocess_function,
            batched=True,
            remove_columns=self.raw_train_dataset.column_names,
            desc="Tokenizing train dataset"
        )
        
        self.val_dataset = self.raw_val_dataset.map(
            self.preprocess_function, 
            batched=True,
            remove_columns=self.raw_val_dataset.column_names,
            desc="Tokenizing validation dataset"
        )
        
        print("✅ Datasets tokenized")
    
    def preprocess_function(self, examples):
        """Preprocess examples for training"""
        # Create input-output pairs
        inputs = []
        for instruction, input_text, output_text in zip(
            examples["instruction"], examples["input"], examples["output"]
        ):
            # Format as conversation
            if input_text.strip():
                prompt = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n"
            else:
                prompt = f"### Instruction:\n{instruction}\n\n### Response:\n"
            
            eos_token = self.tokenizer.eos_token if self.tokenizer.eos_token else "</s>"
            full_text = prompt + output_text + eos_token
            inputs.append(full_text)
        
        # Tokenize
        model_inputs = self.tokenizer(
            inputs,
            max_length=self.model_args.max_length,
            truncation=True,
            padding=False,  # Will be done by data collator
        )
        
        # Labels are same as input_ids for causal LM
        model_inputs["labels"] = model_inputs["input_ids"].copy()
        
        return model_inputs
    
    def train(self, output_dir: str = "models/legal-qwen3-lora", 
              num_train_epochs: int = 3,
              per_device_train_batch_size: int = 2,
              gradient_accumulation_steps: int = 8,
              learning_rate: float = 2e-4,
              warmup_steps: int = 100,
              logging_steps: int = 10,
              save_steps: int = 500,
              eval_steps: int = 500,
              use_wandb: bool = False):
        """Train the model"""
        
        print("🏋️ Starting training...")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(output_path),
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            per_device_eval_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            weight_decay=0.01,
            warmup_steps=warmup_steps,
            logging_steps=logging_steps,
            evaluation_strategy="steps",
            eval_steps=eval_steps,
            save_strategy="steps",
            save_steps=save_steps,
            save_total_limit=3,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to="wandb" if use_wandb else None,
            run_name=f"legal-qwen3-{datetime.now().strftime('%Y%m%d-%H%M%S')}" if use_wandb else None,
            dataloader_pin_memory=False,
            fp16=True,  # Enable mixed precision
            gradient_checkpointing=True,  # Save memory
        )
        
        # Data collator
        data_collator = DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer,
            model=self.model,
            padding=True
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.val_dataset,
            tokenizer=self.tokenizer,
            data_collator=data_collator,
        )
        
        # Start training
        print("🚀 Training started!")
        train_result = trainer.train()
        
        # Save model
        trainer.save_model()
        trainer.save_state()
        
        print("✅ Training completed!")
        print(f"💾 Model saved to: {output_path}")
        
        return train_result
    
    def test_model(self, prompt: str = None):
        """Test the trained model with a sample prompt"""
        if prompt is None:
            prompt = "### Instruction:\nAnswer the following question about the Indian Constitution:\n\n### Input:\nWhat is the fundamental right to equality?\n\n### Response:\n"
        
        print(f"🧪 Testing model with prompt: {prompt[:100]}...")
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=inputs.input_ids.shape[1] + 200,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"🤖 Model response:\n{response[len(prompt):]}")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune Qwen3 on Indian legal data")
    
    # Model arguments
    parser.add_argument("--model_name", default="microsoft/DialoGPT-medium", 
                       help="Model name or path (use smaller model for testing)")
    parser.add_argument("--max_length", type=int, default=1024, help="Max sequence length")
    
    # Data arguments  
    parser.add_argument("--data_dir", default="data/processed", 
                       help="Data directory")
    parser.add_argument("--max_train_samples", type=int, default=1000, 
                       help="Limit training samples for testing")
    
    # Training arguments
    parser.add_argument("--output_dir", default="models/legal-llm-lora", 
                       help="Output directory")
    parser.add_argument("--epochs", type=int, default=2, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--use_wandb", action="store_true", help="Use Weights & Biases")
    
    # LoRA arguments
    parser.add_argument("--lora_rank", type=int, default=8, help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=16, help="LoRA alpha")
    
    # Actions
    parser.add_argument("--test_only", action="store_true", help="Only test preprocessing")
    
    args = parser.parse_args()
    
    print("🏛️  Legal LLM Fine-tuning")
    print("=" * 50)
    
    # Configuration
    model_args = ModelArguments(
        model_name=args.model_name,
        max_length=args.max_length
    )
    
    data_args = DataArguments(
        data_dir=args.data_dir,
        max_train_samples=args.max_train_samples
    )
    
    lora_args = LoraArguments(
        lora_rank=args.lora_rank,
        lora_alpha=args.lora_alpha
    )
    
    # Initialize trainer
    trainer = LegalLLMTrainer(model_args, data_args, lora_args)
    
    try:
        # Load data first
        trainer.load_datasets()
        
        if args.test_only:
            print("✅ Data loading test passed!")
            return
        
        # Load model and tokenizer
        trainer.load_tokenizer_and_model()
        
        # Tokenize datasets now that we have the tokenizer
        trainer.tokenize_datasets()
        
        # Setup LoRA
        trainer.setup_lora()
        
        # Start training
        trainer.train(
            output_dir=args.output_dir,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            use_wandb=args.use_wandb
        )
        
        # Test the model
        trainer.test_model()
        
        print(f"\n🎉 Training complete! Model saved to: {args.output_dir}")
        
    except Exception as e:
        print(f"❌ Error during training: {e}")
        raise e


if __name__ == "__main__":
    main()