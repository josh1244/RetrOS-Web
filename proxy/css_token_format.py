"""
CSS Token Format & Era Prompts

Defines how the LLM outputs CSS (token format) and prompt engineering
for each era to ensure consistent, era-appropriate styling.
"""

import logging
from typing import Dict, List, Any
from enum import Enum

logger = logging.getLogger(__name__)


class CSSToken(Enum):
    """CSS properties the LLM can emit as tokens."""
    BACKGROUND = "BACKGROUND"
    COLOR = "COLOR"
    FONT_FAMILY = "FONT_FAMILY"
    FONT_SIZE = "FONT_SIZE"
    FONT_WEIGHT = "FONT_WEIGHT"
    BORDER = "BORDER"
    BORDER_RADIUS = "BORDER_RADIUS"
    PADDING = "PADDING"
    MARGIN = "MARGIN"
    TEXT_DECORATION = "TEXT_DECORATION"
    BOX_SHADOW = "BOX_SHADOW"
    TEXT_SHADOW = "TEXT_SHADOW"
    DISPLAY = "DISPLAY"
    WIDTH = "WIDTH"
    HEIGHT = "HEIGHT"


# Era-specific design guidelines and color palettes
ERA_DESIGN = {
    "web1996": {
        "name": "Classic 1990s Web",
        "colors": {
            "primary": "#00FF00",
            "secondary": "#FF00FF",
            "accent": "#FFFF00",
            "background": "#C0C0C0",
            "text": "#000000",
        },
        "fonts": ["Comic Sans MS", "Arial", "Helvetica"],
        "characteristics": [
            "Bright neon colors",
            "Marquee text",
            "Animated GIFs (visual indicators)",
            "Beveled borders",
            "Table-based layouts",
            "Underlined links",
        ],
    },
    "win95": {
        "name": "Windows 95",
        "colors": {
            "primary": "#C0C0C0",
            "secondary": "#DFDFDF",
            "accent": "#000080",
            "background": "#C0C0C0",
            "text": "#000000",
        },
        "fonts": ["MS Sans Serif", "Arial", "Helvetica"],
        "characteristics": [
            "Gray beveled 3D buttons",
            "Inset borders (3D effect)",
            "System gray background",
            "Taskbar-like elements",
            "Dialog box metaphor",
            "Navy blue accents",
        ],
    },
    "win98": {
        "name": "Windows 98",
        "colors": {
            "primary": "#CCCCCC",
            "secondary": "#E0E0E0",
            "accent": "#000080",
            "background": "#CCCCCC",
            "text": "#000000",
        },
        "fonts": ["Tahoma", "Arial", "Helvetica"],
        "characteristics": [
            "Slightly lighter grays than Win95",
            "Rounded button corners (minimal)",
            "Similar beveled effect but refined",
            "Gradient backgrounds (subtle)",
            "Improved typography",
        ],
    },
    "winxp": {
        "name": "Windows XP",
        "colors": {
            "primary": "#0078D4",
            "secondary": "#F0F0F0",
            "accent": "#FFFFFF",
            "background": "#ECE9D8",
            "text": "#000000",
        },
        "fonts": ["Segoe UI", "Tahoma", "Arial"],
        "characteristics": [
            "Luna blue theme",
            "Glossy buttons with gradients",
            "Rounded corners (5-10px)",
            "Soft shadows and glows",
            "Modern flat elements mixed with 3D",
            "Light blue accents",
            "Smooth transitions and hover effects",
        ],
    },
}


