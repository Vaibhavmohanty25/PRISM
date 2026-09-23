from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_agent_query_endpoint_returns_agent_result():
    original_agent = app.state.agent

    mock_agent = Mock()

    mock_agent.run.return_value = {
        "answer": "Project Alpha requires additional evidence.",
        "tools_used": [
            "get_project_predictive_summary",
        ],
        "iterations": 2,
    }

    app.state.agent = mock_agent

    try:
        response = client.post(
            "/api/v1/agent/query",
            json={
                "query": (
                    "Give me the predictive status "
                    "of Project Alpha."
                )
            },
        )

        assert response.status_code == 200

        assert response.json() == {
            "answer": (
                "Project Alpha requires additional evidence."
            ),
            "tools_used": [
                "get_project_predictive_summary",
            ],
            "iterations": 2,
        }

        mock_agent.run.assert_called_once_with(
            "Give me the predictive status of Project Alpha."
        )

    finally:
        app.state.agent = original_agent


def test_agent_query_rejects_empty_query():
    response = client.post(
        "/api/v1/agent/query",
        json={
            "query": "",
        },
    )

    assert response.status_code == 400


def test_agent_query_requires_query_field():
    response = client.post(
        "/api/v1/agent/query",
        json={},
    )

    assert response.status_code == 400

def test_agent_query_normalizes_unicode_typography():
    original_agent = app.state.agent

    mock_agent = Mock()

    mock_agent.run.return_value = {
        "answer": (
            "Project\u202fAlpha has "
            "predictive\u2011risk evidence."
        ),
        "tools_used": [],
        "iterations": 1,
    }

    app.state.agent = mock_agent

    try:
        response = client.post(
            "/api/v1/agent/query",
            json={
                "query": "Analyze Project Alpha."
            },
        )

        assert response.status_code == 200

        assert response.json()["answer"] == (
            "Project Alpha has predictive-risk evidence."
        )

    finally:
        app.state.agent = original_agent