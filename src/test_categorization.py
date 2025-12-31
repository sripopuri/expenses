#!/usr/bin/env python3
"""
Test script to categorize top N transactions
Useful for testing categorization without processing entire dataset
"""

import json
from pathlib import Path
from pdf_parser import BankStatementParser
from expense_categorizer import ExpenseCategorizer
from lm_studio_client import LMStudioClient


def test_categorization(num_transactions: int = 10) -> None:
    """
    Test categorization on a limited number of transactions
    
    Args:
        num_transactions: Number of transactions to categorize
    """
    print("="*70)
    print(f"EXPENSE CATEGORIZATION TEST - Top {num_transactions} Transactions")
    print("="*70)
    
    # Step 1: Load parsed transactions
    print("\n[Step 1] Loading Parsed Transactions...")
    print("-" * 70)
    
    output_dir = Path(__file__).parent.parent / "output"
    json_file = output_dir / "all_transactions.json"
    
    if not json_file.exists():
        print(f"✗ No parsed transactions found. Run 'python src/pdf_parser.py' first.")
        return
    
    with open(json_file, 'r') as f:
        all_transactions = json.load(f)
    
    print(f"✓ Loaded {len(all_transactions)} total transactions")
    
    # Take only top N transactions
    test_transactions = all_transactions[:num_transactions]
    print(f"✓ Testing with top {len(test_transactions)} transactions")
    
    # Step 2: Initialize LLM
    print("\n[Step 2] Initializing LLM Client...")
    print("-" * 70)
    
    client = LMStudioClient()
    
    models = client.get_available_models()
    if not models:
        print("✗ No models available. Make sure LM Studio is running.")
        return
    
    model_id = models[0].get('id')
    client.set_model(model_id)
    print(f"✓ Using model: {model_id}")
    
    # Step 3: Categorize
    print(f"\n[Step 3] Categorizing {len(test_transactions)} Transactions...")
    print("-" * 70)
    
    categorizer = ExpenseCategorizer(client)
    categorized_transactions = categorizer.categorize_transactions(test_transactions)
    
    # Step 4: Display Results
    print(f"\n[Step 4] Results")
    print("="*70)
    print(f"{'Date':<12} {'Description':<40} {'Amount':<10} {'Category':<20}")
    print("-" * 70)
    
    for tx in categorized_transactions:
        date = tx.get('date', '')
        description = tx.get('description', '')[:37] + "..." if len(tx.get('description', '')) > 40 else tx.get('description', '')
        amount = f"${float(tx.get('amount', 0)):.2f}"
        category = tx.get('category_name', 'Unknown')
        
        print(f"{date:<12} {description:<40} {amount:>9}  {category}")
    
    # Step 5: Show detailed JSON
    print(f"\n[Step 5] Detailed JSON Output (First 3 Transactions)")
    print("="*70)
    
    for i, tx in enumerate(categorized_transactions[:3], 1):
        print(f"\nTransaction {i}:")
        print(json.dumps(tx, indent=2))
    
    # Step 6: Summary
    print(f"\n[Step 6] Categorization Summary")
    print("="*70)
    
    summary = categorizer.get_categorization_summary(categorized_transactions)
    
    print(f"{'Category':<30} {'Count':<8} {'Total':<12}")
    print("-" * 70)
    
    for cat_id in sorted(summary.keys()):
        cat_info = summary[cat_id]
        print(f"{cat_info['name']:<30} {cat_info['count']:<8} ${cat_info['total']:>10.2f}")
    
    total_amount = sum(cat['total'] for cat in summary.values())
    print("-" * 70)
    print(f"{'TOTAL':<30} {len(categorized_transactions):<8} ${total_amount:>10.2f}")
    
    # Step 7: Save categorized output
    print(f"\n[Step 7] Saving Categorized Output...")
    print("-" * 70)
    
    output_file = output_dir / f"categorized_transactions_test_{num_transactions}.json"
    with open(output_file, 'w') as f:
        json.dump(categorized_transactions, f, indent=2)
    
    print(f"✓ Saved to: {output_file}")
    
    print(f"\n{'='*70}")
    print("✓ Test Complete!")
    print(f"{'='*70}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test expense categorization on top N transactions")
    parser.add_argument(
        "-n", "--num",
        type=int,
        default=10,
        help="Number of transactions to test (default: 10)"
    )
    args = parser.parse_args()
    
    test_categorization(args.num)
