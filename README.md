# Bank Statement Expense Categorizer

A tool to parse bank statement PDFs, extract transaction details, and categorize expenses.

## Project Structure

```
expenses/
├── input/              # Place your bank statement PDFs here
├── output/             # Generated CSV files with transactions
├── src/                # Source code
│   └── pdf_parser.py   # PDF parsing logic
├── config/             # Configuration files (for custom parsing rules)
├── requirements.txt    # Python dependencies
└── README.md
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Place your bank statement PDF files in the `input/` folder

3. Run the parser:
   ```bash
   python src/pdf_parser.py
   ```

The parser will extract transaction details and save them as CSV files in the `output/` folder.

## How It Works

1. **PDF Extraction**: Reads PDF files and extracts text
2. **Transaction Parsing**: Identifies and extracts transaction records (date, description, amount)
3. **CSV Export**: Saves clean transaction data to CSV format

## Privacy & Security

- Only transaction details (date, description, amount) are extracted
- Sensitive banking information and headers are automatically filtered
- Output files contain only essential transaction data for categorization

## Next Steps

Once transactions are extracted to CSV:
1. Review and clean the CSV data
2. Create categorization rules for your expenses
3. Implement expense bucketing logic
