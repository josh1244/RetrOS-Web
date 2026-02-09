import hashlib
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) "
    "Gecko/20100101 Firefox/109.0"
)


class FetchError(Exception):
    pass


def _compute_digest(soup: BeautifulSoup) -> str:
    # Improved digest: tag hierarchy, counts, and text nodes
    tag_counts = {}
    text_nodes = 0
    for tag in soup.find_all():
        tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1
        if tag.string and tag.string.strip():
            text_nodes += 1
    
    tag_items = [f"{k}:{tag_counts[k]}" for k in sorted(tag_counts.keys())]
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    
    # Include hierarchy info: count of divs, forms, inputs to detect layout changes
    div_count = tag_counts.get("div", 0)
    form_count = tag_counts.get("form", 0)
    input_count = tag_counts.get("input", 0)
    
    data = ("|".join(tag_items) + f"|title:{title}|divs:{div_count}|forms:{form_count}|inputs:{input_count}|text_nodes:{text_nodes}")
    logger.debug(f"Computed digest for {title}: {data[:100]}...")
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def fetch_page(url: str, timeout: int = 10, max_size: int = 5 * 1024 * 1024, max_redirects: int = 5):
    logger.info(f"Fetching page: {url}")
    session = requests.Session()
    session.max_redirects = max_redirects
    headers = {"User-Agent": DEFAULT_UA}

    try:
        # Stream so we can bail out if the response is too large
        with session.get(url, headers=headers, timeout=timeout, stream=True, allow_redirects=True) as resp:
            resp.raise_for_status()
            logger.info(f"Fetched {url} -> {resp.status_code} from {resp.url}")

            content_length = resp.headers.get("Content-Length")
            if content_length is not None:
                try:
                    cl = int(content_length)
                    if cl > max_size:
                        logger.warning(f"Content too large: {cl} bytes > {max_size} bytes")
                        return {"error": "content_too_large", "content_length": cl}
                except ValueError:
                    pass

            chunks = []
            size = 0
            for chunk in resp.iter_content(chunk_size=8192):
                if not chunk:
                    break
                size += len(chunk)
                if size > max_size:
                    logger.warning(f"Downloaded content exceeds {max_size}: {size} bytes")
                    return {"error": "content_too_large", "downloaded": size}
                chunks.append(chunk)

            html = b"".join(chunks).decode(resp.encoding or "utf-8", errors="replace")

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {url} after {timeout}s")
        raise FetchError(f"Timeout after {timeout}s")
    except requests.exceptions.RequestException as e:
        logger.error(f"Fetch error for {url}: {e}")
        raise FetchError(str(e))

    # Parse DOM (static, no JS execution)
    logger.debug(f"Parsing DOM for {url}")
    soup = BeautifulSoup(html, "lxml")

    # Gather basic metadata
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = ""
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        meta_desc = md.get("content").strip()

    tag_count = len(soup.find_all())
    div_count = len(soup.find_all("div"))

    digest = _compute_digest(soup)
    logger.info(f"Digest for {url}: {digest}")

    result = {
        "status": "ok",
        "final_url": resp.url if 'resp' in locals() else url,
        "status_code": resp.status_code if 'resp' in locals() else None,
        "content_length": len(html),
        "title": title,
        "meta_description": meta_desc,
        "tag_count": tag_count,
        "div_count": div_count,
        "digest": digest,
    }
    logger.info(f"Fetch result for {url}: {result['status']} ({result['tag_count']} tags)")
    return result
