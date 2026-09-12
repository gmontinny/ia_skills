import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from main import app
from src.domain.skill import Skill, SkillMetadata

MOCK_SKILL = Skill(
    id="lgpd-brasil",
    metadata=SkillMetadata(
        name="lgpd-brasil",
        description="Orienta sobre a LGPD",
        status="stable",
    ),
    content="---\nname: lgpd-brasil\ndescription: Orienta sobre a LGPD\nstatus: stable\n---\n\n# LGPD\n\nConteúdo da skill.",
    gitlab_path="skills/lgpd-brasil/SKILL.md",
)


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_skills_endpoint():
    with patch(
        "src.api.routes.SkillRegistry.get_all",
        new_callable=AsyncMock,
        return_value={"lgpd-brasil": MOCK_SKILL},
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/skills")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["skills"][0]["id"] == "lgpd-brasil"
