"""
JAWIR OS - LLM Utilities
Helper functions for working with LLM responses.
"""

from typing import Any


def extract_text_from_response(content: Any) -> str:
    """
    Extract text from LLM response content.
    Handles both Gemini 2 (string) and Gemini 3 (list of parts) formats.
    
    Args:
        content: The response.content from LangChain LLM
        
    Returns:
        Extracted text as string
    """
    if isinstance(content, str):
        return content
    
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict):
                if 'text' in part:
                    text_parts.append(part['text'])
                elif 'content' in part:
                    text_parts.append(str(part['content']))
            elif isinstance(part, str):
                text_parts.append(part)
        return "".join(text_parts)
    
    return str(content)
