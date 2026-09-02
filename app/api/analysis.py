from fastapi import APIRouter, Depends, HTTPException

from app.schemas.project_data import (
    ActivityInsight,
    ActivityIssueHistory,
    ActivityHistory,
    ActivityScheduleImpact,
    ActivityScheduleImpactHistory,
    ProjectScheduleImpact,
    ProjectScheduleImpactHistory,
    ProjectInsight,
    ProjectIssueHistory,
    RiskResult,
    TrendResult,
)
from app.services.analysis_service import (
    AnalysisService,
    get_analysis_service,
)
from app.schemas.api import ProjectsResponse


router = APIRouter(
    prefix="/api/v1",
    tags=["Analysis"],
)


def _require_project(
    service: AnalysisService,
    project_name: str,
) -> None:
    if project_name not in service.get_projects():
        raise HTTPException(
            status_code=404,
            detail=f"Unknown project: {project_name}",
        )


@router.get("/projects", response_model=ProjectsResponse)
def get_projects(
    service: AnalysisService = Depends(get_analysis_service),
) -> ProjectsResponse:
    return {"projects": service.get_projects()}


@router.get(
    "/projects/{project_name}/activities/{activity_name}/history",
    response_model=ActivityHistory,
)
def get_activity_history(
    project_name: str,
    activity_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> ActivityHistory:
    _require_project(service, project_name)
    history = service.get_activity_history(
        project_name,
        activity_name,
    )

    if history is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown activity: {activity_name}",
        )

    return history


@router.get(
    "/projects/{project_name}/trends",
    response_model=list[TrendResult],
)
def get_project_trends(
    project_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> list[TrendResult]:
    _require_project(service, project_name)
    return service.analyze_project_trends(project_name)


@router.get(
    "/projects/{project_name}/activities/{activity_name}/trend",
    response_model=TrendResult,
)
def get_activity_trend(
    project_name: str,
    activity_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> TrendResult:
    _require_project(service, project_name)
    result = service.analyze_activity_trend(
        project_name,
        activity_name,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown activity: {activity_name}",
        )

    return result


@router.get(
    "/projects/{project_name}/risks",
    response_model=list[RiskResult],
)
def get_project_risks(
    project_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> list[RiskResult]:
    _require_project(service, project_name)
    return service.analyze_project_risks(project_name)


@router.get(
    "/projects/{project_name}/activities/{activity_name}/risk",
    response_model=RiskResult,
)
def get_activity_risk(
    project_name: str,
    activity_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> RiskResult:
    _require_project(service, project_name)
    result = service.analyze_activity_risk(
        project_name,
        activity_name,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown activity: {activity_name}",
        )

    return result


@router.get(
    "/projects/{project_name}/insights",
    response_model=ProjectInsight,
)
def get_project_insights(
    project_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> ProjectInsight:
    _require_project(service, project_name)
    result = service.analyze_project_insight(project_name)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown project: {project_name}",
        )

    return result


@router.get(
    "/projects/{project_name}/activities/{activity_name}/insight",
    response_model=ActivityInsight,
)
def get_activity_insight(
    project_name: str,
    activity_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> ActivityInsight:
    _require_project(service, project_name)
    result = service.analyze_activity_insight(
        project_name,
        activity_name,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown activity: {activity_name}",
        )

    return result


@router.get(
    "/projects/{project_name}/schedule-impact",
    response_model=ProjectScheduleImpact,
)
def get_project_schedule_impact(
    project_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> ProjectScheduleImpact:
    _require_project(service, project_name)
    result = service.analyze_project_schedule_impact(project_name)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown project: {project_name}",
        )

    return result


@router.get(
    "/projects/{project_name}/schedule-impact/history",
    response_model=ProjectScheduleImpactHistory,
)
def get_project_schedule_impact_history(
    project_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> ProjectScheduleImpactHistory:
    _require_project(service, project_name)
    result = service.analyze_project_schedule_impact_history(project_name)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown project: {project_name}",
        )

    return result


@router.get(
    "/projects/{project_name}/activities/{activity_name}/schedule-impact",
    response_model=ActivityScheduleImpact,
)
def get_activity_schedule_impact(
    project_name: str,
    activity_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> ActivityScheduleImpact:
    _require_project(service, project_name)
    result = service.analyze_activity_schedule_impact(
        project_name,
        activity_name,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown activity: {activity_name}",
        )

    return result


@router.get(
    "/projects/{project_name}/activities/{activity_name}/schedule-impact/history",
    response_model=ActivityScheduleImpactHistory,
)
def get_activity_schedule_impact_history(
    project_name: str,
    activity_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> ActivityScheduleImpactHistory:
    _require_project(service, project_name)
    result = service.analyze_activity_schedule_impact_history(
        project_name,
        activity_name,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown activity: {activity_name}",
        )

    return result


@router.get(
    "/projects/{project_name}/issues/history",
    response_model=ProjectIssueHistory,
)
def get_project_issue_history(
    project_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> ProjectIssueHistory:
    _require_project(service, project_name)
    result = service.analyze_project_issue_history(project_name)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown project: {project_name}",
        )

    return result


@router.get(
    "/projects/{project_name}/activities/{activity_name}/issues/history",
    response_model=ActivityIssueHistory,
)
def get_activity_issue_history(
    project_name: str,
    activity_name: str,
    service: AnalysisService = Depends(get_analysis_service),
) -> ActivityIssueHistory:
    _require_project(service, project_name)
    result = service.analyze_activity_issue_history(
        project_name,
        activity_name,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown activity: {activity_name}",
        )

    return result
