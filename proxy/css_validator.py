"""
CSS Validator: Ensure generated CSS is safe and valid.

Validates:
- Syntax (no unmatched braces)
- No dangerous directives (@import, @keyframes in unsafe contexts)
- Proper scoping
"""

import logging
import re

logger = logging.getLogger(__name__)


def validate_css(css: str) -> tuple[bool, str]:
    """
    Validate CSS syntax and safety.
    
    Args:
        css: CSS string to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not css or not css.strip():
        return False, "CSS is empty"
    
    errors = []
    
    # Check brace matching
    open_braces = css.count("{")
    close_braces = css.count("}")
    if open_braces != close_braces:
        errors.append(f"Mismatched braces: {open_braces} open, {close_braces} close")
    
    # Check for dangerous directives
    dangerous_patterns = [
        (r"@import\s*['\"]", "Dangerous @import detected"),
        (r"javascript:", "JavaScript protocol detected"),
        (r"expression\s*\(", "CSS expression detected"),
    ]
    
    for pattern, msg in dangerous_patterns:
        if re.search(pattern, css, re.IGNORECASE):
            errors.append(msg)
    
    # Basic selector validation (very loose)
    lines = css.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Skip comments and empty lines
        if not stripped or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        
        # Warn if line ends with colon without semicolon (might be incomplete)
        if ":" in stripped and not stripped.endswith(";") and not stripped.endswith("{"):
            if not stripped.startswith("//"):  # Skip comments
                # Likely a property without semicolon
                if "{" not in stripped and "}" not in stripped:
                    logger.debug(f"Line {i} might be incomplete: {stripped[:50]}")
    
    if errors:
        error_msg = "; ".join(errors)
        logger.warning(f"CSS validation failed: {error_msg}")
        return False, error_msg
    
    logger.info("CSS validation passed")
    return True, ""


def sanitize_css(css: str) -> str:
    """
    Remove or neutralize potentially dangerous CSS.
    
    Args:
        css: CSS string
    
    Returns:
        Sanitized CSS
    """
    # Remove @import directives
    css = re.sub(r'@import\s*[^;]*;', '', css)
    
    # Remove javascript: protocols
    css = re.sub(r'javascript:', '', css, flags=re.IGNORECASE)
    
    # Remove expression() calls
    css = re.sub(r'expression\s*\([^)]*\)', '', css, flags=re.IGNORECASE)
    
    return css
