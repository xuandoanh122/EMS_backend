"""
Dashboard Controller – FastAPI router.

Endpoints:
  GET  /dashboard/stats   – Tổng hợp số liệu: tổng HS/GV/lớp,
                            danh sách HS/GV mới nhất (5 bản ghi).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import require_role
from app.core.response import APIResponse
from app.modules.dashboard.service import DashboardService

router = APIRouter(dependencies=[Depends(require_role("admin"))])


def get_service(session: AsyncSession = Depends(get_async_session)) -> DashboardService:
    return DashboardService(session)


@router.get(
    "/stats",
    status_code=200,
    summary="Thống kê tổng quan Dashboard",
    response_description=(
        "Trả về: total_students, total_teachers, total_classrooms, "
        "active_students, active_teachers, recent_students (5), recent_teachers (5)"
    ),
)
async def get_dashboard_stats(
    service: DashboardService = Depends(get_service),
) -> APIResponse:
    """
    Endpoint chạy 7 queries song song (asyncio.gather) để thu thập
    số liệu dashboard trong 1 request duy nhất.

    Response data:
    ```json
    {
      "total_students": 120,
      "total_teachers": 15,
      "total_classrooms": 8,
      "active_students": 110,
      "active_teachers": 13,
      "recent_students": [...],
      "recent_teachers": [...]
    }
    ```
    """
    stats = await service.get_stats()
    return APIResponse.success(
        data=stats,
        detail="Dashboard stats retrieved successfully",
    )
