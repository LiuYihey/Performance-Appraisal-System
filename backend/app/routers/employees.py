from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import Employee, Department, AssessmentRecord, RecordStatus
from app.routers.auth import UserInfo, get_login_user
from app.services.wecom import wecom_service

router = APIRouter(prefix="/api", tags=["组织架构"])


@router.get("/employees")
def list_employees(keyword: str = "", dept_id: Optional[int] = None, status: str = "active", page: int = 1, page_size: int = 50, user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    stmt = select(Employee)
    if keyword:
        stmt = stmt.where(Employee.name.contains(keyword))
    if dept_id:
        stmt = stmt.where(Employee.dept_id == dept_id)
    if status:
        stmt = stmt.where(Employee.status == status)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar()
    items = db.execute(stmt.offset((page - 1) * page_size).limit(page_size).order_by(Employee.id)).scalars().all()
    return {"total": total, "page": page, "items": [{"id": e.id, "name": e.name, "wecom_userid": e.wecom_userid, "dept_id": e.dept_id, "position": e.position, "level": e.level, "status": e.status, "direct_leader_id": e.direct_leader_id} for e in items]}


@router.get("/employees/subordinates")
def list_subordinates(user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    employees = db.execute(select(Employee).where(Employee.direct_leader_id == user.id, Employee.status == "active").order_by(Employee.id)).scalars().all()
    items = []
    for e in employees:
        dept_name = None
        if e.dept_id:
            dept_name = db.execute(select(Department.name).where(Department.id == e.dept_id)).scalar()
        items.append({"id": e.id, "name": e.name, "wecom_userid": e.wecom_userid, "dept_id": e.dept_id, "dept_name": dept_name, "position": e.position, "level": e.level, "status": e.status})
    return items


@router.get("/departments")
def list_departments(user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    depts = db.execute(select(Department).order_by(Department.id)).scalars().all()
    return [{"id": d.id, "name": d.name, "parent_id": d.parent_id, "leader_id": d.leader_id} for d in depts]


@router.post("/sync/departments")
async def sync_departments(user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    if user.role not in ("admin", "hr"):
        raise HTTPException(403, "仅管理员可操作")
    try:
        dept_list = await wecom_service.get_department_list()
        count = 0
        for d in dept_list:
            existing = db.execute(select(Department).where(Department.id == d["id"])).scalar_one_or_none()
            if not existing:
                db.add(Department(id=d["id"], name=d["name"], parent_id=d.get("parentid")))
                count += 1
        db.flush()
        return {"message": f"同步完成，新增 {count} 个部门", "total": len(dept_list)}
    except Exception as e:
        raise HTTPException(500, f"同步失败: {str(e)}")


@router.post("/sync/employees")
async def sync_employees(user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    if user.role not in ("admin", "hr"):
        raise HTTPException(403, "仅管理员可操作")
    try:
        dept_list = await wecom_service.get_department_list()
        count = 0
        for dept in dept_list:
            users = await wecom_service.get_department_users(dept["id"])
            for u in users:
                userid = u.get("userid")
                if not userid:
                    continue
                existing = db.execute(select(Employee).where(Employee.wecom_userid == userid)).scalar_one_or_none()
                if not existing:
                    db.add(Employee(name=u.get("name", userid), wecom_userid=userid, dept_id=u.get("department"), position=u.get("position"), avatar=u.get("avatar"), phone=u.get("mobile"), status="active"))
                    count += 1
        db.flush()
        return {"message": f"同步完成，新增 {count} 名员工"}
    except Exception as e:
        raise HTTPException(500, f"同步失败: {str(e)}")
