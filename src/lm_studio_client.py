"""
LM Studio API Client
A Python module to interact with locally hosted LLM via LM Studio API
"""

import requests
import json
import re
import argparse
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a chat message"""
    role: str  # "user", "assistant", "system"
    content: str


def load_system_prompt() -> str:
    """Load and construct the system prompt from prompts.json file"""
    prompts_file = os.path.join(os.path.dirname(__file__), "prompts.json")
    try:
        with open(prompts_file, 'r') as f:
            prompts = json.load(f)
            base_prompt = prompts.get("system_prompt", "You are a helpful assistant.")
            
            # Build personality section
            personality = prompts.get("personality", [])
            personality_text = "\n".join([f"- {p}" for p in personality])
            
            # Build guidelines section
            guidelines = prompts.get("response_guidelines", [])
            guidelines_text = "\n".join([f"{i+1}. {g}" for i, g in enumerate(guidelines)])
            
            # Combine all sections
            full_prompt = f"{base_prompt}\n\nPersonality:\n{personality_text}\n\nResponse Guidelines:\n{guidelines_text}"
            return full_prompt
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load prompts.json: {e}")
        return "You are a helpful assistant."


class LMStudioClient:
    """Client for interacting with LM Studio locally hosted LLM"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:1234"):
        """
        Initialize the LM Studio client
        
        Args:
            base_url: The base URL of the LM Studio API (default: http://127.0.0.1:1234)
        """
        self.base_url = base_url
        self.model = None
        self._verify_connection()
    
    def _verify_connection(self) -> bool:
        """Verify that the LM Studio API is reachable"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            response.raise_for_status()
            print("✓ Connected to LM Studio API")
            return True
        except requests.exceptions.ConnectionError:
            print("✗ Cannot connect to LM Studio API. Make sure LM Studio is running.")
            return False
        except Exception as e:
            print(f"✗ Error connecting to LM Studio API: {e}")
            return False

    def _sanitize_text(self, text: str) -> str:
        """
        Remove model "thinking" sections (e.g. <think>...</think>) from output.

        This keeps only the user-facing content.
        """
        if not text:
            return text

        # Remove any <think>...</think> blocks (multiline)
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I)

        # Remove any stray <think/> or closing tags
        cleaned = re.sub(r"</?think\s*/?>", "", cleaned, flags=re.I)

        # Collapse excessive whitespace
        cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.base_url}/v1/models")
            response.raise_for_status()
            data = response.json()
            models = data.get("data", [])
            print(f"Available models: {len(models)}")
            for model in models:
                print(f"  - {model.get('id', 'Unknown')}")
            return models
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []
    
    def set_model(self, model_id: str) -> None:
        """Set the active model to use"""
        self.model = model_id
        print(f"Model set to: {model_id}")
    
    def chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 0.9,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send a chat completion request
        
        Args:
            messages: List of Message objects
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            stream: Whether to stream the response
        
        Returns:
            Response from the API
        """
        if not self.model:
            print("Error: No model set. Use set_model() first.")
            return {}
        
        try:
            # Convert Message objects to dicts
            messages_list = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            payload = {
                "model": self.model,
                "messages": messages_list,
                "temperature": temperature,
                "top_p": top_p,
                "stream": stream
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error in chat completion: {e}")
            return {}
    
    def extract_response_text(self, response: Dict[str, Any]) -> str:
        """
        Extract text from API response and clean it
        
        Args:
            response: Response dictionary from the API
        
        Returns:
            Cleaned response text
        """
        if not response or "choices" not in response:
            return ""
        
        # Try to get content from chat completion response
        if "message" in response["choices"][0]:
            raw_text = response["choices"][0]["message"].get("content", "")
        else:
            # Fallback for completion response
            raw_text = response["choices"][0].get("text", "")
        
        # Sanitize the text
        cleaned = self._sanitize_text(raw_text)
        return cleaned
    
    def completion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 0.9,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send a text completion request
        
        Args:
            prompt: The input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            stream: Whether to stream the response
        
        Returns:
            Response from the API
        """
        if not self.model:
            print("Error: No model set. Use set_model() first.")
            return {}
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "top_p": top_p,
                "stream": stream
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            response = requests.post(
                f"{self.base_url}/v1/completions",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error in completion: {e}")
            return {}
    
    def get_embeddings(self, text: str) -> Optional[List[float]]:
        """
        Get embeddings for a text
        
        Args:
            text: The text to embed
        
        Returns:
            List of embedding values
        """
        if not self.model:
            print("Error: No model set. Use set_model() first.")
            return None
        
        try:
            payload = {
                "model": self.model,
                "input": text
            }
            
            response = requests.post(
                f"{self.base_url}/v1/embeddings",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("data", [{}])[0].get("embedding", [])
            return embeddings
        except Exception as e:
            print(f"Error getting embeddings: {e}")
            return None


def main():
    """Example usage of the LM Studio client"""
    parser = argparse.ArgumentParser(description="LM Studio client example runner")
    parser.add_argument("-p", "--prompt", help="Question or prompt to send to the model")
    parser.add_argument("-m", "--model", help="Model id to use (overrides auto-selection)")
    args = parser.parse_args()

    # Determine user question from args or interactive input
    question = args.prompt or input("Enter your question: ")

    # Initialize the client
    client = LMStudioClient()
    
    # Get available models
    models = client.get_available_models()
    
    if models:
        # Set the model: use provided model id or the first available model
        model_id = args.model or models[0].get("id")
        client.set_model(model_id)
        
        # Example 1: Simple chat completion
        print("\n--- Chat Completion Example ---")
        system_prompt = load_system_prompt()
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=question)
        ]
        
        response = client.chat_completion(messages, max_tokens=500)
        
        if response and "choices" in response:
            raw = response['choices'][0].get('message', {}).get('content') or response['choices'][0].get('text', '')
            cleaned = client._sanitize_text(raw)
            print(f"Assistant: {cleaned}")


if __name__ == "__main__":
    main()