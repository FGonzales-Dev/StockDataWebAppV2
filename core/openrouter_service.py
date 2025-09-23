"""
OpenRouter AI Service for Stock Ticker Symbol Resolution
Converts company names to stock ticker symbols using AI
"""

import requests
import json
import logging
from typing import Dict, Optional, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)

class OpenRouterService:
    """
    Service to interact with OpenRouter AI for stock ticker symbol resolution
    """
    
    def __init__(self):
        self.api_key = "add this in droplet instead"
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def resolve_ticker_symbol(self, company_name: str, market: str = None) -> Dict:
        """
        Resolve company name to stock ticker symbol using OpenRouter AI
        
        Args:
            company_name (str): Company name (e.g., "Apple", "Microsoft", "Tesla")
            market (str, optional): Market exchange (e.g., "NASDAQ", "NYSE", "XNAS")
            
        Returns:
            Dict: {
                'success': bool,
                'ticker': str,
                'market': str,
                'company_name': str,
                'confidence': str,
                'error': str (if any)
            }
        """
        try:
            # Prepare the prompt for AI
            prompt = self._create_ticker_resolution_prompt(company_name, market)
            
            # Make API request to OpenRouter
            response = self._make_openrouter_request(prompt)
            
            if response.get('success'):
                return self._parse_ai_response(response['data'], company_name, market)
            else:
                return {
                    'success': False,
                    'ticker': company_name.upper(),
                    'market': market or 'XNAS',
                    'company_name': company_name,
                    'confidence': 'low',
                    'error': response.get('error', 'Unknown error')
                }
                
        except Exception as e:
            logger.error(f"Error in resolve_ticker_symbol: {str(e)}")
            return {
                'success': False,
                'ticker': company_name.upper(),
                'market': market or 'XNAS',
                'company_name': company_name,
                'confidence': 'low',
                'error': f"Service error: {str(e)}"
            }
    
    def _create_ticker_resolution_prompt(self, company_name: str, market: str = None) -> str:
        """
        Create a prompt for AI to resolve ticker symbol
        """
        market_context = f" on {market}" if market else ""
        
        prompt = f"""
You are a financial data expert. I need you to convert a company name to its stock ticker symbol.

Company Name: "{company_name}"
Market: {market or "Any major exchange (NASDAQ, NYSE, etc.)"}

Please provide the most likely stock ticker symbol for this company. Consider:

1. If the input is already a ticker symbol (like "AAPL", "MSFT"), return it as-is
2. For company names, provide the most common ticker symbol
3. If the company has multiple classes of stock, provide the most commonly traded one
4. If you're unsure, provide your best guess with a note about uncertainty

Respond in this exact JSON format:
{{
    "ticker": "TICKER_SYMBOL",
    "market": "MARKET_CODE",
    "company_name": "FULL_COMPANY_NAME",
    "confidence": "high|medium|low",
    "reasoning": "Brief explanation of your choice"
}}

Market codes to use:
- XNAS for NASDAQ
- XNYS for NYSE  
- XASE for AMEX
- XNCM for NASDAQ Capital Market
- XNMS for NASDAQ Global Market
- XNGS for NASDAQ Global Select

Examples:
- "Apple" → {{"ticker": "AAPL", "market": "XNAS", "company_name": "Apple Inc.", "confidence": "high", "reasoning": "Apple Inc. trades as AAPL on NASDAQ"}}
- "Microsoft" → {{"ticker": "MSFT", "market": "XNAS", "company_name": "Microsoft Corporation", "confidence": "high", "reasoning": "Microsoft Corporation trades as MSFT on NASDAQ"}}
- "AAPL" → {{"ticker": "AAPL", "market": "XNAS", "company_name": "Apple Inc.", "confidence": "high", "reasoning": "Input is already a valid ticker symbol"}}

Now resolve: "{company_name}"{market_context}
"""
        return prompt.strip()
    
    def _make_openrouter_request(self, prompt: str) -> Dict:
        """
        Make API request to OpenRouter
        """
        try:
            payload = {
                "model": "anthropic/claude-3.5-sonnet",  # Using Claude for better reasoning
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.1,  # Low temperature for consistent results
                "top_p": 0.9
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    return {
                        'success': True,
                        'data': content
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No response from AI model'
                    }
            else:
                return {
                    'success': False,
                    'error': f"API request failed with status {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout - AI service is slow'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def _parse_ai_response(self, ai_response: str, original_company: str, original_market: str = None) -> Dict:
        """
        Parse AI response and extract ticker information
        """
        try:
            # Try to extract JSON from the response
            # AI might include extra text, so we need to find the JSON part
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = ai_response[start_idx:end_idx]
            parsed_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['ticker', 'market', 'company_name', 'confidence']
            for field in required_fields:
                if field not in parsed_data:
                    raise ValueError(f"Missing required field: {field}")
            
            return {
                'success': True,
                'ticker': parsed_data['ticker'].upper(),
                'market': parsed_data['market'].upper(),
                'company_name': parsed_data['company_name'],
                'confidence': parsed_data['confidence'],
                'reasoning': parsed_data.get('reasoning', ''),
                'original_input': original_company,
                'original_market': original_market
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {str(e)}")
            # Fallback: try to extract ticker from response text
            return self._fallback_parse(ai_response, original_company, original_market)
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return {
                'success': False,
                'ticker': original_company.upper(),
                'market': original_market or 'XNAS',
                'company_name': original_company,
                'confidence': 'low',
                'error': f"Failed to parse AI response: {str(e)}"
            }
    
    def _fallback_parse(self, response_text: str, original_company: str, original_market: str = None) -> Dict:
        """
        Fallback parsing when JSON parsing fails
        """
        # Look for common ticker patterns in the response
        import re
        
        # Common ticker patterns (3-5 uppercase letters)
        ticker_pattern = r'\b([A-Z]{3,5})\b'
        tickers = re.findall(ticker_pattern, response_text.upper())
        
        if tickers:
            # Take the first ticker found
            ticker = tickers[0]
            return {
                'success': True,
                'ticker': ticker,
                'market': original_market or 'XNAS',
                'company_name': original_company,
                'confidence': 'medium',
                'reasoning': 'Extracted from AI response text',
                'original_input': original_company,
                'original_market': original_market
            }
        else:
            # No ticker found, return original input
            return {
                'success': False,
                'ticker': original_company.upper(),
                'market': original_market or 'XNAS',
                'company_name': original_company,
                'confidence': 'low',
                'error': 'Could not extract ticker from AI response',
                'original_input': original_company,
                'original_market': original_market
            }
    
    def batch_resolve_tickers(self, company_names: list, market: str = None) -> list:
        """
        Resolve multiple company names to ticker symbols
        
        Args:
            company_names (list): List of company names
            market (str, optional): Market exchange
            
        Returns:
            list: List of resolution results
        """
        results = []
        for company_name in company_names:
            result = self.resolve_ticker_symbol(company_name, market)
            results.append(result)
        return results


# Global instance
openrouter_service = OpenRouterService()


def resolve_stock_ticker(company_name: str, market: str = None) -> Dict:
    """
    Convenience function to resolve a single ticker symbol
    
    Args:
        company_name (str): Company name or ticker symbol
        market (str, optional): Market exchange
        
    Returns:
        Dict: Resolution result
    """
    return openrouter_service.resolve_ticker_symbol(company_name, market)


def is_likely_ticker_symbol(text: str) -> bool:
    """
    Check if the input text is likely already a ticker symbol
    
    Args:
        text (str): Input text
        
    Returns:
        bool: True if likely a ticker symbol
    """
    if not text:
        return False
    
    text = text.strip().upper()
    
    # Ticker symbols are typically 1-5 uppercase letters
    if len(text) > 5:
        return False
    
    # Check if it's all uppercase letters
    if not text.isalpha():
        return False
    
    # Common ticker patterns
    if len(text) >= 1 and len(text) <= 5:
        return True
    
    return False
