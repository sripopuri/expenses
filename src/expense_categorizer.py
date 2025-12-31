"""
Expense Categorizer using Local LLM
Categorizes transactions using LM Studio local LLM based on merchant descriptions
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from lm_studio_client import LMStudioClient, Message


class ExpenseCategorizer:
    """
    Categorizes expenses using a local LLM model.
    Reads category definitions and uses them to categorize transactions.
    """
    
    def __init__(self, lm_client: Optional[LMStudioClient] = None):
        """
        Initialize the expense categorizer
        
        Args:
            lm_client: LMStudioClient instance. If None, creates a new one.
        """
        self.client = lm_client or LMStudioClient()
        self.categories = self._load_categories()
        self.prompt_config = self._load_prompt_config()
        self.category_map = {cat['id']: cat['name'] for cat in self.categories}
    
    def _load_categories(self) -> List[Dict]:
        """Load category definitions from JSON file"""
        config_file = Path(__file__).parent.parent / "config" / "category_definitions.json"
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
                return data.get('categories', [])
        except FileNotFoundError:
            print(f"Error: Category definitions file not found at {config_file}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse category definitions: {e}")
            return []
    
    def _load_prompt_config(self) -> Dict:
        """Load categorization prompt configuration from JSON file"""
        config_file = Path(__file__).parent.parent / "config" / "categorization_prompt.json"
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Prompt config file not found at {config_file}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse prompt config: {e}")
            return {}
    
    def _build_categorization_prompt(self, transaction_description: str) -> str:
        """
        Build the prompt for categorizing a single transaction
        
        Args:
            transaction_description: The merchant name/description of the transaction
        
        Returns:
            Formatted prompt string
        """
        # Format categories for the prompt
        categories_text = "\n".join([
            f"- {cat['id']}: {cat['name']} - {cat['description']}"
            for cat in self.categories
        ])
        
        prompt = f"""Categorize this transaction:

Transaction: {transaction_description}

Available categories:
{categories_text}

Rules:
{chr(10).join([f"- {rule}" for rule in self.prompt_config.get('categorization_guidelines', [])])}

Respond with ONLY the category ID (e.g., 'food', 'transportation', 'other'), nothing else."""
        
        return prompt
    
    def categorize_transaction(self, transaction_description: str) -> Optional[str]:
        """
        Categorize a single transaction using the LLM
        
        Args:
            transaction_description: Merchant name/description
        
        Returns:
            Category ID (string), or None if categorization fails
        """
        if not self.client.model:
            print("Error: No LLM model loaded. Cannot categorize.")
            return None
        
        try:
            # Build the prompt
            system_prompt = self.prompt_config.get('categorization_system_prompt', 
                                                   'You are a financial categorizer.')
            user_prompt = self._build_categorization_prompt(transaction_description)
            
            # Send to LLM
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt)
            ]
            
            response = self.client.chat_completion(messages, temperature=0.3, max_tokens=50)
            
            # Extract and clean the response
            category_id = self.client.extract_response_text(response).strip().lower()
            
            # Validate category ID
            valid_ids = {cat['id'] for cat in self.categories}
            if category_id not in valid_ids:
                print(f"Warning: Invalid category returned '{category_id}' for '{transaction_description}', using 'other'")
                return 'other'
            
            return category_id
        
        except Exception as e:
            print(f"Error categorizing transaction '{transaction_description}': {e}")
            return None
    
    def categorize_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """
        Categorize a list of transactions
        
        Args:
            transactions: List of transaction dictionaries
        
        Returns:
            List of transactions with added 'category' field
        """
        if not self.client.model:
            print("Error: No LLM model loaded. Cannot categorize.")
            return transactions
        
        categorized = []
        total = len(transactions)
        
        for i, transaction in enumerate(transactions, 1):
            # Get the description
            description = transaction.get('description', '')
            
            # Categorize
            category_id = self.categorize_transaction(description)
            
            # Add category to transaction
            transaction['category'] = category_id or 'other'
            transaction['category_name'] = self.category_map.get(category_id, 'Other')
            
            categorized.append(transaction)
            
            # Progress indicator
            if i % 10 == 0 or i == total:
                print(f"  Categorized {i}/{total} transactions")
        
        return categorized
    
    def get_categorization_summary(self, transactions: List[Dict]) -> Dict[str, Dict]:
        """
        Generate a summary of spending by category
        
        Args:
            transactions: List of categorized transactions
        
        Returns:
            Dictionary with category summaries
        """
        summary = {}
        
        for transaction in transactions:
            category = transaction.get('category', 'other')
            category_name = transaction.get('category_name', 'Other')
            amount = float(transaction.get('amount', 0))
            
            if category not in summary:
                summary[category] = {
                    'name': category_name,
                    'count': 0,
                    'total': 0.0
                }
            
            summary[category]['count'] += 1
            summary[category]['total'] += amount
        
        return summary


def main():
    """Example usage of the expense categorizer"""
    # Initialize client
    client = LMStudioClient()
    
    # Get and set model
    models = client.get_available_models()
    if not models:
        print("No models available. Make sure LM Studio is running.")
        return
    
    model_id = models[0].get('id')
    client.set_model(model_id)
    
    # Initialize categorizer
    categorizer = ExpenseCategorizer(client)
    
    # Test with sample transactions
    sample_descriptions = [
        "UBER EATS help.uber.com CA",
        "NETFLIX.COM 866-579-7172 CA",
        "WALMART NEIGHBORHOOD MARKET 4686 BENTONVILLE AR",
        "OPENAI *CHATGPT SUBSCR SAN FRANCISCO CA",
        "WAL-MART FUEL 3482 PLANO TX"
    ]
    
    print("\n--- Testing Expense Categorization ---")
    for desc in sample_descriptions:
        category = categorizer.categorize_transaction(desc)
        category_name = categorizer.category_map.get(category, 'Unknown')
        print(f"{desc:50} -> {category_name}")


if __name__ == "__main__":
    main()
