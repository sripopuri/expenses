"""
Apply Merchant Category Corrections
Reads corrected categorizations from Excel and re-runs categorization with overrides
"""

import json
import pandas as pd
from pathlib import Path
from expense_categorizer import ExpenseCategorizer
from lm_studio_client import LMStudioClient


def extract_merchant_overrides_from_excel(excel_path: str, output_path: str):
    """
    Extract merchant corrections from Excel file and save as JSON overrides
    
    Args:
        excel_path: Path to the Excel file with corrections
        output_path: Path to save the merchant overrides JSON
    """
    print(f"Reading corrections from {excel_path}")
    df = pd.read_excel(excel_path)
    
    # Filter for rows with corrections
    corrections = df[df['corrected_category'].notna() & (df['corrected_category'] != '')]
    print(f"Found {len(corrections)} merchant corrections")
    
    # Load category definitions to map names to IDs
    config_dir = Path(__file__).parent.parent / "config"
    with open(config_dir / "category_definitions.json", 'r') as f:
        category_defs = json.load(f)
    
    # Create name-to-id mapping
    category_name_to_id = {cat['name']: cat['id'] for cat in category_defs['categories']}
    
    # Create merchant overrides dictionary
    merchant_overrides = {}
    for _, row in corrections.iterrows():
        merchant = row['merchant']
        corrected_category_name = row['corrected_category']
        
        category_id = category_name_to_id.get(corrected_category_name)
        
        if category_id:
            merchant_overrides[merchant] = {
                'category_id': category_id,
                'category_name': corrected_category_name
            }
    
    # Save to config file
    with open(output_path, 'w') as f:
        json.dump(merchant_overrides, f, indent=2)
    
    print(f"✓ Created {output_path} with {len(merchant_overrides)} merchant overrides")
    return merchant_overrides


def recategorize_transactions():
    """
    Re-run categorization on all transactions using the updated overrides
    """
    print("\n--- Re-categorizing All Transactions with Overrides ---\n")
    
    # Paths
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "output" / "all_transactions_parsed.json"
    output_json = base_dir / "output" / "all_transactions_categorized.json"
    output_csv = base_dir / "output" / "all_transactions_categorized.csv"
    
    # Load transactions
    print(f"Loading transactions from {input_file}")
    with open(input_file, 'r') as f:
        transactions = json.load(f)
    print(f"Loaded {len(transactions)} transactions")
    
    # Initialize LM Studio client
    print("\nConnecting to LM Studio...")
    client = LMStudioClient()
    
    # Get available models
    models = client.get_available_models()
    if not models:
        print("Error: No models available in LM Studio")
        return
    
    # Use the first available model
    model_id = models[0].get('id')
    print(f"Using model: {model_id}")
    client.set_model(model_id)
    
    # Initialize categorizer (will load merchant overrides automatically)
    categorizer = ExpenseCategorizer(client)
    print(f"Loaded {len(categorizer.merchant_overrides)} merchant overrides")
    
    # Categorize transactions
    print("\nCategorizing transactions...")
    categorized = categorizer.categorize_transactions(transactions)
    
    # Save to JSON
    print(f"\nSaving categorized transactions to {output_json}")
    with open(output_json, 'w') as f:
        json.dump(categorized, f, indent=2)
    
    # Convert to CSV for dashboard
    print(f"Converting to CSV: {output_csv}")
    df = pd.DataFrame(categorized)
    df.to_csv(output_csv, index=False)
    
    # Generate summary
    summary = categorizer.get_categorization_summary(categorized)
    
    print("\n" + "="*60)
    print("CATEGORIZATION SUMMARY")
    print("="*60)
    
    for category_id, stats in sorted(summary.items(), key=lambda x: x[1]['total'], reverse=True):
        print(f"{stats['name']:25} ${stats['total']:>10,.2f} ({stats['count']:>4} transactions)")
    
    print("="*60)
    print(f"{'TOTAL':25} ${sum(s['total'] for s in summary.values()):>10,.2f} ({sum(s['count'] for s in summary.values()):>4} transactions)")
    print("="*60)
    
    print(f"\n✓ Categorization complete!")
    print(f"✓ Output saved to {output_json}")
    print(f"✓ CSV saved to {output_csv}")


def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent
    
    # Step 1: Extract overrides from Excel
    excel_file = base_dir / "input" / "corrected_categorizations" / "merchant_category_corrections.xlsx"
    overrides_file = base_dir / "config" / "merchant_category_overrides.json"
    
    if excel_file.exists():
        extract_merchant_overrides_from_excel(str(excel_file), str(overrides_file))
    else:
        print(f"Excel file not found: {excel_file}")
        print("Skipping override extraction, using existing overrides file if present")
    
    # Step 2: Re-categorize all transactions
    recategorize_transactions()


if __name__ == "__main__":
    main()
