# Bank Statement Expense Categorizer

A tool to parse bank statement PDFs, extract transaction details, categorize expenses using local LLM, and analyze spending patterns with an interactive Streamlit dashboard.

## Project Structure

```
expenses/
├── input/              # Place your bank statement PDFs here
├── output/             # Generated JSON and CSV files with categorized transactions
├── src/                # Source code
│   ├── pdf_parser.py   # PDF parsing logic
│   ├── lm_studio_client.py  # Local LLM API client
│   ├── expense_categorizer.py  # LLM-based expense categorizer
│   ├── merchant_extractor.py  # Clean merchant name extraction
│   ├── process_expenses.py  # Main processing pipeline
│   └── test_categorization.py  # Test script for limited datasets
├── config/             # Configuration files
│   ├── category_definitions.json  # Category definitions
│   └── categorization_prompt.json  # LLM prompt configuration
├── dashboard.py        # Streamlit interactive dashboard
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
2. Load a model (recommended: Qwen 3-4B or similar)
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
4. Extract clean merchant names
5. Generate a summary report
6. Save categorized transactions to `output/all_transactions_categorized.json`

### Parse Only (Without Categorization)

```bash
python src/process_expenses.py --no-categorize
```

### Test Categorization on Limited Dataset

```bash
python src/test_categorization.py -n 10
```

This will test on the first N transactions and save results to `output/categorized_transactions_test_N.json`.

### Launch Interactive Dashboard

```bash
streamlit run dashboard.py
```

This opens an interactive dashboard at http://localhost:8501 with:
- **Category spending overview** - Bar chart of total spending by category
- **Merchant analysis** - Scatter plot showing merchant frequency vs spending
- **Category drill-down** - Click a category to see merchants and individual transactions
- **Spending summary tables** - Detailed breakdowns by category and merchant

## How It Works

### 1. PDF Parsing

- Extracts text from bank statement PDFs
- Identifies transaction details: date, merchant, amount
- Detects bank and card name
- Combines multiple statements into a single dataset

### 2. Merchant Name Extraction

- Uses pattern matching for 25+ known merchants (Netflix, Walmart, Uber, etc.)
- Heuristic extraction for unknown merchants
- Removes reference codes, phone numbers, and location codes
- Produces clean, standardized merchant names

### 3. LLM-Based Categorization

- Sends merchant descriptions to a local LLM
- Uses category definitions to guide categorization
- Applies consistent rules across all transactions
- Adds `category` and `category_name` fields to each transaction

### 4. Dashboard Visualization

- Interactive category spending breakdown
- Merchant frequency analysis with scatter plot
- Median transaction values for each merchant
- Category-filtered views for deep analysis
- Export-ready data

### 5. Output Format

Each transaction includes:

```json
{
  "date": "12/31/24",
  "description": "NETFLIX.COM 866-579-7172 CA",
  "amount": "7.57",
  "bank": "American Express",
  "card": "Blue Cash Everyday® from American Express",
  "merchant": "Netflix",
  "category": "lifestyle",
  "category_name": "Lifestyle & Digital"
}
```

## Categories

The system now categorizes expenses into:

- **Housing** - Rent, mortgage, property maintenance
- **Utilities & Connectivity** - Internet, phone, utilities
- **Groceries** - Supermarket groceries, household supplies, general merchandise
- **Food & Restaurants** - Restaurants, cafes, takeout, food delivery
- **Transportation** - Rideshares, gas, parking, transit
- **Health & Wellness** - Medical, dental, therapy
- **Personal Care & Fitness** - Gym, haircut, skincare
- **Shopping** - Clothing, accessories, electronics, lifestyle shopping
- **Subscriptions** - Netflix, Hulu, apps, software, music subscriptions
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

### Merchant Patterns

Edit the `MERCHANT_PATTERNS` dictionary in `src/merchant_extractor.py` to:
- Add patterns for new merchants
- Customize merchant name mappings
- Improve extraction for specific formats

## Features

✅ PDF text extraction from multiple bank statement formats
✅ Automatic transaction parsing with amount and date detection
✅ Bank and card type identification
✅ Clean merchant name extraction with 25+ patterns
✅ LLM-based intelligent categorization
✅ Interactive Streamlit dashboard
✅ Spending summary by category and merchant
✅ Scatter plot analysis of spending patterns
✅ JSON output format with all transaction details
✅ CSV export for spreadsheet analysis
✅ Extensible and modular architecture

## Requirements

- Python 3.8+
- PyPDF2 3.0.1 - PDF text extraction
- Pandas 2.0+ - Data handling
- Streamlit - Interactive dashboard
- Plotly - Data visualization
- Requests 2.31.0 - LLM API communication

See `requirements.txt` for complete dependency list.

## Example Analysis

With 910 transactions from multiple bank statements:

| Category | Transactions | Total Spending |
|----------|--------------|----------------|
| Shopping & Household | 594 | $14,986.11 |
| Health & Wellness | 20 | $3,040.90 |
| Lifestyle & Digital | 80 | $1,911.96 |
| Food | 92 | $1,737.45 |
| Other | 54 | $1,821.90 |
| Transportation | 55 | $1,106.27 |
| Travel & Occasions | 8 | $407.62 |
| Personal Care & Fitness | 6 | $241.17 |
| Utilities & Connectivity | 1 | $7.73 |

## License

MIT
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

