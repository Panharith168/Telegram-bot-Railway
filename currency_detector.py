"""
Currency detection and extraction module

Automatically detects and extracts USD and Cambodian Riel amounts from text messages
using comprehensive pattern matching.
"""

import re
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

class CurrencyDetector:
    def __init__(self):
        # USD patterns
        self.usd_patterns = [
            # Standard formats: $100, $100.50, $1,200.25
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\$',
            
            # Simple formats: $100, 100$
            r'\$(\d+(?:\.\d{2})?)',
            r'(\d+(?:\.\d{2})?)\$',
            
            # Word-based: 100 USD, 100 dollars
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*USD',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',
            r'USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'dollars?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            
            # Transaction formats: paid $100, received $50
            r'paid\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'received\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'transfer\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*paid',
        ]
        
        # Cambodian Riel patterns
        self.riel_patterns = [
            # Standard formats: ៛25,000, ៛500,000
            r'៛(\d{1,3}(?:,\d{3})*)',
            r'(\d{1,3}(?:,\d{3})*)៛',
            
            # Simple formats: ៛25000, 25000៛
            r'៛(\d+)',
            r'(\d+)៛',
            
            # Word-based: 25000 riel, 25000 KHR
            r'(\d{1,3}(?:,\d{3})*)\s*riel',
            r'(\d{1,3}(?:,\d{3})*)\s*KHR',
            r'riel\s*(\d{1,3}(?:,\d{3})*)',
            r'KHR\s*(\d{1,3}(?:,\d{3})*)',
            
            # Transaction formats: paid ៛25000, received ៛50000
            r'paid\s*៛(\d{1,3}(?:,\d{3})*)',
            r'received\s*៛(\d{1,3}(?:,\d{3})*)',
            r'៛(\d{1,3}(?:,\d{3})*)\s*paid',
        ]
    
    def extract_amounts(self, text: str) -> Tuple[float, float]:
        """
        Extract USD and Cambodian Riel amounts from text.
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Tuple[float, float]: (usd_amount, riel_amount)
        """
        usd_amount = 0.0
        riel_amount = 0.0
        
        if not text:
            return usd_amount, riel_amount
        
        # Clean text
        text = text.strip()
        
        try:
            # Extract USD amounts
            usd_amounts = self._extract_usd(text)
            if usd_amounts:
                usd_amount = max(usd_amounts)  # Take largest amount found
                logger.debug(f"USD amounts found: {usd_amounts}, using: ${usd_amount}")
            
            # Extract Riel amounts
            riel_amounts = self._extract_riel(text)
            if riel_amounts:
                riel_amount = max(riel_amounts)  # Take largest amount found
                logger.debug(f"Riel amounts found: {riel_amounts}, using: ៛{riel_amount}")
            
        except Exception as e:
            logger.error(f"Error extracting amounts from '{text}': {e}")
        
        return usd_amount, riel_amount
    
    def _extract_usd(self, text: str) -> List[float]:
        """Extract all USD amounts from text."""
        amounts = []
        
        for pattern in self.usd_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Remove commas and convert to float
                    clean_amount = match.replace(',', '')
                    amount = float(clean_amount)
                    if amount > 0:
                        amounts.append(amount)
                except (ValueError, TypeError):
                    continue
        
        return amounts
    
    def _extract_riel(self, text: str) -> List[float]:
        """Extract all Riel amounts from text."""
        amounts = []
        
        for pattern in self.riel_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Remove commas and convert to float
                    clean_amount = match.replace(',', '')
                    amount = float(clean_amount)
                    if amount > 0:
                        amounts.append(amount)
                except (ValueError, TypeError):
                    continue
        
        return amounts
    
    def test_detection(self, text: str) -> str:
        """
        Test currency detection on a text message.
        
        Args:
            text (str): Text to test
            
        Returns:
            str: Formatted test results
        """
        usd_amount, riel_amount = self.extract_amounts(text)
        
        result = f"**Currency Detection Test**\n\n"
        result += f"**Input:** `{text}`\n\n"
        result += f"**Results:**\n"
        result += f"💵 USD: ${usd_amount:.2f}\n"
        result += f"🏛️ KHR: ៛{riel_amount:,.0f}\n\n"
        
        if usd_amount == 0 and riel_amount == 0:
            result += "❌ No currency amounts detected"
        else:
            result += "✅ Currency detection successful"
        
        return result

# Global detector instance
detector = CurrencyDetector()

def extract_amounts(text: str) -> Tuple[float, float]:
    """Convenience function for extracting amounts."""
    return detector.extract_amounts(text)

def test_detection(text: str) -> str:
    """Convenience function for testing detection."""
    return detector.test_detection(text)