"""
Parsing utilities for extracting structured data from LLM responses.
"""

import re
from typing import Dict, List, Any, Optional

def extract_xml(text: str, tag: str) -> Optional[str]:
    """
    Extract content between XML-like tags from text.
    
    Args:
        text: Text to search in
        tag: Tag name to extract
        
    Returns:
        Content between tags, or None if not found
    """
    pattern = f"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else None

def extract_thoughts(content: str, node_id: str) -> List[Dict[str, Any]]:
    """
    Extract thoughts from LLM text output.
    
    Args:
        content: LLM response text
        node_id: Current node ID (for thought ID generation)
        
    Returns:
        List of thought dictionaries
    """
    thoughts = []
    
    # Look for patterns like "1. Thought description" or "Thought 1: description"
    thought_patterns = [
        r'(?:^|\n)(\d+)[.:]\s+(.*?)(?=\n*(?:\d+[.:]|\Z))',  # Numbered lists
        r'(?:^|\n)Thought[ \t]+(\d+)[.:][ \t]+(.*?)(?=\n*(?:Thought[ \t]+\d+[.:]|\Z))'  # "Thought N:" format
    ]
    
    for pattern in thought_patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            for idx, match in enumerate(matches):
                thought_num = int(match[0])
                full_text = match[1].strip()
                
                # Extract thought description and rationale
                thought_desc = full_text
                rationale = ""
                
                # Look for rationale sections
                rationale_patterns = [
                    r'\*\*Rationale\*\*:\s*(.*?)(?=\n\n|\Z)',
                    r'Rationale:\s*(.*?)(?=\n\n|\Z)'
                ]
                
                for r_pattern in rationale_patterns:
                    r_match = re.search(r_pattern, full_text, re.DOTALL)
                    if r_match:
                        # Extract main thought (everything before rationale)
                        thought_parts = re.split(r_pattern, full_text, maxsplit=1)
                        if thought_parts and len(thought_parts) > 0:
                            thought_desc = thought_parts[0].strip()
                        rationale = r_match.group(1).strip()
                        break
                
                # Clean up thought description
                thought_desc = re.sub(r'^\*\*Thought\*\*:\s*', '', thought_desc)
                thought_desc = thought_desc.strip()
                
                thought_id = f"{node_id}-t{thought_num}"
                thoughts.append({
                    "thought_id": thought_id,
                    "description": thought_desc,
                    "generation_rationale": rationale
                })
    
    return thoughts
