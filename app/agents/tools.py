from app.services.analysis_service import AnalysisService


class PrismAgentTools:
    """
    Safe tool interface between the AI agent and PRISM's
    deterministic analytical services.

    The agent is allowed to request analysis through these
    methods, but analytical calculations remain owned by
    AnalysisService and the underlying analyzers.
    """

    def __init__(self, analysis_service: AnalysisService):
        self.analysis_service = analysis_service

    def get_project_predictive_summary(
        self,
        project_name: str,
    ) -> dict:
        result = self.analysis_service.analyze_project_predictive_summary(
            project_name
        )

        if result is None:
            return {
                "status": "not_found",
                "message": f"Project '{project_name}' was not found.",
                "data": None,
            }

        return {
            "status": "success",
            "data": result.model_dump(mode="json"),
        }

    def get_activity_predictive_summary(
        self,
        project_name: str,
        activity_name: str,
    ) -> dict:
        result = self.analysis_service.analyze_activity_predictive_summary(
            project_name,
            activity_name,
        )

        if result is None:
            return {
                "status": "not_found",
                "message": (
                    f"No predictive summary was found for activity "
                    f"'{activity_name}' in project '{project_name}'."
                ),
                "data": None,
            }

        return {
            "status": "success",
            "data": result.model_dump(mode="json"),
        }

    def get_activity_history(
        self,
        project_name: str,
        activity_name: str,
    ) -> dict:
        result = self.analysis_service.get_activity_history(
            project_name,
            activity_name,
        )

        if result is None:
            return {
                "status": "not_found",
                "message": (
                    f"No history was found for activity "
                    f"'{activity_name}' in project '{project_name}'."
                ),
                "data": None,
            }

        return {
            "status": "success",
            "data": result.model_dump(mode="json"),
        }