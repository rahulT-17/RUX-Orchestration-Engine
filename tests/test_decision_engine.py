import asyncio

from core.tool_response import ToolResponse, ToolStatus
from services.decision_engine import DecisionEngine


class DummyCriticService:
    def __init__(self):
        self.calls = 0

    async def critique(self, message, domain, task_type, result):
        self.calls += 1
        return '{"verdict": true, "severity": "low"}'


def test_critic_skips_successful_read_only_analyze():
    asyncio.run(_test_critic_skips_successful_read_only_analyze())


async def _test_critic_skips_successful_read_only_analyze():
    critic = DummyCriticService()
    engine = DecisionEngine(critic)

    result = ToolResponse(
        status=ToolStatus.SUCCESS,
        message="Total expense for food in this month: 20.0",
        data={"total": 20.0, "period": "this month", "category": "food"},
    )

    analysis = await engine.evaluate(
        user_id="u1",
        message="analyze food this month",
        domain="expense",
        task_type="analyze",
        result=result,
    )

    assert critic.calls == 0
    assert analysis["critic_analysis"] is None


def test_critic_runs_for_failed_action():
    asyncio.run(_test_critic_runs_for_failed_action())


async def _test_critic_runs_for_failed_action():
    critic = DummyCriticService()
    engine = DecisionEngine(critic)

    result = ToolResponse(
        status=ToolStatus.FAILED,
        message="Expense rejected. Budget exceeded.",
        error="Budget exceeded",
    )

    analysis = await engine.evaluate(
        user_id="u1",
        message="log 1000 food",
        domain="expense",
        task_type="log",
        result=result,
    )

    assert critic.calls == 1
    assert analysis["critic_analysis"] is not None


def test_critic_runs_for_successful_high_risk_delete():
    asyncio.run(_test_critic_runs_for_successful_high_risk_delete())


async def _test_critic_runs_for_successful_high_risk_delete():
    critic = DummyCriticService()
    engine = DecisionEngine(critic)

    result = ToolResponse(
        status=ToolStatus.SUCCESS,
        message="Project deleted successfully.",
        data={"project_id": 1},
    )

    analysis = await engine.evaluate(
        user_id="u1",
        message="delete project id 1",
        domain="project",
        task_type="delete_project",
        result=result,
    )

    assert critic.calls == 1
    assert analysis["critic_analysis"] is not None
