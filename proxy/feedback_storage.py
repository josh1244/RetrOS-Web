"""
Feedback Storage System for RetrOS

Handles persistence of user feedback for analytics and future model improvements.
Stores feedback in JSON format in the proxy directory.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Feedback storage directory
FEEDBACK_DIR = Path(__file__).parent / "feedback"
FEEDBACK_FILE = FEEDBACK_DIR / "feedback_history.json"

# Valid feedback preset types
VALID_FEEDBACK_TYPES = [
    "too_modern",          # Generated styles are too modern/polished
    "too_simple",          # Generated styles are too minimal/plain
    "simplify_layout",     # Layout has too many visual elements
    "make_usable",         # Styling breaks usability or readability
    "regenerate",          # Generic regenerate request
    "good",                # User is happy with the result
    "other"                # Free-form feedback
]


class FeedbackError(Exception):
    """Feedback storage error."""
    pass


def _ensure_feedback_dir():
    """Ensure feedback directory exists."""
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


def _load_feedback_history() -> List[Dict[str, Any]]:
    """Load feedback history from disk."""
    try:
        _ensure_feedback_dir()
        if FEEDBACK_FILE.exists():
            with open(FEEDBACK_FILE, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"Failed to load feedback history: {e}")
    return []


def _save_feedback_history(history: List[Dict[str, Any]]):
    """Save feedback history to disk."""
    try:
        _ensure_feedback_dir()
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        logger.debug(f"Saved {len(history)} feedback entries")
    except Exception as e:
        logger.error(f"Failed to save feedback history: {e}")
        raise FeedbackError(f"Could not save feedback: {e}")


def validate_feedback(feedback_data: Dict[str, Any] | str | None) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate feedback data.
    
    Args:
        feedback_data: Can be string (free-form) or dict with 'type' and 'text'
    
    Returns:
        (is_valid, error_message, normalized_feedback_dict)
    """
    if not feedback_data:
        return True, None, None  # Feedback is optional
    
    if isinstance(feedback_data, str):
        # Simple free-form feedback
        text = feedback_data.strip()
        if len(text) > 500:
            return False, "Feedback text exceeds 500 characters", None
        return True, None, {"type": "other", "text": text}
    
    elif isinstance(feedback_data, dict):
        feedback_type = feedback_data.get("type", "").strip().lower()
        feedback_text = feedback_data.get("text", "").strip()
        
        # Validate type
        if feedback_type and feedback_type not in VALID_FEEDBACK_TYPES:
            return False, f"Invalid feedback type: {feedback_type}. Valid types: {', '.join(VALID_FEEDBACK_TYPES)}", None
        
        # Validate text length
        if len(feedback_text) > 500:
            return False, "Feedback text exceeds 500 characters", None
        
        # At least one field required
        if not feedback_type and not feedback_text:
            return False, "Feedback must have either 'type' or 'text'", None
        
        normalized = {
            "type": feedback_type or "other",
            "text": feedback_text
        }
        return True, None, normalized
    
    else:
        return False, "Feedback must be string or dict", None


def store_feedback(
    domain: str,
    era: str,
    feedback: Dict[str, Any],
    dom_digest: str = "",
    cache_key: str = ""
) -> bool:
    """
    Store feedback for a domain/era combination.
    
    Args:
        domain: Website domain
        era: Era name
        feedback: Validated feedback dict with 'type' and 'text'
        dom_digest: Optional DOM digest for tracking changes
        cache_key: Optional cache key used for generation
    
    Returns:
        True if stored successfully, False otherwise
    """
    try:
        _ensure_feedback_dir()
        history = _load_feedback_history()
        
        # Create feedback entry
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "domain": domain,
            "era": era,
            "feedback_type": feedback.get("type", "other"),
            "feedback_text": feedback.get("text", ""),
            "dom_digest": dom_digest[:32] if dom_digest else "",
            "cache_key": cache_key[:32] if cache_key else ""
        }
        
        history.append(entry)
        _save_feedback_history(history)
        
        logger.info(f"Stored feedback for {domain} ({era}): {feedback.get('type', 'other')}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to store feedback: {e}")
        return False


def get_feedback_summary(domain: Optional[str] = None, era: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get feedback summary (for analytics).
    
    Args:
        domain: Optional filter by domain
        era: Optional filter by era
        limit: Max entries to return
    
    Returns:
        List of feedback entries
    """
    try:
        history = _load_feedback_history()
        
        # Filter if needed
        if domain:
            history = [e for e in history if e.get("domain") == domain]
        if era:
            history = [e for e in history if e.get("era") == era]
        
        # Return most recent first
        return sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
    
    except Exception as e:
        logger.error(f"Failed to get feedback summary: {e}")
        return []


def get_feedback_stats() -> Dict[str, Any]:
    """
    Get feedback statistics.
    
    Returns:
        Dict with feedback counts by type, domain, era
    """
    try:
        history = _load_feedback_history()
        
        stats = {
            "total_feedback": len(history),
            "by_type": {},
            "by_domain": {},
            "by_era": {},
            "recent_domains": []
        }
        
        domains_set = set()
        
        for entry in history:
            # Count by type
            fb_type = entry.get("feedback_type", "unknown")
            stats["by_type"][fb_type] = stats["by_type"].get(fb_type, 0) + 1
            
            # Count by domain
            domain = entry.get("domain", "unknown")
            stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1
            domains_set.add(domain)
            
            # Count by era
            era = entry.get("era", "unknown")
            stats["by_era"][era] = stats["by_era"].get(era, 0) + 1
        
        # Get recent domains
        recent = sorted(
            [(d, c) for d, c in stats["by_domain"].items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        stats["recent_domains"] = [{"domain": d, "count": c} for d, c in recent]
        
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}")
        return {"error": str(e)}
