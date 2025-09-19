#!/usr/bin/env python3
"""
Legal Dataset Preprocessing Script for Fine-tuning
Converts Indian legal QA datasets to JSONL instruction format for LLM training
"""

import json
import os
from typing import List, Dict, Any
import argparse
from pathlib import Path


class LegalDataPreprocessor:
    """Preprocessor for converting legal QA datasets to instruction format"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.legal_qa_dir = self.data_dir / "legal_qa"
        self.output_dir = self.data_dir / "processed"
        self.output_dir.mkdir(exist_ok=True)
    
    def load_qa_dataset(self, filepath: Path) -> List[Dict[str, Any]]:
        """Load QA dataset from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Loaded {len(data)} QA pairs from {filepath.name}")
            return data
        except Exception as e:
            print(f"❌ Error loading {filepath}: {e}")
            return []
    
    def convert_to_instruction_format(self, qa_data: List[Dict], 
                                    source_name: str) -> List[Dict[str, str]]:
        """Convert QA data to instruction format"""
        instructions = []
        
        # Define instruction templates based on source
        if "constitution" in source_name.lower():
            instruction_template = "Answer the following question about the Indian Constitution:"
            context = "Indian Constitution"
        elif "ipc" in source_name.lower():
            instruction_template = "Answer the following question about the Indian Penal Code (IPC):"
            context = "Indian Penal Code"
        elif "crpc" in source_name.lower():
            instruction_template = "Answer the following question about the Code of Criminal Procedure (CrPC):"
            context = "Code of Criminal Procedure"
        else:
            instruction_template = "Answer the following legal question:"
            context = "Indian Legal System"
        
        for item in qa_data:
            if "question" in item and "answer" in item:
                # Create instruction format
                instruction_item = {
                    "instruction": instruction_template,
                    "input": item["question"],
                    "output": item["answer"]
                }
                instructions.append(instruction_item)
        
        print(f"✅ Converted {len(instructions)} items from {source_name}")
        return instructions
    
    def create_variations(self, instructions: List[Dict[str, str]], 
                         source_name: str) -> List[Dict[str, str]]:
        """Create variations of instructions for better training diversity"""
        variations = []
        
        # Original instructions
        variations.extend(instructions)
        
        # Add summarization variations
        if "constitution" in source_name.lower():
            for item in instructions[:100]:  # Limit to avoid too much data
                summary_item = {
                    "instruction": "Provide a brief explanation of this constitutional provision:",
                    "input": item["input"],
                    "output": f"Constitutional Provision: {item['output']}"
                }
                variations.append(summary_item)
        
        return variations
    
    def save_jsonl(self, data: List[Dict[str, str]], filepath: Path):
        """Save data in JSONL format"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for item in data:
                    json.dump(item, f, ensure_ascii=False)
                    f.write('\n')
            print(f"✅ Saved {len(data)} items to {filepath}")
        except Exception as e:
            print(f"❌ Error saving {filepath}: {e}")
    
    def process_all_datasets(self):
        """Process all available QA datasets"""
        all_instructions = []
        
        # Process each QA file
        qa_files = [
            "constitution_qa.json",
            "ipc_qa.json", 
            "crpc_qa.json"
        ]
        
        for qa_file in qa_files:
            filepath = self.legal_qa_dir / qa_file
            if filepath.exists():
                print(f"\n📁 Processing {qa_file}...")
                
                # Load QA data
                qa_data = self.load_qa_dataset(filepath)
                if not qa_data:
                    continue
                
                # Convert to instruction format
                instructions = self.convert_to_instruction_format(qa_data, qa_file)
                
                # Create variations
                varied_instructions = self.create_variations(instructions, qa_file)
                
                # Save individual file
                output_file = self.output_dir / f"{qa_file.replace('.json', '_processed.jsonl')}"
                self.save_jsonl(varied_instructions, output_file)
                
                # Add to combined dataset
                all_instructions.extend(varied_instructions)
            else:
                print(f"⚠️  File not found: {filepath}")
        
        # Save combined dataset
        if all_instructions:
            combined_output = self.output_dir / "combined_legal_instructions.jsonl"
            self.save_jsonl(all_instructions, combined_output)
            
            # Create train/validation split
            self.create_train_val_split(all_instructions)
            
            print(f"\n🎯 Total processed instructions: {len(all_instructions)}")
        else:
            print("❌ No data processed!")
    
    def create_train_val_split(self, all_instructions: List[Dict[str, str]], 
                              split_ratio: float = 0.9):
        """Create train/validation split"""
        import random
        random.seed(42)  # For reproducibility
        
        # Shuffle data
        shuffled_data = all_instructions.copy()
        random.shuffle(shuffled_data)
        
        # Split
        split_idx = int(len(shuffled_data) * split_ratio)
        train_data = shuffled_data[:split_idx]
        val_data = shuffled_data[split_idx:]
        
        # Save splits
        train_file = self.output_dir / "train.jsonl"
        val_file = self.output_dir / "validation.jsonl"
        
        self.save_jsonl(train_data, train_file)
        self.save_jsonl(val_data, val_file)
        
        print(f"📊 Train split: {len(train_data)} items")
        print(f"📊 Validation split: {len(val_data)} items")
    
    def show_sample_data(self, num_samples: int = 3):
        """Show sample processed data"""
        combined_file = self.output_dir / "combined_legal_instructions.jsonl"
        if combined_file.exists():
            print(f"\n🔍 Sample processed data from {combined_file}:")
            with open(combined_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= num_samples:
                        break
                    data = json.loads(line)
                    print(f"\n--- Sample {i+1} ---")
                    print(f"Instruction: {data['instruction']}")
                    print(f"Input: {data['input'][:100]}..." if len(data['input']) > 100 else f"Input: {data['input']}")
                    print(f"Output: {data['output'][:100]}..." if len(data['output']) > 100 else f"Output: {data['output']}")


def main():
    parser = argparse.ArgumentParser(description='Preprocess legal datasets for fine-tuning')
    parser.add_argument('--data_dir', default='data', 
                       help='Data directory containing legal_qa folder')
    parser.add_argument('--show_samples', action='store_true',
                       help='Show sample processed data')
    
    args = parser.parse_args()
    
    print("🏛️  Legal Dataset Preprocessor")
    print("=" * 50)
    
    # Initialize preprocessor
    preprocessor = LegalDataPreprocessor(args.data_dir)
    
    # Process all datasets
    preprocessor.process_all_datasets()
    
    # Show samples if requested
    if args.show_samples:
        preprocessor.show_sample_data()
    
    print("\n✅ Preprocessing complete!")
    print(f"📁 Output directory: {preprocessor.output_dir}")
    print("Files created:")
    print("  - train.jsonl (training data)")
    print("  - validation.jsonl (validation data)")
    print("  - combined_legal_instructions.jsonl (all data)")
    print("  - individual processed files")


if __name__ == "__main__":
    main()