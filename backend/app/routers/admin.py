"""
系统管理路由
包括组织架构同步等管理功能
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import UserInfo
from app.permissions import require_admin_user
from app.services.sync import sync_service, run_full_sync

router = APIRouter(prefix="/api/admin", tags=["系统管理"])


@router.post("/sync/departments")
async def sync_departments(
    user: UserInfo = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    同步企业微信部门
    需要管理员权限
    """
    count = await sync_service.sync_departments(db)
    return {"message": f"同步完成，新增 {count} 个部门"}


@router.post("/sync/employees")
async def sync_all_employees(
    background_tasks: BackgroundTasks,
    user: UserInfo = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    同步所有员工（后台任务）
    需要管理员权限
    """
    # 在后台执行同步任务
    background_tasks.add_task(run_full_sync)
    return {"message": "同步任务已启动，将在后台执行"}


@router.post("/sync/department/{dept_id}/employees")
async def sync_department_employees(
    dept_id: int,
    user: UserInfo = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    同步指定部门的员工
    需要管理员权限
    """
    count = await sync_service.sync_employees_in_department(db, dept_id)
    return {"message": f"同步完成，新增 {count} 名员工"}


@router.post("/sync/leader-relationships")
async def update_leader_relationships(
    user: UserInfo = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    更新员工上下级关系
    需要管理员权限
    """
    await sync_service.update_leader_relationships(db)
    return {"message": "上下级关系更新完成"}


@router.get("/sync/status")
async def get_sync_status(
    user: UserInfo = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取同步状态统计
    需要管理员权限
    """
    from app.models import Department, Employee
    from sqlalchemy import select, func

    dept_count = db.execute(select(func.count(Department.id))).scalar()
    emp_count = db.execute(select(func.count(Employee.id))).scalar()
    active_emp_count = db.execute(
        select(func.count(Employee.id)).where(Employee.status == "active")
    ).scalar()

    return {
        "departments": dept_count,
        "employees": emp_count,
        "active_employees": active_emp_count
    }
