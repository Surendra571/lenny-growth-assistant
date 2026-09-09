import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent.providers.fake_provider import FakeLLMProvider
from app.agent.skills.ship30_skill import Ship30Skill
from app.repositories.session_repository import SessionRepository
from app.services.artifact_service import ArtifactService


@pytest.mark.asyncio
async def test_ship30_to_artifact_persistence(db_session: AsyncSession):
    # 1. Create session
    session = await SessionRepository.create(db=db_session, title="Ship 30 to Artifact Test")
    fake_llm = FakeLLMProvider()

    # 2. Generate Ship 30 essay
    ship30_result = await Ship30Skill.generate_essay(
        db=db_session,
        session_id=session.id,
        topic="How did Superhuman measure product market fit with Rahul Vohra?",
        llm_provider=fake_llm,
    )

    assert ship30_result.metadata["status"] == "success"

    # 3. Persist as Markdown artifact
    artifact = await ArtifactService.create_from_ship30(
        db=db_session,
        session_id=session.id,
        ship30_res=ship30_result,
    )

    assert artifact.session_id == session.id
    assert artifact.title == ship30_result.title
    assert artifact.artifact_type == "markdown"
    assert artifact.content == ship30_result.content
    assert artifact.version == 1
    assert artifact.metadata["skill"] == "ship30"
    assert artifact.metadata["word_count"] == ship30_result.word_count
    assert len(artifact.metadata["sources"]) > 0

    # 4. Verify artifact listing for the session
    session_artifacts = await ArtifactService.list_session_artifacts(db=db_session, session_id=session.id)
    assert len(session_artifacts) == 1
    assert session_artifacts[0].id == artifact.id

