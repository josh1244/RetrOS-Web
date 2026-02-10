"""
Fallback Styles: Safe, era-appropriate CSS for use when LLM generation fails.

These are guaranteed-safe, minimal stylesheets that provide era aesthetics
even if the AI engine is unavailable or times out.
"""

FALLBACK_STYLES = {
    "web1996": """
/* RetrOS 1990s Web - Fallback */
body { font-family: Arial, sans-serif; background-color: #C0C0C0; color: #000; }
h1, h2, h3 { color: #00FF00; font-weight: bold; }
p { color: #000; line-height: 1.6; }
a { color: #0000FF; text-decoration: underline; }
a:visited { color: #800080; }
button, input[type="submit"] { background: #00FF00; color: #000; padding: 4px 8px; border: 2px solid #000; }
input, textarea { background: #FFF; border: 2px solid #000; padding: 4px; }
""",
    
    "win95": """
/* RetrOS Windows 95 - Fallback */
body { font-family: "MS Sans Serif", Arial, sans-serif; background-color: #C0C0C0; color: #000; }
h1, h2, h3 { color: #000080; font-weight: bold; }
p { color: #000; }
a { color: #0000FF; text-decoration: underline; }
button, input[type="submit"], input[type="button"] { 
    background: #C0C0C0; 
    border: 2px solid; 
    border-color: #DFDFDF #808080 #808080 #DFDFDF; 
    padding: 4px 8px; 
    cursor: pointer; 
}
button:active { border-color: #808080 #DFDFDF #DFDFDF #808080; }
input, textarea { background: #FFF; border: 2px solid #808080; padding: 4px; }
""",
    
    "win98": """
/* RetrOS Windows 98 - Fallback */
body { font-family: Tahoma, Arial, sans-serif; background-color: #CCCCCC; color: #000; }
h1, h2, h3 { color: #000080; font-weight: bold; }
p { color: #000; }
a { color: #0000FF; text-decoration: underline; }
button, input[type="submit"] { 
    background: #CCCCCC; 
    border: 2px solid; 
    border-color: #E0E0E0 #808080 #808080 #E0E0E0; 
    padding: 4px 8px; 
    border-radius: 2px;
    cursor: pointer; 
}
input, textarea { background: #FFF; border: 1px solid #999; padding: 4px; }
""",
    
    "winxp": """
/* RetrOS Windows XP - Fallback */
body { font-family: "Segoe UI", Tahoma, Arial, sans-serif; background: #ECE9D8; color: #000; }
h1, h2, h3 { color: #0078D4; font-weight: bold; }
p { color: #000; }
a { color: #0078D4; text-decoration: underline; }
a:visited { color: #800080; }
button, input[type="submit"] { 
    background: linear-gradient(to bottom, #F0F0F0, #C0C0C0);
    border: 1px solid #0078D4;
    border-radius: 3px;
    padding: 4px 12px;
    cursor: pointer;
    color: #000;
}
button:hover { background: linear-gradient(to bottom, #F5F5F5, #D5D5D5); }
input, textarea { background: #FFF; border: 1px solid #999; padding: 4px; border-radius: 2px; }
""",
}


def get_fallback_css(era: str) -> str:
    """Get fallback CSS for an era."""
    return FALLBACK_STYLES.get(era, FALLBACK_STYLES["win95"])
