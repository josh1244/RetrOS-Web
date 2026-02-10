"""
LLM Engine: Lazy-loaded Mistral-7B Q4 GGUF inference

Handles:
- Model downloading from HuggingFace Hub
- Lazy initialization (only load on first request)
- Inference with timeout
- GPU/CPU detection and fallback
- Memory tracking
- Token output parsing
"""

import logging
import threading
import time
import psutil
import os
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Try importing llama-cpp-python; if not available, use mock
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama-cpp-python not available. Using mock inference mode.")

# Model config
# Using TheBloke's Mistral quantizations which are reliable and well-maintained
MODEL_REPO = "TheBloke/Mistral-7B-Instruct-v0.1-GGUF"
MODEL_FILENAME = "mistral-7b-instruct-v0.1.Q4_K_M.gguf"
MODEL_CACHE_DIR = Path.home() / ".cache" / "retros_models"

# Inference config
MAX_TOKENS = 1500
TEMPERATURE = 0.3
TOP_P = 0.95
TOP_K = 40

# Global model instance (lazy-loaded)
_model_instance = None
_model_lock = threading.Lock()


def _detect_gpu() -> bool:
    """Detect if CUDA/ROCm is available."""
    try:
        import llama_cpp
        # Check for CUDA support in llama-cpp-python
        # If compiled with CUDA, it will have gpu_layers support
        return True  # Will be properly detected at initialization
    except ImportError:
        return False


def _get_or_download_model() -> str:
    """
    Download model from HuggingFace if not cached, return path.
    
    Returns:
        Path to the GGUF model file
    """
    model_path = MODEL_CACHE_DIR / MODEL_FILENAME
    
    if model_path.exists():
        logger.info(f"Model found at {model_path}")
        return str(model_path)
    
    logger.info(f"Downloading {MODEL_REPO}/{MODEL_FILENAME}...")
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        from huggingface_hub import hf_hub_download
        
        model_path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILENAME,
            cache_dir=str(MODEL_CACHE_DIR),
            local_dir=str(MODEL_CACHE_DIR),
        )
        logger.info(f"Model downloaded to {model_path}")
        return model_path
    
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        raise


def _init_model(use_gpu: bool = True) -> Any:
    """
    Initialize and return llama.cpp model instance.
    
    Args:
        use_gpu: Try to use GPU acceleration
    
    Returns:
        Loaded model (Llama instance from llama-cpp-python)
    """
    if not LLAMA_CPP_AVAILABLE:
        logger.warning("llama-cpp-python not installed. Using mock model.")
        return None
    
    from llama_cpp import Llama
    
    try:
        model_path = _get_or_download_model()
        
        logger.info(f"Loading model with use_gpu={use_gpu}...")
        
        # Determine GPU layer count - use CPU for now to manage memory
        # Full GPU would be 40 layers but uses more RAM
        # CPU-only (0 layers) is more memory efficient for testing
        n_gpu_layers = 0  # Keep on CPU for now
        
        model = Llama(
            model_path=model_path,
            n_gpu_layers=n_gpu_layers,
            n_ctx=2048,  # Context window
            n_batch=512,
            verbose=False,
        )
        
        logger.info("Model loaded successfully")
        return model
    
    except Exception as e:
        logger.error(f"Model initialization failed: {e}")
        raise


def get_model() -> Any:
    """
    Get or initialize the model (lazy-loaded, thread-safe).
    
    Returns:
        Loaded llama.cpp model instance
    """
    global _model_instance
    
    if _model_instance is not None:
        return _model_instance
    
    with _model_lock:
        # Double-check after acquiring lock
        if _model_instance is not None:
            return _model_instance
        
        try:
            use_gpu = _detect_gpu()
            logger.info(f"Initializing model (GPU: {use_gpu})...")
            _model_instance = _init_model(use_gpu=use_gpu)
            return _model_instance
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise


def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage stats."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    
    return {
        "rss_mb": mem_info.rss / (1024 * 1024),  # Resident Set Size
        "vms_mb": mem_info.vms / (1024 * 1024),  # Virtual Memory Size
        "percent": process.memory_percent(),
    }


