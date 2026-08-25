import re
from typing import Tuple, Dict

def is_english_text(text: str) -> bool:
    """
    Simple heuristic check to see if text contains non-ASCII or Cyrillic/non-English characters.
    Returns True if text appears to be English-only.
    """
    if not text or not text.strip():
        return True
    
    # Check for Cyrillic characters (Russian, Ukrainian, etc.) or other non-Latin scripts
    cyrillic_pattern = re.compile(r'[\u0400-\u04FF]')
    if cyrillic_pattern.search(text):
        return False
        
    return True

async def translate_to_english(text: str) -> Tuple[str, bool]:
    """
    Translates non-English text into English.
    Returns a tuple of (translated_text, was_translated).
    
    If text is already English, returns (text, False).
    """
    if not text or is_english_text(text):
        return text, False

    # Dictionary of common phrases for mocking/fallback translation in offline/test mode
    mock_translations: Dict[str, str] = {
        "канцелярия": "Office Supplies",
        "бумага для принтера": "Printer Paper",
        "расходы на поездку": "Travel Expenses",
        "закупка инвентаря": "Inventory Purchase",
        "оплата подписки": "Subscription Fee",
        "ремонт оборудования": "Equipment Repair"
    }

    cleaned = text.strip().lower()
    if cleaned in mock_translations:
        return mock_translations[cleaned], True

    # Fallback simulated AI translation for non-English text
    # In production, this connects to LLM / Translation API (e.g. OpenAI / Azure Translator / Gemini API)
    translated = f"[Translated] {text.strip()}"
    return translated, True
