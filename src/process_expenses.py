#!/usr/bin/env python3
"""
Expense Processing Pipeline
Combines PDF parsing and LLM-based expense categorization
"""

import json
from pathlib import Path
from .pdf_parser import BankStatementParser
from .expense_categorizer import ExpenseCategorizer
from .lm_studio_client import LMStudioClient


def process_expenses(categorize: bool = True) -> None:
    """
    Complete expense processing pipeline
    
    Args:
        categorize: Whether to run LLM categorization (requires LM Studio running)
    """
    print("="*60)
    print("EXPENSE PROCESSING PIPELINE")
    print("="*60)
    
    # Step 1: Parse PDFs
    print("\n[Step 1] Parsing Bank Statements...")
    print("-" * 60)
    
    parser = BankStatementParser()
    input_dir = Path(__file__).parent.parent / "input"
    output_dir = Path(__file__).parent.parent / "output"
    
    output_dir.mkdir(exist_ok=True)
    
    pdf_files = sorted(list(input_dir.glob("*.pdf")))
    
    if not pdf_files:
        print(f"✗ No PDF files found in {input_dir}")
        return
    
    # Process all PDFs
    all_transactions = []
    for pdf_file in pdf_files:
        print(f"  Processing: {pdf_file.name}")
        text = parser.extract_text_from_pdf(str(pdf_file))
        
        parser.current_bank = parser.extract_bank_name(text, pdf_file.name)
        parser.current_card = parser.extract_card_name(text, pdf_file.name)
        
        transactions = parser.parse_transactions(text)
        all_transactions.extend(transactions)
        print(f"    ✓ Found {len(transactions)} transactions")
    
    # Sort by date
    all_transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    print(f"\n✓ Total transactions parsed: {len(all_transactions)}")
    
    # Step 2: Categorize (if enabled)
    if categorize:
        print("\n[Step 2] Categorizing Expenses with LLM...")
        print("-" * 60)
        
        # Initialize LLM client
        client = LMStudioClient()
        
        # Get and set model
        models = client.get_available_models()
        if not models:
            print("✗ No models available. Make sure LM Studio is running.")
            print("  Skipping categorization. Saving parsed transactions without categories.")
            categorize = False
        else:
            model_id = models[0].get('id')
            client.set_model(model_id)
            print(f"  Using model: {model_id}")
            
            # Categorize transactions
            categorizer = ExpenseCategorizer(client)
            all_transactions = categorizer.categorize_transactions(all_transactions)
            
            # Print summary
            summary = categorizer.get_categorization_summary(all_transactions)
            print(f"\n✓ Categorization complete!")
            print(f"\nSpending Summary by Category:")
            print("-" * 60)
            for cat_id in sorted(summary.keys()):
                cat_info = summary[cat_id]
                print(f"  {cat_info['name']:30} {cat_info['count']:4} transactions ${cat_info['total']:10.2f}")
    
    # Step 3: Save results
    print("\n[Step 3] Saving Results...")
    print("-" * 60)
    
    # Save parsed transactions (without categories)
    json_parsed = output_dir / "all_transactions_parsed.json"
    parser.export_to_json(all_transactions, str(json_parsed))
    
    # Save categorized transactions (if categorization was done)
    if categorize:
        json_categorized = output_dir / "all_transactions_categorized.json"
        with open(json_categorized, 'w') as f:
            json.dump(all_transactions, f, indent=2)
        
        print(f"✓ Parsed transactions: {json_parsed}")
        print(f"✓ Categorized transactions: {json_categorized}")
    else:
        print(f"✓ Parsed transactions: {json_parsed}")
    
    print(f"\n{'='*60}")
    print(f"✓ Processing Complete!")
    print(f"✓ Output files saved in: {output_dir}")
    print(f"  Total transactions: {len(all_transactions)}")
    if categorize:
        print(f"  Categorization: Enabled (using LLM)")
    else:
        print(f"  Categorization: Disabled")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    
    parser_args = argparse.ArgumentParser(description="Process bank statements and categorize expenses")
    parser_args.add_argument(
        "--no-categorize",
        action="store_true",
        help="Skip LLM categorization (only parse PDFs)"
    )
    args = parser_args.parse_args()
    
    process_expenses(categorize=not args.no_categorize)
