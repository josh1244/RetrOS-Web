"""
DOM Reducer: Converts raw HTML → Structured DOM Summary

Purpose: Reduce noisy HTML into a clean, semantic summary for the LLM.
This keeps prompt size small and generation fast.
"""

import logging
import hashlib
import json
from bs4 import BeautifulSoup
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def _count_elements(soup: BeautifulSoup, tag: str) -> int:
    """Count occurrences of a tag."""
    return len(soup.find_all(tag, recursive=True))


def _get_element_types(soup: BeautifulSoup) -> List[str]:
    """Extract semantic structure from page."""
    semantic_tags = ["header", "nav", "main", "article", "section", "aside", "footer", "form"]
    found = []
    for tag in semantic_tags:
        if soup.find(tag):
            found.append(tag)
    return found


def _estimate_layout(soup: BeautifulSoup) -> str:
    """Guess layout density: sparse vs dense."""
    total_text = sum(len(t.get_text()) for t in soup.find_all())
    total_tags = len(soup.find_all())
    
    # Ratio of text to tags
    if total_tags == 0:
        return "empty"
    
    ratio = total_text / total_tags
    
    if ratio < 5:
        return "sparse"
    elif ratio < 20:
        return "medium"
    else:
        return "dense"


def _count_major_divs(soup: BeautifulSoup) -> int:
    """Count divs that likely represent major layout containers."""
    count = 0
    for div in soup.find_all("div", recursive=True):
        if div.get("id") or div.get("class") or div.get("role"):
            count += 1
    return count


def reduce_dom(html: str, max_summary_lines: int = 100) -> Dict[str, Any]:
    """
    Convert raw HTML to a structured summary.
    
    Args:
        html: Raw HTML string
        max_summary_lines: Limit summary size (for very large pages)
    
    Returns:
        dict with title, layout_summary, element_types, etc.
    """
    try:
        logger.debug("Reducing DOM...")
        soup = BeautifulSoup(html, "lxml")
        
        # Extract title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()[:100]  # Cap at 100 chars
        
        # Extract meta description
        meta_desc = ""
        md = soup.find("meta", attrs={"name": "description"})
        if md and md.get("content"):
            meta_desc = md.get("content").strip()[:100]
        
        # Count key elements
        layout_summary = {
            "headers": _count_elements(soup, "h1") + _count_elements(soup, "h2") + _count_elements(soup, "h3"),
            "navs": _count_elements(soup, "nav"),
            "sidebars": len(soup.find_all("aside")),
            "main_columns": len(soup.find_all("main")),
            "forms": _count_elements(soup, "form"),
            "tables": _count_elements(soup, "table"),
            "images": _count_elements(soup, "img"),
            "links": _count_elements(soup, "a"),
            "paragraphs": _count_elements(soup, "p"),
            "lists": _count_elements(soup, "ul") + _count_elements(soup, "ol"),
        }
        
        # Semantic structure
        element_types = _get_element_types(soup)
        
        # Layout density
        estimated_density = _estimate_layout(soup)
        
        # Check for dark mode hints
        has_dark_mode = False
        html_lower = html.lower()
        if 'prefers-color-scheme' in html_lower or 'dark' in html_lower:
            has_dark_mode = True
        
        total_elements = len(soup.find_all())
        div_count = _count_elements(soup, "div")
        major_divs = _count_major_divs(soup)

        # Compute deterministic fingerprint digest
        fingerprint_payload = {
            "layout_summary": layout_summary,
            "element_types": element_types,
            "total_elements": total_elements,
            "divs": div_count,
            "major_divs": major_divs,
        }
        summary_text = json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(summary_text.encode()).hexdigest()
        
        result = {
            "status": "ok",
            "title": title,
            "meta_description": meta_desc,
            "layout_summary": layout_summary,
            "element_types": element_types,
            "estimated_density": estimated_density,
            "has_dark_mode": has_dark_mode,
            "digest": digest,
            "total_elements": total_elements,
            "divs": div_count,
            "major_divs": major_divs,
        }
        
        logger.info(f"DOM reduced: {result['total_elements']} elements → {estimated_density} density")
        return result
        
    except Exception as e:
        logger.error(f"DOM reduction error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "title": "",
            "layout_summary": {},
            "element_types": [],
            "estimated_density": "unknown",
            "digest": "",
        }


def format_summary_for_prompt(summary: Dict[str, Any]) -> str:
    """
    Format DOM summary into a readable prompt snippet.
    
    Used by era prompts to describe the page structure.
    """
    if summary.get("status") != "ok":
        return "Page structure unknown (parsing error)"
    
    ls = summary.get("layout_summary", {})
    elements = summary.get("element_types", [])
    density = summary.get("estimated_density", "unknown")
    title = summary.get("title", "(no title)")
    
    snippet = f"""
Page: {title}
Structure: {', '.join(elements) if elements else 'basic HTML'}
Density: {density}
Layout: {ls.get('headers', 0)} headers, {ls.get('navs', 0)} nav(s), {ls.get('main_columns', 0)} main area(s)
Content: {ls.get('paragraphs', 0)} paragraphs, {ls.get('forms', 0)} form(s), {ls.get('tables', 0)} table(s)
Media: {ls.get('images', 0)} images, {ls.get('links', 0)} links
""".strip()
    
    return snippet
