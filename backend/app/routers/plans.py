from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
import asyncio

from app.database import get_db
from app.models import Employee, Department, AssessmentPlan, AssessmentRecord, EvalTemplate, RecordStatus
from app.routers.auth import UserInfo, get_login_user
from app.permissions import require_hr_user, require_admin_user
from app.services.wecom import wecom_service
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/api", tags=["业务"])


# ── 考核计划 ──

class PlanCreate(BaseModel):
    name: str
    cycle_type: str
    start_date: str
    end_date: str
    self_eval_start: Optional[str] = None
    self_eval_end: Optional[str] = None
    manager_eval_end: Optional[str] = None
    template_id: int
    approval_chain: list[str]
    dept_ids: Optional[list[int]] = None


@router.get("/plans")
def list_plans(user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    stmt = select(AssessmentPlan).order_by(AssessmentPlan.created_at.desc())
    plans = db.execute(stmt).scalars().all()
    return [
        {
            "id": p.id, "name": p.name, "cycle_type": p.cycle_type,
            "status": p.status, "start_date": str(p.start_date),
            "end_date": str(p.end_date),
            "self_eval_end": str(p.self_eval_end) if p.self_eval_end else None,
        }
        for p in plans
    ]


@router.post("/plans")
async def create_plan(body: PlanCreate, user: UserInfo = Depends(require_hr_user), db: Session = Depends(get_db)):
    plan = AssessmentPlan(
        name=body.name, cycle_type=body.cycle_type,
        start_date=body.start_date, end_date=body.end_date,
        self_eval_start=body.self_eval_start, self_eval_end=body.self_eval_end,
        manager_eval_end=body.manager_eval_end,
        template_id=body.template_id, approval_chain=body.approval_chain,
        status="running", created_by=user.id,
    )
    db.add(plan)
    db.flush()

    stmt = select(Employee).where(Employee.status == "active")
    if body.dept_ids:
        stmt = stmt.where(Employee.dept_id.in_(body.dept_ids))
    employees = db.execute(stmt).scalars().all()

    # 创建考核记录
    for emp in employees:
        record = AssessmentRecord(
            plan_id=plan.id, employee_id=emp.id,
            status=RecordStatus.PENDING.value, current_step="self_eval",
        )
        db.add(record)
    db.flush()

    # 异步推送企微消息给所有员工
    async def send_notifications():
        for emp in employees:
            try:
                # 构造消息内容
                self_eval_end_str = body.self_eval_end if body.self_eval_end else "待定"
                description = f"考核周期：{body.cycle_type}\n自评截止时间：{self_eval_end_str}\n请及时完成自评"

                await wecom_service.send_textcard(
                    touser=emp.wecom_userid,
                    title=f"新考核通知：{body.name}",
                    description=description,
                    url=f"{settings.APP_BASE_URL}/employee/assessments"
                )
            except Exception as e:
                # 记录错误但不影响主流程
                import logging
                logging.error(f"发送消息给 {emp.name} 失败: {str(e)}")

    # 在后台执行消息推送
    asyncio.create_task(send_notifications())

    return {"id": plan.id, "message": f"考核计划已创建，覆盖 {len(employees)} 人，正在推送通知"}



# ── 我的考核 ──

@router.get("/my/assessments")
def my_assessments(user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    stmt = (
        select(AssessmentRecord, AssessmentPlan.name, AssessmentPlan.cycle_type)
        .join(AssessmentPlan, AssessmentRecord.plan_id == AssessmentPlan.id)
        .where(AssessmentRecord.employee_id == user.id)
        .order_by(AssessmentRecord.created_at.desc())
    )
    rows = db.execute(stmt).all()
    return [
        {
            "id": r[0].id, "plan_name": r[1], "cycle_type": r[2],
            "status": r[0].status, "current_step": r[0].current_step,
            "final_score": r[0].final_score,
        }
        for r in rows
    ]


# ── 模板 ──

class TemplateCreate(BaseModel):
    name: str
    type: str
    dimensions: list[dict]


@router.get("/templates")
def list_templates(db: Session = Depends(get_db)):
    stmt = select(EvalTemplate).order_by(EvalTemplate.created_at.desc())
    templates = db.execute(stmt).scalars().all()
    return [
        {"id": t.id, "name": t.name, "type": t.type, "dimensions": t.dimensions_json, "is_default": t.is_default}
        for t in templates
    ]


@router.post("/templates")
def create_template(body: TemplateCreate, user: UserInfo = Depends(require_hr_user), db: Session = Depends(get_db)):
    template = EvalTemplate(name=body.name, type=body.type, dimensions_json=body.dimensions, created_by=user.id)
    db.add(template)
    db.flush()
    return {"id": template.id, "message": "模板已创建"}


# ── 数据概览 ──

@router.get("/dashboard/overview")
def dashboard_overview(user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    total_employees = db.execute(select(func.count(Employee.id)).where(Employee.status == "active")).scalar()
    total_depts = db.execute(select(func.count(Department.id))).scalar()
    active_plans = db.execute(select(func.count(AssessmentPlan.id)).where(AssessmentPlan.status == "running")).scalar()
    return {"total_employees": total_employees, "total_departments": total_depts, "active_plans": active_plans}
