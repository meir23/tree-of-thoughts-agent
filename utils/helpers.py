"""
Helper functions for the ToTA agent.

This module provides utility functions such as timestamp generation and ID creation.
"""

import datetime
import uuid

def generate_timestamp() -> str:
    """
    Generate a timestamp in YYYYMMDD_HHMMSS format.
    
    Returns:
        Formatted timestamp string
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID, optionally with a prefix.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique ID string
    """
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
    return f"{prefix}-{unique_id}" if prefix else unique_id
