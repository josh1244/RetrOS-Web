"""
CSS Generation Orchestrator: Ties together all modules (DOM reducer, LLM, token parser, validator).

Pipeline:
1. Fetch HTML (external) or use provided HTML
2. Reduce DOM to summary
3. Build era-specific prompt
4. Run LLM inference (with timeout)
5. Parse token output
6. Expand to CSS
7. Validate CSS
8. Return result or fallback
"""

import logging
import time
from typing import Dict, Any, Optional

from dom_reducer import reduce_dom, format_summary_for_prompt
from css_token_format import get_era_prompt, parse_token_output, expand_tokens_to_css
from llm_engine import generate_tokens, get_model_info
from css_validator import validate_css, sanitize_css
from fallback_styles import get_fallback_css
from feedback_storage import store_feedback, validate_feedback

logger = logging.getLogger(__name__)


class CSSGenerationError(Exception):
    """CSS generation failed."""
    pass


def generate_css_with_llm(
    html: str,
    era: str,
    dom_digest: str = "",
    feedback: Dict[str, str] = None,
    domain: str = "",
    timeout_sec: int = 5
) -> Dict[str, Any]:
    """
    Generate CSS using the full LLM pipeline.
    
    Args:
        html: Raw HTML content
        era: Era name (win95, win98, winxp, web1996)
        dom_digest: Optional digest for caching
        feedback: Optional feedback dict {type, text}
        domain: Optional domain for feedback storage
        timeout_sec: Timeout for LLM inference
    
    Returns:
        dict: {
            status: ok | error | fallback,
            css: CSS string,
            cache_key: hash for caching,
            metadata: {generation_ms, fallback, tokens_used, ...},
            error: error message if status is error
        }
    """
    start_time = time.time()
    
    # Validate and normalize feedback
    if feedback:
        is_valid, error_msg, normalized_feedback = validate_feedback(feedback)
        if not is_valid:
            logger.warning(f"Invalid feedback data: {error_msg}")
            normalized_feedback = None
        feedback = normalized_feedback
    
    try:
        logger.info(f"Starting CSS generation: era={era}, html_size={len(html)} bytes, feedback={feedback.get('type') if feedback else 'none'}")
        
        # Step 1: Validate era
        valid_eras = ["web1996", "win95", "win98", "winxp"]
        if era not in valid_eras:
            raise CSSGenerationError(f"Unknown era: {era}. Valid: {valid_eras}")
        
        # Step 2: Reduce DOM
        logger.debug("Reducing DOM...")
        summary = reduce_dom(html)
        if summary.get("status") != "ok":
            raise CSSGenerationError(f"DOM reduction failed: {summary.get('error')}")
        
        # Step 3: Format for prompt
        logger.debug("Formatting prompt...")
        prompt_snippet = format_summary_for_prompt(summary)
        
        # Step 4: Build era prompt (with feedback adjustment)
        logger.debug(f"Building {era} prompt...")
        prompt = get_era_prompt(era, prompt_snippet, feedback)
        logger.debug(f"Prompt size: {len(prompt)} chars")
        
        # Step 5: Run LLM inference
        logger.info(f"Running LLM inference (timeout={timeout_sec}s)...")
        try:
            token_output = generate_tokens(prompt, timeout_sec=timeout_sec)
        except TimeoutError:
            logger.warning("LLM inference timed out, using fallback")
            cache_key = summary.get("digest", "")
            elapsed = time.time() - start_time
            
            # Store feedback if provided
            if feedback and domain:
                store_feedback(domain, era, feedback, dom_digest, cache_key)
            
            return {
                "status": "fallback",
                "css": get_fallback_css(era),
                "cache_key": cache_key,
                "metadata": {
                    "era": era,
                    "generation_ms": int((time.time() - start_time) * 1000),
                    "fallback": True,
                    "fallback_reason": "timeout",
                },
            }
        except Exception as e:
            logger.error(f"LLM error: {e}")
            cache_key = summary.get("digest", "")
            
            # Store feedback if provided
            if feedback and domain:
                store_feedback(domain, era, feedback, dom_digest, cache_key)
            
            return {
                "status": "fallback",
                "css": get_fallback_css(era),
                "cache_key": cache_key,
                "metadata": {
                    "era": era,
                    "generation_ms": int((time.time() - start_time) * 1000),
                    "fallback": True,
                    "fallback_reason": str(e)[:50],
                },
            }
        
        # Step 6: Parse tokens
        logger.debug("Parsing token output...")
        try:
            rules = parse_token_output(token_output)
            if not rules:
                raise CSSGenerationError("No CSS rules generated")
        except Exception as e:
            logger.error(f"Token parsing failed: {e}")
            cache_key = summary.get("digest", "")
            
            # Store feedback if provided
            if feedback and domain:
                store_feedback(domain, era, feedback, dom_digest, cache_key)
            
            return {
                "status": "fallback",
                "css": get_fallback_css(era),
                "cache_key": cache_key,
                "metadata": {
                    "era": era,
                    "generation_ms": int((time.time() - start_time) * 1000),
                    "fallback": True,
                    "fallback_reason": "parse_error",
                },
            }
        
        # Step 7: Expand to CSS
        logger.debug("Expanding tokens to CSS...")
        css = expand_tokens_to_css(rules)
        logger.info(f"CSS generated: {len(css)} bytes, {len(rules)} rules")
        
        # Step 8: Validate CSS
        logger.debug("Validating CSS...")
        valid, error_msg = validate_css(css)
        if not valid:
            logger.warning(f"CSS validation failed: {error_msg}")
            # Try sanitizing and re-validating
            css_sanitized = sanitize_css(css)
            valid, error_msg = validate_css(css_sanitized)
            if not valid:
                logger.error("Sanitized CSS still invalid, using fallback")
                cache_key = summary.get("digest", "")
                
                # Store feedback if provided
                if feedback and domain:
                    store_feedback(domain, era, feedback, dom_digest, cache_key)
                
                return {
                    "status": "fallback",
                    "css": get_fallback_css(era),
                    "cache_key": cache_key,
                    "metadata": {
                        "era": era,
                        "generation_ms": int((time.time() - start_time) * 1000),
                        "fallback": True,
                        "fallback_reason": "validation_failed",
                    },
                }
            css = css_sanitized
        
        # Success!
        elapsed_ms = int((time.time() - start_time) * 1000)
        cache_key = summary.get("digest", "")
        
        # Store feedback if provided
        if feedback and domain:
            store_feedback(domain, era, feedback, dom_digest, cache_key)
        
        logger.info(f"CSS generation complete in {elapsed_ms}ms")
        
        return {
            "status": "ok",
            "css": css,
            "cache_key": cache_key,
            "metadata": {
                "era": era,
                "generation_ms": elapsed_ms,
                "fallback": False,
                "rules_count": len(rules),
                "token_output_chars": len(token_output),
            },
        }
    
    except Exception as e:
        logger.error(f"Unexpected error in CSS generation: {e}")
        return {
            "status": "error",
            "css": None,
            "error": str(e)[:100],
            "metadata": {
                "era": era,
                "generation_ms": int((time.time() - start_time) * 1000),
            },
        }


def get_ai_status() -> Dict[str, Any]:
    """Get status of AI engine."""
    return get_model_info()
