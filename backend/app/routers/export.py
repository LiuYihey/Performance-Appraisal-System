"""
报表导出路由
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.routers.auth import UserInfo
from app.permissions import require_hr_user, require_manager_user
from app.services.export import export_service

router = APIRouter(prefix="/api/export", tags=["报表导出"])


@router.get("/records")
async def export_records(
    plan_id: int = None,
    user: UserInfo = Depends(require_hr_user),
    db: Session = Depends(get_db)
):
    """
    导出考核记录列表
    需要HR或管理员权限
    """
    try:
        output = export_service.export_assessment_records(db, plan_id)
        filename = f"考核记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/record/{record_id}")
async def export_record_detail(
    record_id: int,
    user: UserInfo = Depends(require_manager_user),
    db: Session = Depends(get_db)
):
    """
    导出单个考核详情
    需要经理、HR或管理员权限
    """
    try:
        output = export_service.export_assessment_detail(db, record_id)
        filename = f"考核详情_{record_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/plan/{plan_id}/summary")
async def export_plan_summary(
    plan_id: int,
    user: UserInfo = Depends(require_hr_user),
    db: Session = Depends(get_db)
):
    """
    导出考核计划汇总报表
    需要HR或管理员权限
    """
    try:
        output = export_service.export_plan_summary(db, plan_id)
        filename = f"考核汇总_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
