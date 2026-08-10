from typing import Dict, List, Optional

DEFAULT_SENSITIVE_KEYS = ["authorization", "cookie", "set-cookie", "x-api-key", "api-key", "token"]

def scrub_headers(headers: Optional[Dict[str, str]], sensitive_keys: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Scrubs sensitive headers case-insensitively, replacing their values with [FILTERED].
    """
    if not headers:
        return {}
        
    keys_to_scrub = {k.lower() for k in (sensitive_keys or DEFAULT_SENSITIVE_KEYS)}
    scrubbed = {}
    
    for key, val in headers.items():
        if key.lower() in keys_to_scrub:
            scrubbed[key] = "[FILTERED]"
        else:
            scrubbed[key] = val
            
    return scrubbed
