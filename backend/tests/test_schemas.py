import uuid
from datetime import datetime, timezone
from app.schemas.health import HealthResponse
from app.schemas.message import MessageCreate, SourceCitation
from app.schemas.session import SessionCreate, SessionResponse
from app.schemas.artifact import ArtifactCreate, ArtifactResponse


def test_session_schemas():
    create_payload = SessionCreate(title="Growth Frameworks")
    assert create_payload.title == "Growth Frameworks"

    session_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    response_payload = SessionResponse(
        id=session_id,
        title="Growth Frameworks",
        created_at=now,
        updated_at=now,
        message_count=2,
    )
    assert response_payload.id == session_id
    assert response_payload.message_count == 2


def test_source_citation_schema():
    citation = SourceCitation(
        episode_title="Rahul Vohra on Finding PMF",
        guest_name="Rahul Vohra",
        relevance_score=0.89,
        snippet="We asked how disappointed users would be if Superhuman disappeared.",
    )
    assert citation.guest_name == "Rahul Vohra"
    assert citation.relevance_score == 0.89


def test_artifact_schema():
    art_payload = ArtifactCreate(
        session_id=uuid.uuid4(),
        title="PMF Calculator",
        artifact_type="html",
        content="<div>Interactive PMF Calculator</div>",
    )
    assert art_payload.artifact_type == "html"
    assert "PMF Calculator" in art_payload.content