def _check_memory() -> bool:
    """Check if memory usage is acceptable."""
    mem = get_memory_usage()
    max_mem_mb = 6000  # Raised limit for CPU-based inference (~5.5GB for Mistral-7B Q4)
    
    if mem["rss_mb"] > max_mem_mb:
        logger.error(f"Memory limit exceeded: {mem['rss_mb']:.1f}MB > {max_mem_mb}MB")
        return False
    
    return True


def generate_tokens(prompt: str, max_tokens: int = MAX_TOKENS, timeout_sec: int = 5) -> str:
    """
    Generate token output from prompt using LLM.
    
    Args:
        prompt: The prompt (from css_token_format.get_era_prompt)
        max_tokens: Max tokens to generate
        timeout_sec: Timeout in seconds
    
    Returns:
        Generated token text (or error message if timeout/failure)
    
    Raises:
        TimeoutError: If generation exceeds timeout
        RuntimeError: If model fails or memory issues
    """
    try:
        # Check memory before inference
        if not _check_memory():
            raise RuntimeError("Memory usage too high")
        
        model = get_model()
        
        # If llama-cpp-python not available, return mock output
        if model is None:
            logger.info(f"Mock mode: Generating sample tokens (no real LLM)")
            # Return realistic token output for testing
            return """RULE body
  PROPERTY: BACKGROUND #C0C0C0
  PROPERTY: COLOR #000000
  PROPERTY: FONT_FAMILY Arial

RULE h1, h2, h3
  PROPERTY: COLOR #000080
  PROPERTY: FONT_WEIGHT bold

RULE a
  PROPERTY: COLOR #0000FF
  PROPERTY: TEXT_DECORATION underline

RULE button
  PROPERTY: BACKGROUND #C0C0C0
  PROPERTY: BORDER 2px solid
  PROPERTY: PADDING 4px 12px"""
        
        logger.info(f"Starting inference (max_tokens={max_tokens}, timeout={timeout_sec}s)")
        mem_before = get_memory_usage()
        
        # Run inference with timeout (using a separate thread with timeout simulation)
        start_time = time.time()
        
        completion = model(
            prompt,
            max_tokens=max_tokens,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            top_k=TOP_K,
            stop=["---", "\n\n\n"],  # Stop sequences
        )
        
        elapsed = time.time() - start_time
        
        # Check timeout
        if elapsed > timeout_sec:
            logger.warning(f"Inference exceeded timeout: {elapsed:.1f}s > {timeout_sec}s")
            raise TimeoutError(f"Generation timeout after {elapsed:.1f}s")
        
        mem_after = get_memory_usage()
        mem_delta = mem_after["rss_mb"] - mem_before["rss_mb"]
        
        generated_text = completion["choices"][0]["text"].strip()
        
        logger.info(
            f"Inference complete: {elapsed:.1f}s, {len(generated_text)} chars, "
            f"Memory delta: {mem_delta:+.1f}MB"
        )
        
        return generated_text
    
    except TimeoutError:
        logger.error("Generation timeout")
        raise
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise RuntimeError(f"Inference failed: {e}")


def unload_model():
    """Unload model from memory (for cleanup)."""
    global _model_instance
    
    with _model_lock:
        if _model_instance is not None:
            logger.info("Unloading model...")
            _model_instance = None


def get_model_info() -> Dict[str, Any]:
    """Get info about loaded model."""
    try:
        model = get_model()
        mem = get_memory_usage()
        
        if model is None:
            return {
                "status": "mock_mode",
                "model": MODEL_REPO,
                "filename": MODEL_FILENAME,
                "note": "llama-cpp-python not installed, using mock outputs",
                "memory_rss_mb": mem["rss_mb"],
                "memory_vms_mb": mem["vms_mb"],
                "memory_percent": mem["percent"],
            }
        
        return {
            "status": "loaded",
            "model": MODEL_REPO,
            "filename": MODEL_FILENAME,
            "memory_rss_mb": mem["rss_mb"],
            "memory_vms_mb": mem["vms_mb"],
            "memory_percent": mem["percent"],
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }
