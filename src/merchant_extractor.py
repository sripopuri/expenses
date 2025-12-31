"""
Merchant Name Extractor
Cleans and standardizes merchant names from transaction descriptions
"""

import re
from typing import Optional


class MerchantExtractor:
    """
    Extracts clean merchant names from transaction descriptions.
    Handles various formats and removes noise like reference codes, phone numbers, etc.
    """
    
    # Common merchant patterns and their clean names
    MERCHANT_PATTERNS = {
        r'(?:UBER|UberXL|UBER EATS)': 'Uber',
        r'(?:NETFLIX|NETFLIX\.COM)': 'Netflix',
        r'(?:DISNEY|DISNEYPLUS)': 'Disney+',
        r'(?:AMAZON|AMZN)': 'Amazon',
        r'(?:WAL-?MART|WALMART)': 'Walmart',
        r'(?:CVS|CVS/PHARMACY)': 'CVS Pharmacy',
        r'(?:WHOLE FOODS|WHOLEFOODS)': 'Whole Foods',
        r'(?:TARGET|TGT)': 'Target',
        r'(?:COSTCO|COSTCO WHOLESALE)': 'Costco',
        r'(?:BEST BUY|BESTBUY)': 'Best Buy',
        r'(?:HOME DEPOT|HOMEDEPOT)': 'Home Depot',
        r'(?:LOWES|LOWE\'?S)': 'Lowes',
        r'(?:CHIPOTLE|CHIPOLTE)': 'Chipotle',
        r'(?:STARBUCKS|SBUX)': 'Starbucks',
        r'(?:MCDONALDS|MCDONALD\'?S|MCDONALDs)': 'McDonalds',
        r'(?:CHICK-?FIL-?A|CHICKFILA)': 'Chick-fil-A',
        r'(?:PANERA|PANERA BREAD)': 'Panera',
        r'(?:TACO BELL|TACOBELL)': 'Taco Bell',
        r'(?:STARBUCKS)': 'Starbucks',
        r'(?:OPENAI|CHATGPT)': 'OpenAI',
        r'(?:GOOGLE|GOOGLE PLAY)': 'Google',
        r'(?:APPLE|ITUNES|APP STORE)': 'Apple',
        r'(?:MICROSOFT|XBOX)': 'Microsoft',
        r'(?:SPOTIFY)': 'Spotify',
        r'(?:HULU)': 'Hulu',
        r'(?:MAX|HBO)': 'Max/HBO',
        r'(?:YELLOW CAB|YELLOW TAXI)': 'Yellow Cab',
        r'(?:LYFT)': 'Lyft',
        r'(?:AIRBNB|AIR BNB)': 'Airbnb',
        r'(?:HOTEL|INN|RESORT)': 'Hotel',
        r'(?:AIRLINE|DELTA|UNITED|AMERICAN|SOUTHWEST)': 'Airline',
        r'(?:SHELL|EXXON|CHEVRON|MOBIL)': 'Gas Station',
        r'(?:CVS|WALGREENS|RITE AID|PHARMACY)': 'Pharmacy',
        r'(?:WHOLE FOODS|KROGER|SAFEWAY|TRADER JOES|SPROUTS)': 'Grocery',
    }
    
    @staticmethod
    def extract_merchant(description: str) -> str:
        """
        Extract and clean merchant name from transaction description
        
        Args:
            description: Raw transaction description
        
        Returns:
            Clean merchant name
        """
        if not description:
            return "Unknown"
        
        # First, try pattern matching for known merchants
        for pattern, merchant_name in MerchantExtractor.MERCHANT_PATTERNS.items():
            if re.search(pattern, description, re.IGNORECASE):
                return merchant_name
        
        # If no pattern matches, extract the first meaningful part
        merchant = MerchantExtractor._extract_from_description(description)
        return merchant if merchant else "Unknown"
    
    @staticmethod
    def _extract_from_description(description: str) -> Optional[str]:
        """
        Extract merchant name from description using heuristics
        
        Args:
            description: Raw transaction description
        
        Returns:
            Extracted merchant name or None
        """
        # Remove common prefixes like "AplPay", "Apply", etc.
        cleaned = re.sub(r'^(?:AplPay|Apply|Apay|PAY\*|TST\*|POS\*)\s+', '', description, flags=re.IGNORECASE)
        
        # Remove reference codes and locations at the end (like "00-", "000011015", "214-2913000 TX")
        # Keep the main merchant name part
        cleaned = re.sub(r'\s+\d{2,}[-\s]*\w{2}\s*$', '', cleaned)  # Remove things like "00- PLANO TX"
        cleaned = re.sub(r'\s+\d{9,}.*$', '', cleaned)  # Remove long reference numbers
        
        # Try to get multi-word merchant names for common types
        # Medical facilities: capture name before numbers/codes
        medical_match = re.match(r'^([A-Z][A-Z\s&/]+?)(?:\s+\d+|-|00|$)', cleaned)
        if medical_match:
            name = medical_match.group(1).strip()
            if len(name) > 3:
                return name
        
        # General fallback: split by common separators and get first few meaningful words
        parts = re.split(r'[\s#\-\*]', cleaned)
        
        # Collect meaningful parts (skip short, empty, or numeric parts)
        merchant_parts = []
        for part in parts:
            if part and len(part) > 2 and not part.isdigit() and not re.match(r'^[A-Z]{2}$', part):
                merchant_parts.append(part)
                if len(merchant_parts) >= 2:  # Get up to 2 words for better names
                    break
        
        if merchant_parts:
            return ' '.join(merchant_parts)
        
        # If nothing worked, return first word
        first_word = parts[0] if parts else None
        return first_word if first_word and len(first_word) > 2 else None
    
    @staticmethod
    def get_merchant_category(merchant_name: str) -> Optional[str]:
        """
        Infer category hint based on merchant name
        Useful for validation or debugging
        
        Args:
            merchant_name: Clean merchant name
        
        Returns:
            Suggested category or None
        """
        merchant_lower = merchant_name.lower()
        
        if any(x in merchant_lower for x in ['uber', 'lyft', 'taxi', 'parking', 'gas']):
            return 'transportation'
        elif any(x in merchant_lower for x in ['netflix', 'hulu', 'disney', 'spotify', 'openai']):
            return 'lifestyle'
        elif any(x in merchant_lower for x in ['walmart', 'amazon', 'target', 'costco']):
            return 'shopping'
        elif any(x in merchant_lower for x in ['restaurant', 'cafe', 'starbucks', 'chipotle', 'mcdonalds']):
            return 'food'
        elif any(x in merchant_lower for x in ['cvs', 'pharmacy', 'walgreens', 'hospital', 'doctor']):
            return 'health'
        elif any(x in merchant_lower for x in ['hotel', 'airbnb', 'airline', 'flight']):
            return 'travel'
        
        return None


def test_merchant_extraction():
    """Test the merchant extractor with sample descriptions"""
    test_descriptions = [
        "UBER EATS help.uber.com CA",
        "AplPay BEST BUY 002568 FARMERS BRANC TX",
        "NETFLIX.COM 866-579-7172 CA",
        "WALMART NEIGHBORHOOD MARKET 4686 BENTONVILLE AR",
        "OPENAI *CHATGPT SUBSCR SAN FRANCISCO CA",
        "TST* RAMEN NARA 00120655 ROGERS AR",
        "AplPay CVS/PHARMACY #11015 000011015 DALLAS TX",
        "BAYLOR SURGICARE AT PLA 214-2913000 TX",
        "Uber Trip help.uber.com CA",
        "DISNEY STREAMING 888-905-7888 CA"
    ]
    
    print("Merchant Extraction Test")
    print("=" * 80)
    print(f"{'Description':<50} {'Merchant':<25}")
    print("-" * 80)
    
    for desc in test_descriptions:
        merchant = MerchantExtractor.extract_merchant(desc)
        print(f"{desc:<50} {merchant:<25}")


if __name__ == "__main__":
    test_merchant_extraction()
