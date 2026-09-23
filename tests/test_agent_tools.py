from unittest.mock import Mock

from app.agents.tools import PrismAgentTools


class FakeModel:
    """
    Minimal fake Pydantic-like model used only for testing
    PrismAgentTools serialization behavior.
    """

    def model_dump(self, mode=None):
        return {
            "project_name": "Project Alpha",
            "total_activity_count": 3,
        }


def test_project_predictive_summary_returns_not_found():
    service = Mock()
    service.analyze_project_predictive_summary.return_value = None

    tools = PrismAgentTools(service)

    result = tools.get_project_predictive_summary(
        "Unknown Project"
    )

    assert result["status"] == "not_found"
    assert result["data"] is None

    service.analyze_project_predictive_summary.assert_called_once_with(
        "Unknown Project"
    )


def test_activity_predictive_summary_returns_not_found():
    service = Mock()
    service.analyze_activity_predictive_summary.return_value = None

    tools = PrismAgentTools(service)

    result = tools.get_activity_predictive_summary(
        "Project Alpha",
        "Unknown Activity",
    )

    assert result["status"] == "not_found"
    assert result["data"] is None

    service.analyze_activity_predictive_summary.assert_called_once_with(
        "Project Alpha",
        "Unknown Activity",
    )


def test_activity_history_returns_not_found():
    service = Mock()
    service.get_activity_history.return_value = None

    tools = PrismAgentTools(service)

    result = tools.get_activity_history(
        "Project Alpha",
        "Unknown Activity",
    )

    assert result["status"] == "not_found"
    assert result["data"] is None

    service.get_activity_history.assert_called_once_with(
        "Project Alpha",
        "Unknown Activity",
    )


def test_project_predictive_summary_serializes_result():
    service = Mock()
    service.analyze_project_predictive_summary.return_value = FakeModel()

    tools = PrismAgentTools(service)

    result = tools.get_project_predictive_summary(
        "Project Alpha"
    )

    assert result == {
        "status": "success",
        "data": {
            "project_name": "Project Alpha",
            "total_activity_count": 3,
        },
    }

    service.analyze_project_predictive_summary.assert_called_once_with(
        "Project Alpha"
    )