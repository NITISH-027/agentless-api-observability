import re
from typing import List, Dict, Any, Tuple

def parse_traceback_string(traceback_str: str) -> Tuple[List[Dict[str, Any]], str, str]:
    """
    Parses a standard Python traceback string into a list of structured frames,
    and extracts the final exception type and exception message.
    
    Each frame contains:
      - file_path: str (raw file path)
      - line_number: int (1-indexed line number)
      - function_name: str (name of target function)
      - code_line: str (offending line source snippet if present)
    """
    # Pattern to match standard traceback frame lines:
    # File "path/to/file.py", line 123, in func_name
    frame_pattern = re.compile(
        r'File\s+"([^"]+)",\s*line\s*(\d+),\s*in\s*([^\n]+)'
    )
    
    frames = []
    lines = [line.strip() for line in traceback_str.split("\n")]
    # Clean up empty lines
    lines = [line for line in lines if line]
    
    for i, line in enumerate(lines):
        match = frame_pattern.search(line)
        if match:
            file_path = match.group(1)
            line_num = int(match.group(2))
            function_name = match.group(3).strip()
            
            # Extract code preview line if the next line is NOT another file frame
            # and NOT an exception declaration line (doesn't contain colon or traceback headers)
            code_line = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                is_next_frame = frame_pattern.search(next_line)
                is_header = next_line.startswith("Traceback")
                # If it's not a frame, header, or the last line containing the exception colon
                if not is_next_frame and not is_header and (i + 1 != len(lines) - 1 or ":" not in next_line):
                    code_line = next_line
                    
            frames.append({
                "file_path": file_path,
                "line_number": line_num,
                "function_name": function_name,
                "code_line": code_line
            })
            
    # Extract exception type and message (typically the last line, e.g., ValueError: invalid qty)
    exc_type = "UnknownError"
    exc_msg = ""
    
    if lines:
        # Check from bottom up for the first line with a colon representing error: message
        for line in reversed(lines):
            # Skip traceback structure lines
            if frame_pattern.search(line) or line.startswith("Traceback") or line.startswith("During handling"):
                continue
            if ":" in line:
                parts = line.split(":", 1)
                exc_type = parts[0].strip()
                exc_msg = parts[1].strip()
                break
            else:
                exc_msg = line
                break
                
    return frames, exc_type, exc_msg
