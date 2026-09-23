from unittest.mock import Mock

import pytest

from app.agents.tool_registry import ToolRegistry


def test_registry_exposes_allowed_tool_names():
    tools = Mock()
    registry = ToolRegistry(tools)

    names = registry.get_tool_names()

    assert names == [
        "get_project_predictive_summary",
        "get_activity_predictive_summary",
        "get_activity_history",
    ]


def test_registry_executes_project_predictive_summary():
    tools = Mock()

    tools.get_project_predictive_summary.return_value = {
        "status": "success",
        "data": {
            "project_name": "Project Alpha",
        },
    }

    registry = ToolRegistry(tools)

    result = registry.execute(
        "get_project_predictive_summary",
        {
            "project_name": "Project Alpha",
        },
    )

    assert result == {
        "status": "success",
        "data": {
            "project_name": "Project Alpha",
        },
    }

    tools.get_project_predictive_summary.assert_called_once_with(
        project_name="Project Alpha"
    )


def test_registry_executes_activity_predictive_summary():
    tools = Mock()

    tools.get_activity_predictive_summary.return_value = {
        "status": "success",
        "data": {
            "project_name": "Project Alpha",
            "activity_name": "Foundation Work",
        },
    }

    registry = ToolRegistry(tools)

    result = registry.execute(
        "get_activity_predictive_summary",
        {
            "project_name": "Project Alpha",
            "activity_name": "Foundation Work",
        },
    )

    assert result["status"] == "success"

    tools.get_activity_predictive_summary.assert_called_once_with(
        project_name="Project Alpha",
        activity_name="Foundation Work",
    )


def test_registry_rejects_unknown_tool():
    tools = Mock()
    registry = ToolRegistry(tools)

    with pytest.raises(ValueError, match="Unknown tool"):
        registry.execute(
            "delete_project",
            {
                "project_name": "Project Alpha",
            },
        )


def test_registry_rejects_missing_required_arguments():
    tools = Mock()
    registry = ToolRegistry(tools)

    with pytest.raises(ValueError, match="Invalid arguments"):
        registry.execute(
            "get_activity_history",
            {
                "project_name": "Project Alpha",
            },
        )


def test_registry_rejects_extra_arguments():
    tools = Mock()
    registry = ToolRegistry(tools)

    with pytest.raises(ValueError, match="Invalid arguments"):
        registry.execute(
            "get_project_predictive_summary",
            {
                "project_name": "Project Alpha",
                "dangerous_argument": "something",
            },
        )


def test_registry_exposes_tool_schemas():
    tools = Mock()
    registry = ToolRegistry(tools)

    schemas = registry.get_tool_schemas()

    assert len(schemas) == 3

    first = schemas[0]

    assert first["name"] == "get_project_predictive_summary"
    assert "description" in first
    assert "parameters" in first

    assert (
        first["parameters"]["properties"]["project_name"]["type"]
        == "string"
    )