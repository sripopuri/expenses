"""
Bank-Specific Transaction Parsers
Each bank has its own parser class to handle different PDF formats
"""

import re
from typing import List, Dict, Optional
from abc import ABC, abstractmethod


class BaseBankParser(ABC):
    """Base class for bank-specific parsers"""
    
    def __init__(self):
        self.bank_name = "Unknown"
        self.transactions = []
    
    @abstractmethod
    def detect_bank(self, text: str, filename: str) -> bool:
        """
        Detect if this parser can handle the given PDF
        
        Args:
            text: Extracted PDF text
            filename: PDF filename
            
        Returns:
            True if this parser can handle the PDF
        """
        pass
    
    @abstractmethod
    def parse_transactions(self, text: str) -> List[Dict[str, str]]:
        """
        Parse transactions from PDF text
        
        Args:
            text: Extracted PDF text
            
        Returns:
            List of transaction dictionaries
        """
        pass
    
    @abstractmethod
    def extract_card_name(self, text: str, filename: str) -> str:
        """Extract card name from PDF"""
        pass


class AmexParser(BaseBankParser):
    """Parser for American Express statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "American Express"
        self.current_card = None
    
    def detect_bank(self, text: str, filename: str) -> bool:
        """Detect American Express statements"""
        return 'american express' in text.lower() or 'amex' in filename.lower()
    
    def extract_card_name(self, text: str, filename: str) -> str:
        """Extract Amex card name"""
        first_line = text.split('\n')[0].strip()
        
        card_patterns = [
            r'(American Express[®]?\s+Gold\s+Card)',
            r'(Blue Cash Everyday[®]?\s+from\s+American Express)',
            r'(American Express[®]?\s+(?:Platinum|Sapphire|Preferred|Reserve|Signature|Elite|Premier)[®]?)',
        ]
        
        for pattern in card_patterns:
            match = re.search(pattern, first_line, re.IGNORECASE)
            if match:
                return ' '.join(match.group(1).split())
        
        if 'gold' in filename.lower():
            return 'American Express® Gold Card'
        elif 'blue' in filename.lower():
            return 'Blue Cash Everyday® from American Express'
        
        return 'American Express Card'
    
    def parse_transactions(self, text: str) -> List[Dict[str, str]]:
        """Parse Amex transactions - handles two different statement formats"""
        transactions = []
        seen_descriptions = set()
        
        lines = text.split('\n')
        
        # Try Format 1: MM/DD/YY description (amount on next line)
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Amex format 1: MM/DD/YY description
            date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+)', line)
            
            if date_match and 'Closing Date' not in line:
                date = date_match.group(1)
                description = date_match.group(2).strip()
                
                # Skip payments
                if any(keyword in description.upper() for keyword in ['THANK YOU', 'MOBILE PAYMENT', 'PAYMENT - THANK YOU', 'AUTOPAY']):
                    i += 1
                    continue
                
                # Amount is on next line or line after that
                amount = None
                is_credit = False
                lines_to_check = [i + 1, i + 2] if i + 2 < len(lines) else [i + 1] if i + 1 < len(lines) else []
                
                for line_idx in lines_to_check:
                    next_line = lines[line_idx].strip()
                    
                    # Pattern for credits: phonenumber-$amount
                    amount_match = re.search(r'\d+-\$([\d,]+\.\d{2})', next_line)
                    if amount_match:
                        is_credit = True
                        amount = amount_match.group(1)
                        break
                    
                    # Standard pattern
                    amount_match = re.search(r'(-?)\$?([\d,]+\.\d{2})⧫?', next_line)
                    if amount_match:
                        is_credit = amount_match.group(1) == '-'
                        amount = amount_match.group(2)
                        break
                
                if amount and description and len(description) > 2:
                    # Clean description
                    description = re.sub(r'\+?\d{10,}', '', description)
                    description = re.sub(r'[A-Z0-9]{6,}\s*\d{5}', '', description)
                    description = ' '.join(description.split())
                    
                    if len(description) > 2:
                        key = f"{date}_{description}_{amount}"
                        if key not in seen_descriptions:
                            final_amount = amount.replace(',', '')
                            if is_credit:
                                final_amount = f"-{final_amount}"
                            
                            transactions.append({
                                'date': date,
                                'description': description,
                                'amount': final_amount,
                                'bank': self.bank_name,
                                'card': self.current_card
                            })
                            seen_descriptions.add(key)
            
            i += 1
        
        # If few transactions found, try Format 2: amount, then date on next line, then description
        if len(transactions) < 5:
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Look for amount line first: -$XXX.XX or $XXX.XX
                amount_match = re.match(r'^(-?\$[\d,]+\.\d{2})$', line)
                
                if amount_match and i + 1 < len(lines):
                    amount_str = amount_match.group(1)
                    is_credit = amount_str.startswith('-')
                    amount = amount_str.replace('$', '').replace('-', '').replace(',', '')
                    
                    # Check next line for date
                    next_line = lines[i + 1].strip()
                    date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4})$', next_line)
                    
                    if date_match:
                        date = date_match.group(1)
                        
                        # Skip payments
                        if i + 2 < len(lines):
                            check_line = lines[i + 2].strip()
                            if any(keyword in check_line.upper() for keyword in ['THANK YOU', 'MOBILE PAYMENT', 'PAYMENT', 'AUTOPAY']):
                                i += 1
                                continue
                        
                        # Gather description from next few lines
                        description_parts = []
                        for j in range(i + 2, min(i + 10, len(lines))):
                            desc_line = lines[j].strip()
                            
                            # Stop at next amount or date
                            if re.match(r'^-?\$[\d,]+\.\d{2}$', desc_line) or re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', desc_line):
                                break
                            
                            # Skip empty lines and very short lines
                            if desc_line and len(desc_line) > 1 and not desc_line.isdigit():
                                description_parts.append(desc_line)
                            
                            # If we have enough description, stop
                            if len(description_parts) >= 3:
                                break
                        
                        if description_parts:
                            description = ' '.join(description_parts[:5]).strip()
                            
                            # Clean description
                            description = re.sub(r'\+?\d{10,}', '', description)
                            description = ' '.join(description.split())
                            
                            if len(description) > 2:
                                key = f"{date}_{description}_{amount}"
                                if key not in seen_descriptions:
                                    final_amount = f"-{amount}" if is_credit else amount
                                    
                                    transactions.append({
                                        'date': date,
                                        'description': description,
                                        'amount': final_amount,
                                        'bank': self.bank_name,
                                        'card': self.current_card
                                    })
                                    seen_descriptions.add(key)
                
                i += 1
        
        return transactions


class BankOfAmericaParser(BaseBankParser):
    """Parser for Bank of America statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "Bank of America"
        self.current_card = None
    
    def detect_bank(self, text: str, filename: str) -> bool:
        """Detect Bank of America statements"""
        return 'bank of america' in text.lower() or 'bofa' in filename.lower() or 'bankofamerica' in text.lower()
    
    def extract_card_name(self, text: str, filename: str) -> str:
        """Extract BofA card name"""
        # Look for card type in first 1000 characters
        header = text[:1000]
        
        if 'Visa Signature' in header:
            return 'Bank of America Visa Signature'
        elif 'Cash Rewards' in header:
            return 'Bank of America Cash Rewards'
        elif 'Travel Rewards' in header:
            return 'Bank of America Travel Rewards'
        elif 'Customized Cash Rewards' in header:
            return 'Bank of America Customized Cash Rewards'
        
        return 'Bank of America Credit Card'
    
    def parse_transactions(self, text: str) -> List[Dict[str, str]]:
        """
        Parse Bank of America transactions
        
        Format: MM/DD MM/DD DESCRIPTION CITY STATE REFNUM ACCOUNT AMOUNT
        Example: 08/28 08/30 SUNGLASS HUT 5167 ROGERS AR 9098 2361 215.72
        """
        transactions = []
        seen_descriptions = set()
        
        lines = text.split('\n')
        
        # Extract statement closing date to infer year for transactions
        statement_year = None
        statement_month = None
        for line in lines:
            # Look for patterns like "August 21 - September 20, 2025" or "Statement Closing Date 09/20/2025"
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
            if date_match and 'Closing Date' in line:
                closing_date = date_match.group(1)
                month, day, year = closing_date.split('/')
                statement_year = year
                statement_month = int(month)
                break
            # Alternative format: "August 21 - September 20, 2025"
            date_match = re.search(r'(\w+)\s+\d+\s*-\s*(\w+)\s+\d+,\s*(\d{4})', line)
            if date_match:
                end_month_name = date_match.group(2)
                statement_year = date_match.group(3)
                month_map = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                           'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}
                statement_month = month_map.get(end_month_name)
                break
        
        if not statement_year:
            statement_year = "2025"  # Default fallback
            statement_month = 12
        
        # Find where transactions start (after "Purchases and Adjustments" without a dollar amount)
        transaction_start = -1
        for i, line in enumerate(lines):
            # Look for "Purchases and Adjustments" that is NOT followed by a dollar amount
            if 'Purchases and Adjustments' in line and not re.search(r'\$[\d,]+\.[\d]{2}', line):
                transaction_start = i + 1
                break
        
        if transaction_start == -1:
            return transactions
        
        for i in range(transaction_start, len(lines)):
            line = lines[i].strip()
            
            # Stop at next section
            if any(keyword in line for keyword in ['TOTAL PURCHASES', 'Interest Charged', 'Fees Charged', 'Page ']):
                break
            
            # BofA format: MM/DD MM/DD DESCRIPTION ... AMOUNT
            # Pattern: date date description city state refnum account amount
            match = re.match(r'^(\d{2}/\d{2})\s+(\d{2}/\d{2})\s+(.+?)\s+([\d.]+)$', line)
            
            if match:
                transaction_date = match.group(1)
                posting_date = match.group(2)
                description_and_amount = match.group(3)
                amount = match.group(4)
                
                # Add year to transaction date
                # If transaction month is after statement month, it's from previous year
                trans_month = int(transaction_date.split('/')[0])
                trans_year = statement_year
                if trans_month > statement_month:
                    trans_year = str(int(statement_year) - 1)
                
                full_date = f"{transaction_date}/{trans_year}"
                
                # Extract description (everything before the last numeric parts)
                # The format is: DESCRIPTION CITY STATE REFNUM ACCOUNT
                parts = description_and_amount.split()
                
                # Last 2 parts are typically reference number and account number
                # State is usually 2 letters
                # Work backwards to find description
                description_parts = []
                state_found = False
                
                for j, part in enumerate(parts):
                    # If we find a 2-letter state code, include everything before it
                    if len(part) == 2 and part.isupper() and not state_found:
                        description_parts = parts[:j-1]  # Exclude city and state
                        state_found = True
                        break
                
                if not description_parts:
                    # Fallback: take first few parts
                    description_parts = parts[:min(4, len(parts))]
                
                description = ' '.join(description_parts).strip()
                
                if description and amount:
                    # Check if it's a credit (look for CR or negative indicators)
                    is_credit = False
                    if 'CR' in line or line.endswith('-'):
                        is_credit = True
                        amount = amount.replace('-', '')
                    
                    final_amount = amount.replace(',', '')
                    if is_credit:
                        final_amount = f"-{final_amount}"
                    
                    key = f"{full_date}_{description}_{amount}"
                    if key not in seen_descriptions:
                        transactions.append({
                            'date': full_date,
                            'description': description,
                            'amount': final_amount,
                            'bank': self.bank_name,
                            'card': self.current_card
                        })
                        seen_descriptions.add(key)
        
        return transactions


class BankParserFactory:
    """Factory to detect and return the appropriate bank parser"""
    
    # Register all available parsers
    PARSERS = [
        AmexParser,
        BankOfAmericaParser,
    ]
    
    @classmethod
    def get_parser(cls, text: str, filename: str) -> Optional[BaseBankParser]:
        """
        Detect and return the appropriate parser for the PDF
        
        Args:
            text: Extracted PDF text
            filename: PDF filename
            
        Returns:
            Appropriate parser instance or None if no match
        """
        for parser_class in cls.PARSERS:
            parser = parser_class()
            if parser.detect_bank(text, filename):
                return parser
        
        # Default to Amex if can't detect
        return AmexParser()
