"""
CSS Generator for RetrOS - Era-specific styling using template-based approach.
This avoids heavy LLM overhead while providing era-appropriate CSS.
"""
import logging
import re
import hashlib

logger = logging.getLogger(__name__)

# Era-specific CSS templates
ERA_TEMPLATES = {
    "90s": {
        "description": "1990s web aesthetic: bright colors, gradients, tiled backgrounds",
        "colors": ["#FF00FF", "#00FFFF", "#FFFF00", "#00FF00"],
        "fonts": "Comic Sans MS, Arial",
        "effects": ["text-shadow", "blink", "background-color: #C0C0C0"],
    },
    "win95": {
        "description": "Windows 95 aesthetic: beveled buttons, grays, beveled edges",
        "colors": ["#C0C0C0", "#808080", "#000080", "#FFFFFF"],
        "fonts": "MS Sans Serif, Arial",
        "effects": ["border: 2px solid; border-color: #DFDFDF #808080"],
    },
    "win98": {
        "description": "Windows 98 aesthetic: similar to Win95 but with more rounded edges",
        "colors": ["#CCCCCC", "#666666", "#000080", "#FFFFFF"],
        "fonts": "Tahoma, Arial",
        "effects": ["border-radius: 3px", "background: #CCCCCC"],
    },
    "winxp": {
        "description": "Windows XP aesthetic: blue gradients, rounded buttons, modern",
        "colors": ["#0078D4", "#FFFFFF", "#F0F0F0", "#C0CCDB"],
        "fonts": "Segoe UI, Arial",
        "effects": ["border-radius: 5px", "box-shadow: 0 1px 3px rgba(0,0,0,0.3)"],
    },
}


class CSSGenerationError(Exception):
    pass


def _generate_era_css(era: str, dom_info: dict) -> str:
    """Generate CSS based on era template and DOM info."""
    if era not in ERA_TEMPLATES:
        raise CSSGenerationError(f"Unknown era: {era}")
    
    template = ERA_TEMPLATES[era]
    logger.info(f"Generating {era} CSS")
    
    # Build CSS rules for common elements
    css_lines = [
        f"/* RetrOS - {era} Era Styling */",
        f"/* Generated for era: {era} */",
        "",
        "* { font-family: " + template["fonts"] + "; }",
        "",
    ]
    
    # Color palette (rotate through colors for different elements)
    colors = template["colors"]
    effects = template["effects"]
    
    # Style body
    css_lines.append(f"body {{ background-color: {colors[0]}; color: {colors[2]}; }}")
    
    # Style common containers
    css_lines.append(f"div, section, article, main {{ background-color: {colors[1]}; padding: 8px; margin: 4px; }}")
    
    # Style text elements
    css_lines.append(f"h1, h2, h3 {{ color: {colors[2]}; font-weight: bold; }}")
    css_lines.append(f"p, span, a {{ color: {colors[2]}; }}")
    css_lines.append(f"a {{ text-decoration: underline; }}")
    
    # Style buttons/interactive
    css_lines.append(f"button, input[type='button'], input[type='submit'] {{ background-color: {colors[0]}; color: {colors[3]}; padding: 4px 8px; {effects[0] if len(effects) > 0 else ''}; }}")
    
    # Style inputs
    css_lines.append(f"input, textarea {{ background-color: {colors[3]}; border: 1px solid {colors[2]}; padding: 4px; }}")
    
    # Add era-specific effects
    for effect in effects:
        if "border" in effect.lower():
            css_lines.append(f"div, section {{ {effect}; }}")
    
    css_lines.append("")
    css_text = "\n".join(css_lines)
    
    logger.debug(f"Generated CSS ({len(css_text)} bytes)")
    return css_text


def _validate_css(css: str) -> tuple[bool, str]:
    """Basic CSS validation: check for syntax errors and common issues."""
    errors = []
    
    # Count braces
    open_braces = css.count("{")
    close_braces = css.count("}")
    if open_braces != close_braces:
        errors.append(f"Mismatched braces: {open_braces} open, {close_braces} close")
    
    # Basic check: should have some content
    if not css.strip() or len(css.strip()) < 10:
        errors.append("CSS appears to be empty or too short")
    
    if errors:
        msg = "; ".join(errors)
        logger.warning(f"CSS validation issues: {msg}")
        return False, msg
    
    logger.info("CSS validation passed")
    return True, ""


def generate_css(dom_content: str, era: str, dom_digest: str = "", feedback: dict = None) -> dict:
    """
    Generate era-appropriate CSS from DOM content.
    
    Args:
        dom_content: HTML DOM as string or parsed info
        era: Era name (90s, win95, win98, winxp, etc)
        dom_digest: Digest of DOM for caching
        feedback: Optional feedback dict with type and text
    
    Returns:
        dict with css, metadata, cache_key
    """
    try:
        logger.info(f"Generating CSS for era={era}, digest={dom_digest[:16] if dom_digest else 'N/A'}...")
        
        # Parse feedback if provided
        feedback_type = feedback.get("type", "") if feedback else ""
        
        # Extract basic DOM info (simplified for now)
        dom_info = {
            "tag_count": len(re.findall(r"<[a-z]+", dom_content.lower())) if isinstance(dom_content, str) else 0,
        }
        
        # Generate CSS based on era
        css = _generate_era_css(era, dom_info)
        
        # Validate CSS
        valid, validation_msg = _validate_css(css)
        
        # Compute cache key
        cache_key = hashlib.sha256(f"{era}|{dom_digest}".encode()).hexdigest()
        
        result = {
            "status": "ok",
            "css": css,
            "era": era,
            "valid": valid,
            "validation_message": validation_msg if validation_msg else "No issues",
            "cache_key": cache_key,
            "feedback_applied": bool(feedback_type),
        }
        
        logger.info(f"CSS generation complete: {len(css)} bytes, valid={valid}")
        return result
        
    except CSSGenerationError as e:
        logger.error(f"CSS generation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in CSS generation: {e}")
        raise CSSGenerationError(str(e))
