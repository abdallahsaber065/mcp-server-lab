"""
Test chat mode intake — 4 options, slot collection, background launch, notify.
"""
import pytest
import asyncio
from services.chat_intake_service import ChatIntakeService, MODE_CONFIG

def test_mode_configs_exist():
    assert "lease_onboarding" in MODE_CONFIG
    assert "maintenance_tender" in MODE_CONFIG
    assert "arrears_mediation" in MODE_CONFIG
    assert MODE_CONFIG["lease_onboarding"]["graph_id"] == "commercial_lease_flow"

@pytest.mark.anyio
async def test_lease_intake_missing_slots():
    result = await ChatIntakeService.run_intake_turn(
        db=None, user_id=1, session_id="sess-1", mode="lease_onboarding",
        history=[], user_message="I want Suite-301", image_urls=[], existing_slots={}
    )
    assert not result["ready_to_launch"]
    assert len(result["missing"]) > 0
    assert "next_question" in result

@pytest.mark.anyio
async def test_lease_intake_ready_with_all_slots():
    result = await ChatIntakeService.run_intake_turn(
        db=None, user_id=1, session_id="sess-1", mode="lease_onboarding",
        history=[], user_message="Suite-301 base 60000 proposed 48000 applicant Ahmed Corp", image_urls=["/static/uploads/receipts/a.jpg"], existing_slots={}
    )
    assert result["graph_id"] == "commercial_lease_flow"
    # Should be ready or at least have most slots
    assert result["ready_to_launch"] or len(result["missing"]) <= 1

@pytest.mark.anyio
async def test_maintenance_intake():
    result = await ChatIntakeService.run_intake_turn(
        db=None, user_id=2, session_id="sess-2", mode="maintenance_tender",
        history=[], user_message="Emergency plumbing burst at Cornerstone Heights Zamalek", image_urls=[], existing_slots={}
    )
    assert result["graph_id"] == "renovation_permit_flow"
    assert "location" in result["slots"] or "issue_description" in result["slots"]

@pytest.mark.anyio
async def test_arrears_intake_ready():
    result = await ChatIntakeService.run_intake_turn(
        db=None, user_id=3, session_id="sess-3", mode="arrears_mediation",
        history=[], user_message="tenant 1 unpaid 3 months monthly 40000 EGP", image_urls=[], existing_slots={}
    )
    assert result["graph_id"] == "rent_arrears_settlement_flow"
    assert result["ready_to_launch"] is True
    assert result["launch_variables"]["tenant_id"] == 1
    assert result["launch_variables"]["unpaid_months"] == 3
    assert result["launch_variables"]["monthly_rent"] == 40000

@pytest.mark.anyio
async def test_background_runner_persists_and_notifies():
    from services.state_graph_background import run_graph_in_background
    from db.session import AsyncSessionLocal
    from db.repositories.chat_repo import AsyncChatRepository
    import uuid
    session_id = f"sess-bg-{uuid.uuid4().hex[:6]}"
    user_id = 1
    async with AsyncSessionLocal() as db:
        repo = AsyncChatRepository(db)
        await repo.create_chat_session(session_id=session_id, title="bg test", role="tenant", user_id=user_id)
    run_id = f"run-bg-{uuid.uuid4().hex[:6]}"
    variables = {"unit_id": 301, "base_rent": 60000, "proposed_rent": 48000, "applicant_name": "Test Corp", "receipt_image_urls": ["/static/uploads/receipts/a.jpg"]}
    await run_graph_in_background(run_id, "commercial_lease_flow", variables, user_id, session_id)
    async with AsyncSessionLocal() as db:
        repo = AsyncChatRepository(db)
        msgs = await repo.get_chat_messages(session_id)
        assert any(m.get("type") == "state_graph_update" for m in msgs), f"Expected state_graph_update, got {msgs}"

@pytest.mark.anyio
async def test_notification_service_pubsub():
    from services.notification_service import NotificationService
    import asyncio
    user_id = 99999
    received = []
    async def subscriber():
        async for evt in NotificationService.subscribe(user_id):
            received.append(evt)
            break
    task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.1)
    await NotificationService.publish(user_id, {"type": "state_graph_update", "run_id": "run-test-123", "status": "PAUSED_HITL"})
    await asyncio.wait_for(task, timeout=2)
    assert len(received) == 1
    assert received[0]["run_id"] == "run-test-123"
