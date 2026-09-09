import re
from typing import List
from bs4 import BeautifulSoup
from app.core.config import settings
from app.core.logging import logger

DANGEROUS_ATTRIBUTES = [
    "onerror", "onload", "onclick", "onmouseover", "onfocus",
    "onblur", "onchange", "onsubmit", "onkeydown", "onkeypress",
    "onkeyup", "onmouseenter", "onmouseleave", "formaction",
]

DANGEROUS_PROTOCOLS = ["javascript:", "vbscript:", "data:text/html", "data:text/javascript"]

CSP_META_TAG = (
    '<meta http-equiv="Content-Security-Policy" '
    'content="default-src \'none\'; style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; '
    'img-src data: https:; font-src data: https:;">'
)


class ArtifactSanitizer:
    """
    Multi-layer defense-in-depth sanitizer for untrusted dynamically generated HTML/CSS/JS artifacts.
    Protects the host application against XSS, DOM breakout, cookie exfiltration, and unauthorized navigation.
    """

    # Prohibited script patterns attempting host DOM escape, parent navigation, or storage exfiltration
    PROHIBITED_PATTERNS = [
        re.compile(r"window\.top", re.IGNORECASE),
        re.compile(r"window\.parent", re.IGNORECASE),
        re.compile(r"parent\.location", re.IGNORECASE),
        re.compile(r"top\.location", re.IGNORECASE),
        re.compile(r"document\.cookie", re.IGNORECASE),
        re.compile(r"localStorage", re.IGNORECASE),
        re.compile(r"sessionStorage", re.IGNORECASE),
        re.compile(r"indexedDB", re.IGNORECASE),
    ]

    @classmethod
    def sanitize_html(cls, html_content: str) -> str:
        """
        Sanitize generated HTML content to prevent XSS and sandbox breakouts.
        """
        if not html_content or not html_content.strip():
            return ""

        if not settings.SANITIZE_ARTIFACT_HTML:
            return html_content

        # 1. Neutralize prohibited script breakout and exfiltration patterns
        clean_code = html_content
        for pattern in cls.PROHIBITED_PATTERNS:
            if pattern.search(clean_code):
                logger.warning(f"Unsafe breakout pattern detected in artifact: {pattern.pattern}")
                clean_code = pattern.sub("/* neutralized_forbidden_access */ undefined", clean_code)

        try:
            soup = BeautifulSoup(clean_code, "html.parser")

            # 2. Remove dangerous structural tags (applets, embeds, objects, frames, base tags)
            for tag in soup(["applet", "embed", "object", "frame", "frameset", "base"]):
                tag.decompose()

            # 3. Clean all element attributes for inline event handlers and dangerous protocols
            for tag in soup.find_all(True):
                # Remove dangerous event handler attributes
                attrs_to_remove = [
                    attr for attr in tag.attrs
                    if attr.lower().startswith("on") or attr.lower() in DANGEROUS_ATTRIBUTES
                ]
                for attr in attrs_to_remove:
                    logger.warning(f"Stripping dangerous attribute '{attr}' from tag <{tag.name}>")
                    del tag[attr]

                # Sanitize href and src attributes against dangerous URL protocols
                for url_attr in ["href", "src", "action", "data"]:
                    if tag.has_attr(url_attr):
                        val = str(tag[url_attr]).strip().lower()
                        if any(val.startswith(proto) for proto in DANGEROUS_PROTOCOLS):
                            logger.warning(f"Neutralizing dangerous protocol '{val}' in {url_attr}")
                            tag[url_attr] = "#neutralized-unsafe-link"

                # Enforce secure link targets
                if tag.name == "a" and tag.has_attr("href"):
                    tag["target"] = "_blank"
                    tag["rel"] = "noopener noreferrer"

            # 4. Inject strict Content Security Policy meta tag into head or document root
            if soup.head:
                if not soup.head.find("meta", attrs={"http-equiv": re.compile(r"content-security-policy", re.I)}):
                    csp_soup = BeautifulSoup(CSP_META_TAG, "html.parser")
                    soup.head.insert(0, csp_soup)
            elif soup.body or soup.find(True):
                # Wrap in standard HTML structure if not present
                csp_soup = BeautifulSoup(CSP_META_TAG, "html.parser")
                if soup.contents:
                    soup.insert(0, csp_soup)

            return str(soup)
        except Exception as e:
            logger.error(f"Failed to parse and sanitize HTML artifact: {e}")
            return clean_code


sanitizer = ArtifactSanitizer()
