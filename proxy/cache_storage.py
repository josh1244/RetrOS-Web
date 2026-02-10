"""
Hybrid cache storage for generated CSS.

Directory structure:
~/.retroweb/styles/<era>/<domain>-approved.css
~/.retroweb/styles/<era>/<domain>-metadata.json
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

BASE_CACHE_DIR = Path.home() / ".retroweb" / "styles"
STATS_FILE = BASE_CACHE_DIR / "cache_stats.json"


def _ensure_era_dir(era: str) -> Path:
    era_dir = BASE_CACHE_DIR / era
    era_dir.mkdir(parents=True, exist_ok=True)
    return era_dir


def _sanitize_domain(domain: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\.-]", "_", domain)


def _get_cache_paths(domain: str, era: str) -> Tuple[Path, Path]:
    era_dir = _ensure_era_dir(era)
    safe_domain = _sanitize_domain(domain)
    css_path = era_dir / f"{safe_domain}-approved.css"
    meta_path = era_dir / f"{safe_domain}-metadata.json"
    return css_path, meta_path


def _load_stats() -> Dict[str, Any]:
    if STATS_FILE.exists():
        try:
            return json.loads(STATS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"hits": 0, "misses": 0, "last_updated": None, "total_size_bytes": 0}
    return {"hits": 0, "misses": 0, "last_updated": None, "total_size_bytes": 0}


def _save_stats(stats: Dict[str, Any]) -> None:
    BASE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    STATS_FILE.write_text(json.dumps(stats, indent=2), encoding="utf-8")


def get_total_cache_size_bytes() -> int:
    if not BASE_CACHE_DIR.exists():
        return 0
    total = 0
    for path in BASE_CACHE_DIR.rglob("*"):
        if path.is_file():
            total += path.stat().st_size
    return total


def _update_stats(hit: Optional[bool]) -> None:
    stats = _load_stats()
    if hit is True:
        stats["hits"] = int(stats.get("hits", 0)) + 1
    elif hit is False:
        stats["misses"] = int(stats.get("misses", 0)) + 1
    stats["total_size_bytes"] = get_total_cache_size_bytes()
    stats["last_updated"] = datetime.now(timezone.utc).isoformat()
    _save_stats(stats)


def build_cache_key(domain: str, era: str, dom_digest: str) -> str:
    digest_part = dom_digest[:32] if dom_digest else "default"
    return f"{domain}-{era}-{digest_part}"


def get_cached_style(domain: str, era: str, dom_digest: str) -> Optional[Dict[str, Any]]:
    css_path, meta_path = _get_cache_paths(domain, era)

    if not css_path.exists() or not meta_path.exists():
        _update_stats(hit=False)
        return None

    try:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        _update_stats(hit=False)
        return None

    cached_digest = metadata.get("dom_digest", "")
    if dom_digest and cached_digest and dom_digest != cached_digest:
        _update_stats(hit=False)
        return None

    try:
        css = css_path.read_text(encoding="utf-8")
    except Exception:
        _update_stats(hit=False)
        return None

    if "cache_key" not in metadata:
        metadata["cache_key"] = build_cache_key(domain, era, dom_digest or cached_digest)

    _update_stats(hit=True)
    return {"css": css, "metadata": metadata}


def save_cached_style(
    domain: str,
    era: str,
    css: str,
    dom_digest: str,
    approval_status: str = "unapproved",
) -> Dict[str, Any]:
    css_path, meta_path = _get_cache_paths(domain, era)
    css_path.write_text(css, encoding="utf-8")

    metadata = {
        "domain": domain,
        "era": era,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "approval_status": approval_status,
        "dom_digest": dom_digest,
        "cache_key": build_cache_key(domain, era, dom_digest),
        "css_bytes": len(css.encode("utf-8"))
    }

    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    _update_stats(hit=None)
    return metadata
