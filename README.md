# Bank Statement Expense Categorizer

A tool to parse bank statement PDFs, extract transaction details, categorize expenses using local LLM, and analyze spending patterns.

## Project Structure

```
expenses/
├── input/              # Place your bank statement PDFs here
├── output/             # Generated JSON files with categorized transactions
├── src/                # Source code
│   ├── pdf_parser.py   # PDF parsing logic
│   ├── lm_studio_client.py  # Local LLM API client
│   ├── expense_categorizer.py  # LLM-based expense categorizer
│   └── process_expenses.py  # Main processing pipeline
├── config/             # Configuration files
│   ├── category_definitions.json  # Category definitions
│   └── categorization_prompt.json  # LLM prompt configuration
├── requirements.txt    # Python dependencies
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Local LLM Setup

This project uses a local LLM via [LM Studio](https://lmstudio.ai/):

1. Download and install LM Studio
2. Load a model (recommended: Mistral 7B or similar)
3. Start the local API server (default: http://127.0.0.1:1234)

### 3. Add Bank Statements

Place your bank statement PDF files in the `input/` folder.

## Usage

### Parse and Categorize Expenses

```bash
python src/process_expenses.py
```

This will:
1. Parse all PDFs in the `input/` folder
2. Extract transaction details
3. Categorize each transaction using the local LLM
4. Generate a summary report
5. Save categorized transactions to `output/all_transactions.json`

### Parse Only (Without Categorization)

```bash
python src/process_expenses.py --no-categorize
```

### Parse Using Original Script

```bash
python src/pdf_parser.py
```

## How It Works

### 1. PDF Parsing

- Extracts text from bank statement PDFs
- Identifies transaction details: date, merchant, amount
- Detects bank and card name
- Combines multiple statements into a single dataset

### 2. LLM-Based Categorization

- Sends merchant descriptions to a local LLM
- Uses category definitions to guide categorization
- Applies consistent rules across all transactions
- Adds `category` and `category_name` fields to each transaction

### 3. Output Format

Each transaction includes:

```json
{
  "date": "12/08/25",
  "description": "UBER EATS help.uber.com CA",
  "amount": "14.47",
  "bank": "American Express",
  "card": "American Express® Gold Card",
  "category": "food",
  "category_name": "Food"
}
```

## Categories

The system categorizes expenses into:

- **Housing** - Rent, mortgage, property maintenance
- **Utilities & Connectivity** - Internet, phone, utilities
- **Food** - Groceries, restaurants, delivery
- **Transportation** - Rideshares, gas, parking, transit
- **Health & Wellness** - Medical, dental, therapy
- **Personal Care & Fitness** - Gym, haircut, skincare
- **Shopping & Household** - Clothing, electronics, home goods
- **Lifestyle & Digital** - Streaming, apps, subscriptions
- **Travel & Occasions** - Flights, hotels, vacations
- **Financial & Future** - Loans, taxes, investments, donations
- **Other** - Unclassified expenses

## Privacy & Security

- Only transaction details (date, description, amount) are extracted
- Sensitive banking information and headers are filtered
- Local LLM ensures data stays on your machine
- No transactions are sent to external services

## Configuration

### Category Definitions

Edit `config/category_definitions.json` to modify categories, descriptions, and examples.

### Categorization Prompts

Edit `config/categorization_prompt.json` to adjust:
- System prompt
- Guidelines for categorization
- Category selection rules

## Features

✅ PDF text extraction
✅ Automatic transaction parsing
✅ Bank and card detection
✅ LLM-based intelligent categorization
✅ Spending summary by category
✅ JSON output format
✅ Extensible architecture

## Requirements

- Python 3.8+
- PyPDF2 - PDF processing
- Requests - HTTP client
- Local LM Studio running with a loaded model

## Example Output

```json
[
  {
    "date": "12/08/25",
    "description": "UBER EATS help.uber.com CA",
    "amount": "14.47",
    "bank": "American Express",
    "card": "American Express® Gold Card",
    "category": "food",
    "category_name": "Food"
  },
  {
    "date": "12/08/25",
    "description": "Uber Trip help.uber.com CA",
    "amount": "10.92",
    "bank": "American Express",
    "card": "American Express® Gold Card",
    "category": "transportation",
    "category_name": "Transportation"
  }
]
```

## Troubleshooting

### "Cannot connect to LM Studio API"

- Ensure LM Studio is running
- Check that the API server is started (http://127.0.0.1:1234)
- Verify no firewall is blocking the connection

### "No models available"

- Load a model in LM Studio before running the script
- Ensure the model is fully loaded

### PDF parsing issues

- Ensure PDFs are from your bank (layout may vary)
- Check that bank statement PDFs are readable text (not scanned images)

