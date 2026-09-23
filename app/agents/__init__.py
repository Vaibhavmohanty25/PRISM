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

    