def get_era_prompt(era: str, dom_summary: str, feedback: Dict[str, str] = None) -> str:
    """
    Generate a specialized prompt for the LLM based on era and DOM.
    
    Args:
        era: Era name (win95, win98, winxp, web1996)
        dom_summary: Output from dom_reducer.format_summary_for_prompt()
        feedback: Optional feedback dict with 'type' and 'text'
    
    Returns:
        A structured prompt for the LLM
    """
    if era not in ERA_DESIGN:
        raise ValueError(f"Unknown era: {era}")
    
    design = ERA_DESIGN[era]
    colors = design["colors"]
    
    prompt = f"""You are a CSS styling expert. Generate era-appropriate CSS for a webpage.

ERA: {design['name']}
---
Key characteristics of this era:
{chr(10).join(f"- {c}" for c in design['characteristics'])}

Color palette:
- Primary: {colors['primary']}
- Secondary: {colors['secondary']}
- Accent: {colors['accent']}
- Background: {colors['background']}
- Text: {colors['text']}

Preferred fonts: {', '.join(design['fonts'])}

---
PAGE STRUCTURE:
{dom_summary}

---
TASK: Generate CSS rules that apply {design['name']} styling to this page.

RULES:
1. Output ONLY CSS tokens in the format below. No explanations.
2. Each rule starts with "RULE <selector>"
3. Each property starts with "  PROPERTY: <token> <value>"
4. Use tokens like BACKGROUND, COLOR, FONT_FAMILY, BORDER, etc.
5. Use only values from the color palette above.
6. Keep selectors broad: body, h1-h3, p, a, button, input, div, section
7. Ensure the styling is authentic to {design['name']}

EXAMPLE FORMAT:
RULE body
  PROPERTY: BACKGROUND {colors['background']}
  PROPERTY: COLOR {colors['text']}
  PROPERTY: FONT_FAMILY "{design['fonts'][0]}"

RULE a
  PROPERTY: COLOR {colors['accent']}
  PROPERTY: TEXT_DECORATION underline

---
Generate the CSS tokens now:
"""
    
    if feedback and (feedback.get('type') or feedback.get('text')):
        feedback_type = feedback.get('type', 'other')
        feedback_text = feedback.get('text', '')
        
        # Build feedback adjustment instructions based on type
        adjustments = ""
        if feedback_type == "too_modern":
            adjustments = """
ADJUSTMENT (User feedback: styles too modern):
- Use darker, more retro color schemes
- Add more beveled 3D borders and effects
- Increase use of era-characteristic design
- Make buttons more prominent with bevels
- Use system fonts appropriate to the era"""
        
        elif feedback_type == "too_simple":
            adjustments = """
ADJUSTMENT (User feedback: styles too simple):
- Improve typography with better hierarchy
- Add subtle box-shadows or gradients where appropriate
- Use more decorative borders and separators
- Enhance visual distinction between elements
- Add more color variation and depth"""
        
        elif feedback_type == "simplify_layout":
            adjustments = """
ADJUSTMENT (User feedback: layout too complex):
- Reduce border styles and visual noise
- Simplify color schemes (use fewer colors)
- Remove unnecessary decorative effects
- Keep styling minimal but era-appropriate
- Focus on readability and simplicity"""
        
        elif feedback_type == "make_usable":
            adjustments = """
ADJUSTMENT (User feedback: improve usability):
- Ensure high contrast for text readability
- Make interactive elements clearly distinguishable
- Improve button visibility and padding
- Ensure sufficient spacing between elements
- Prioritize clarity and functionality over aesthetics"""
        
        elif feedback_type == "good":
            adjustments = """
ADJUSTMENT (User feedback: good result):
- Continue with similar approach
- Apply same style principles to other elements
- Maintain consistency with what worked well"""
        
        else:
            # Generic or custom feedback
            adjustments = f"""
ADJUSTMENT (User feedback: {feedback_text}):
- Apply user's feedback to the generation
- Incorporate their suggestions while maintaining era accuracy"""
        
        feedback_note = f"""
---
FEEDBACK FROM PREVIOUS GENERATION:
Type: {feedback_type}
{f"Comment: {feedback_text}" if feedback_text else ""}
{adjustments}

Please regenerate the CSS with these adjustments in mind.

---
Generate the improved CSS tokens now:
"""
        prompt += feedback_note
    
    return prompt


def parse_token_output(token_text: str) -> List[Dict[str, Any]]:
    """
    Parse LLM token output into structured CSS rules.
    
    Expected format:
    RULE body
      PROPERTY: BACKGROUND #f0f0f0
      PROPERTY: COLOR #000000
    
    RULE h1, h2, h3
      PROPERTY: COLOR #0078d4
    
    Args:
        token_text: LLM output text
    
    Returns:
        List of dicts: [{"selector": "body", "properties": {...}}, ...]
    """
    rules = []
    current_rule = None
    
    for line in token_text.split("\n"):
        line = line.strip()
        
        if line.startswith("RULE "):
            # Save previous rule
            if current_rule:
                rules.append(current_rule)
            
            # Start new rule
            selector = line[5:].strip()
            current_rule = {"selector": selector, "properties": {}}
        
        elif line.startswith("PROPERTY:") and current_rule:
            # Parse property
            parts = line[9:].strip().split(None, 1)
            if len(parts) == 2:
                token_name, value = parts
                current_rule["properties"][token_name] = value
    
    # Don't forget last rule
    if current_rule:
        rules.append(current_rule)
    
    logger.info(f"Parsed {len(rules)} CSS rules from token output")
    return rules


def expand_tokens_to_css(rules: List[Dict[str, Any]]) -> str:
    """
    Convert parsed token rules into actual CSS.
    
    Args:
        rules: Output from parse_token_output()
    
    Returns:
        Valid CSS string
    """
    css_lines = ["/* RetrOS CSS - LLM Generated */", ""]
    
    for rule in rules:
        selector = rule.get("selector", "")
        properties = rule.get("properties", {})
        
        if not selector or not properties:
            continue
        
        css_lines.append(f"{selector} {{")
        
        # Map tokens to CSS properties
        token_map = {
            "BACKGROUND": "background-color",
            "COLOR": "color",
            "FONT_FAMILY": "font-family",
            "FONT_SIZE": "font-size",
            "FONT_WEIGHT": "font-weight",
            "BORDER": "border",
            "BORDER_RADIUS": "border-radius",
            "PADDING": "padding",
            "MARGIN": "margin",
            "TEXT_DECORATION": "text-decoration",
            "BOX_SHADOW": "box-shadow",
            "TEXT_SHADOW": "text-shadow",
            "DISPLAY": "display",
            "WIDTH": "width",
            "HEIGHT": "height",
        }
        
        for token, value in properties.items():
            css_prop = token_map.get(token, token.lower().replace("_", "-"))
            css_lines.append(f"  {css_prop}: {value};")
        
        css_lines.append("}")
        css_lines.append("")
    
    return "\n".join(css_lines)
