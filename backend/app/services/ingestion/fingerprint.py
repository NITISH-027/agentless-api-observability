import re
import hashlib

def generate_fingerprint(
    method: str,
    path: str,
    error_type: str,
    error_message: str,
    stack_trace: str
) -> str:
    """
    Computes a SHA-256 fingerprint for deduplication.
    Uses method, normalized path, error type, normalized error message, and the last stack trace location.
    """
    # 1. Normalize method
    normalized_method = method.strip().upper()

    # 2. Normalize path (strip UUIDs and IDs)
    uuid_pattern = r'/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    path_normalized = re.sub(uuid_pattern, '/:uuid', path)
    path_normalized = re.sub(r'/\d+', '/:id', path_normalized)
    
    # 3. Normalize exception message (lowercase, strip numbers)
    normalized_msg = error_message.lower().strip()
    normalized_msg = re.sub(r'\d+', '', normalized_msg)

    # 4. Extract relevant stack trace location
    stack_location = "unknown"
    if stack_trace:
        # Split trace into lines
        lines = [line.strip() for line in stack_trace.split("\n") if line.strip()]
        # Look for the last line referencing a file to pinpoint the issue location
        for line in reversed(lines):
            if line.startswith("File ") or 'file "' in line.lower():
                stack_location = line
                break
        if stack_location == "unknown" and lines:
            stack_location = lines[-1]

    # Combine into a single key
    raw_key = f"{normalized_method}|{path_normalized}|{error_type}|{normalized_msg}|{stack_location}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
