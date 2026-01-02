"""
PDF Bank Statement Parser
Extracts transaction details from bank statement PDFs and exports to JSON.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional
import csv
import json
from datetime import datetime
import PyPDF2


class BankStatementParser:
    """
    A flexible parser for extracting transaction data from bank statement PDFs.
    Handles various PDF formats and extracts transaction details.
    """
    
    def __init__(self):
        self.transactions = []
        self.current_card = None  # Card name (e.g., "Gold Card")
        self.current_bank = None  # Bank name (e.g., "American Express")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract all text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from the PDF
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
            
            return text
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {str(e)}")
            return ""
    
    def extract_card_name(self, text: str, pdf_filename: str) -> str:
        """
        Extract card name from PDF text or filename.
        
        Args:
            text: Extracted text from PDF
            pdf_filename: Name of the PDF file
            
        Returns:
            Card name
        """
        # Try to extract card name from the very first line (usually in header)
        first_line = text.split('\n')[0].strip()
        
        # Look for specific patterns for known cards (order matters!)
        card_patterns = [
            r'(American Express[®]?\s+Gold\s+Card)',  # Amex Gold
            r'(Blue Cash Everyday[®]?\s+from\s+American Express)',  # Blue Cash
            r'(American Express[®]?\s+(?:Platinum|Sapphire|Preferred|Reserve|Signature|Elite|Premier)[®]?)',
            r'(Gold|Platinum|Sapphire|Preferred|Reserve|Signature|Elite|Premier)\s+(?:Card|Card®)',
        ]
        
        for pattern in card_patterns:
            match = re.search(pattern, first_line, re.IGNORECASE)
            if match:
                card_name = match.group(1).strip()
                # Clean up extra spaces
                card_name = ' '.join(card_name.split())
                return card_name
        
        # Fallback based on filename
        if 'gold' in pdf_filename.lower():
            return 'American Express® Gold Card'
        elif 'platinum' in pdf_filename.lower():
            return 'American Express® Platinum Card'
        elif 'blue' in pdf_filename.lower():
            return 'Blue Cash Everyday® from American Express'
        
        # Default fallback
        return 'Standard Card'
    
    def extract_bank_name(self, text: str, pdf_filename: str) -> str:
        """
        Extract bank/card issuer name from PDF text or filename.
        
        Args:
            text: Extracted text from PDF
            pdf_filename: Name of the PDF file
            
        Returns:
            Bank/card issuer name
        """
        # Try to extract from text first
        bank_names = [
            'American Express',
            'Chase',
            'Bank of America',
            'Wells Fargo',
            'Citibank',
            'Discover',
            'Capital One',
            'US Bank'
        ]
        
        for bank_name in bank_names:
            if bank_name.lower() in text.lower():
                return bank_name
        
        # Try to infer from filename
        if 'amex' in pdf_filename.lower():
            return 'American Express'
        elif 'chase' in pdf_filename.lower():
            return 'Chase'
        elif 'boa' in pdf_filename.lower():
            return 'Bank of America'
        elif 'wells' in pdf_filename.lower():
            return 'Wells Fargo'
        
        # Default fallback
        return 'Unknown Bank'
    
    def parse_transactions(self, text: str) -> List[Dict[str, str]]:
        """
        Parse transaction details from extracted PDF text.
        Includes both charges and credits (returns/refunds), but excludes payments.
        Specifically optimized for Amex statement format where amounts are on next line.
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        seen_descriptions = set()
        
        lines = text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for lines with dates in Amex format (MM/DD/YY with space after)
            date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+)', line)
            
            if date_match and 'Closing Date' not in line:
                date = date_match.group(1)
                description = date_match.group(2).strip()
                
                # Skip payment lines (THANK YOU, MOBILE PAYMENT, etc.)
                if any(keyword in description.upper() for keyword in ['THANK YOU', 'MOBILE PAYMENT', 'PAYMENT - THANK YOU', 'AUTOPAY']):
                    i += 1
                    continue
                
                # Amount is typically on next line or line after that
                amount = None
                is_credit = False
                lines_to_check = [i + 1, i + 2] if i + 2 < len(lines) else [i + 1] if i + 1 < len(lines) else []
                
                for line_idx in lines_to_check:
                    next_line = lines[line_idx].strip()
                    # Look for various amount patterns:
                    # Pattern 1: +14158799686$21.28⧫ or J6UUVJIW 94103$21.07⧫ or -$53.97
                    # Pattern 2: 8009256278-$2,436.94 (phone number followed by negative amount)
                    
                    # Try pattern 2 first (number-$amount indicates credit)
                    amount_match = re.search(r'\d+-\$([\d,]+\.\d{2})', next_line)
                    if amount_match:
                        is_credit = True
                        amount = amount_match.group(1)
                        break
                    
                    # Try pattern 1
                    amount_match = re.search(r'(-?)\$?([\d,]+\.\d{2})⧫?', next_line)
                    if amount_match:
                        is_credit = amount_match.group(1) == '-'
                        amount = amount_match.group(2)
                        break
                
                # Create transaction if we have date, description, and amount
                if amount and description and len(description) > 2:
                    # Clean description - remove phone numbers and reference codes
                    description = re.sub(r'\+?\d{10,}', '', description)
                    description = re.sub(r'[A-Z0-9]{6,}\s*\d{5}', '', description)
                    description = ' '.join(description.split())
                    
                    if len(description) > 2:
                        key = f"{date}_{description}_{amount}"
                        if key not in seen_descriptions:
                            # For credits, make amount negative
                            final_amount = amount.replace(',', '')
                            if is_credit:
                                final_amount = f"-{final_amount}"
                            
                            transactions.append({
                                'date': date,
                                'description': description,
                                'amount': final_amount,
                                'bank': self.current_bank,
                                'card': self.current_card
                            })
                            seen_descriptions.add(key)
            
            i += 1
        
        return transactions
    
    def _parse_transaction_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        Legacy method - kept for compatibility.
        Main parsing is now done in parse_transactions.
        """
        return None
    
    def export_to_csv(self, transactions: List[Dict[str, str]], output_path: str) -> None:
        """
        Export transactions to a CSV file.
        (Deprecated - kept for backward compatibility)
        
        Args:
            transactions: List of transaction dictionaries
            output_path: Path where CSV file will be saved
        """
        if not transactions:
            print("No transactions to export")
            return
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['date', 'description', 'amount', 'bank', 'card']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for transaction in transactions:
                    writer.writerow({
                        'date': transaction.get('date', ''),
                        'description': transaction.get('description', ''),
                        'amount': transaction.get('amount', ''),
                        'bank': transaction.get('bank', ''),
                        'card': transaction.get('card', '')
                    })
            
            print(f"✓ Exported {len(transactions)} transactions to {output_path}")
        except Exception as e:
            print(f"Error exporting to CSV: {str(e)}")
    
    def export_to_json(self, transactions: List[Dict[str, str]], output_path: str) -> None:
        """
        Export transactions to a JSON file.
        
        Args:
            transactions: List of transaction dictionaries
            output_path: Path where JSON file will be saved
        """
        if not transactions:
            print("No transactions to export")
            return
        
        try:
            with open(output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(transactions, jsonfile, indent=2, ensure_ascii=False)
            
            print(f"✓ Exported {len(transactions)} transactions to {output_path}")
        except Exception as e:
            print(f"Error exporting to JSON: {str(e)}")
    
    def process_pdf(self, pdf_path: str, output_path: str) -> List[Dict[str, str]]:
        """
        Process a PDF file end-to-end: extract text, parse transactions, and export to CSV.
        
        Args:
            pdf_path: Path to input PDF
            output_path: Path for output CSV
            
        Returns:
            List of parsed transactions
        """
        print(f"Processing PDF: {pdf_path}")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            print("Failed to extract text from PDF")
            return []
        
        print(f"Extracted {len(text)} characters from PDF")
        
        # Parse transactions
        transactions = self.parse_transactions(text)
        print(f"Found {len(transactions)} potential transactions")
        
        # Export to CSV
        self.export_to_csv(transactions, output_path)
        
        return transactions


def main():
    """
    Example usage of the PDF parser.
    Processes all PDFs in input folder and combines transactions into a single file.
    """
    parser = BankStatementParser()
    
    # Example: process a PDF from input folder
    input_dir = Path(__file__).parent.parent / "input"
    output_dir = Path(__file__).parent.parent / "output"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Process all PDFs in input folder
    pdf_files = sorted(list(input_dir.glob("*.pdf")))
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return
    
    # Combine all transactions from all PDFs
    all_transactions = []
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        text = parser.extract_text_from_pdf(str(pdf_file))
        
        # Extract bank and card names from PDF
        parser.current_bank = parser.extract_bank_name(text, pdf_file.name)
        parser.current_card = parser.extract_card_name(text, pdf_file.name)
        print(f"  Bank: {parser.current_bank}, Card: {parser.current_card}")
        
        transactions = parser.parse_transactions(text)
        all_transactions.extend(transactions)
        print(f"  Found {len(transactions)} transactions")
    
    # Sort transactions by date (newest first)
    all_transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Export to JSON format only
    json_output = output_dir / "all_transactions.json"
    parser.export_to_json(all_transactions, str(json_output))
    
    print(f"\n{'='*50}")
    print(f"✓ Combined {len(all_transactions)} transactions from {len(pdf_files)} PDFs")
    print(f"✓ JSON saved to: {json_output}")


if __name__ == "__main__":
    main()
