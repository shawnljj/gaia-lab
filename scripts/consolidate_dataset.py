#!/usr/bin/env python3
"""
Consolidate all JSONL batch files into the main dataset JSON files.
This ensures Moonshot can see all 1,010 prompts instead of just the ~200 embedded examples.
"""

import json
from pathlib import Path

def consolidate_dataset():
    """Merge all batch JSONL files into dataset JSON files."""
    
    # Batch files to consolidate
    batch_files = [
        'moonshot-data/datasets/support_engineer/batch_00_core.jsonl',
        'moonshot-data/datasets/support_engineer/batch_01_technical.jsonl',
        'moonshot-data/datasets/support_engineer/batch_02_billing.jsonl',
        'moonshot-data/datasets/support_engineer/batch_03_escalation.jsonl',
        'moonshot-data/datasets/support_engineer/batch_04_difficult_customers.jsonl',
        'moonshot-data/datasets/support_engineer/batch_05_integration.jsonl',
        'moonshot-data/datasets/support_engineer/batch_06_security.jsonl',
        'moonshot-data/datasets/support_engineer/batch_07_onboarding.jsonl',
        'moonshot-data/datasets/support_engineer/batch_08_product.jsonl',
        'moonshot-data/datasets/support_engineer/batch_09_performance.jsonl',
        'moonshot-data/datasets/support_engineer/batch_10_mixed.jsonl',
    ]
    
    # Read all JSONL prompts
    examples = []
    for batch_file in batch_files:
        print(f"Reading {batch_file}...")
        with open(batch_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                examples.append({
                    'input': data.get('prompt', data.get('input', '')),
                    'target': data.get('expected', data.get('target', ''))
                })
    
    print(f"Total prompts loaded: {len(examples)}")
    
    # Update dataset JSON files
    dataset_files = [
        'moonshot-data/datasets/enterprise-support-engineer.json',
        'moonshot-data/datasets/support_engineer.json'
    ]
    
    for dataset_file in dataset_files:
        print(f"Updating {dataset_file}...")
        
        # Read existing dataset
        with open(dataset_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        # Update examples
        dataset['examples'] = examples
        dataset['description'] = f"Comprehensive dataset with 1,010 prompts for evaluating LLM performance in enterprise customer support scenarios across 11 thematic batches."
        
        # Write back
        with open(dataset_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Updated {dataset_file} with {len(examples)} prompts")
    
    print(f"\n✅ Consolidation complete! All dataset JSON files now contain {len(examples)} prompts.")

if __name__ == '__main__':
    consolidate_dataset()
