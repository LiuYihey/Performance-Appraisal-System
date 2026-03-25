from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
import io
import csv
from datetime import datetime

from app.database import get_db
from app.models import (
    Employee, Department, AssessmentPlan, AssessmentRecord,
    EvalDetail, EvalTemplate, ApprovalLog, RecordStatus,
)
from app.routers.auth import UserInfo, get_login_user

router = APIRouter(prefix="/api", tags=["HR管理"])


# ── VP 审批 ──

class VPApproveBody(BaseModel):
    record_id: int
    action: str = "approve"
    comment: Optional[str] = None


@router.post("/eval/vp")
def vp_approve(body: VPApproveBody, user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    record = db.execute(select(AssessmentRecord).where(AssessmentRecord.id == body.record_id)).scalar_one_or_none()
    if not record:
        raise HTTPException(404, "考核记录不存在")

    if body.action == "return":
        record.status = RecordStatus.RETURNED.value
        record.current_step = "self_eval"
        db.add(ApprovalLog(record_id=record.id, from_step="vp_approval", to_step="self_eval", approver_id=user.id, action="return", comment=body.comment or "VP 退回"))
        db.flush()
        return {"message": "已退回"}

    record.status = RecordStatus.VP_APPROVED.value
    record.current_step = "hr_final"
    db.add(ApprovalLog(record_id=record.id, from_step="vp_approval", to_step="hr_final", approver_id=user.id, action="approve", comment=body.comment or "VP 审批通过"))
    db.flush()
    return {"message": "VP 审批通过", "next_step": "hr_final"}


# ── 管理者待审批 ──

@router.get("/manager/pending-evals")
def manager_pending_evals(user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    sub_ids = [r[0] for r in db.execute(select(Employee.id).where(Employee.direct_leader_id == user.id, Employee.status == "active")).all()]
    if not sub_ids:
        return []
    rows = db.execute(
        select(AssessmentRecord, Employee.name, AssessmentPlan.name)
        .join(Employee, AssessmentRecord.employee_id == Employee.id)
        .join(AssessmentPlan, AssessmentRecord.plan_id == AssessmentPlan.id)
        .where(AssessmentRecord.employee_id.in_(sub_ids),
               AssessmentRecord.status.in_([RecordStatus.SELF_EVAL_SUBMITTED.value, RecordStatus.RETURNED.value, RecordStatus.MANAGER_EVAL_SUBMITTED.value]))
        .order_by(AssessmentRecord.created_at.desc())
    ).all()
    return [{"id": r[0].id, "employee_id": r[0].employee_id, "employee_name": r[1], "plan_name": r[2], "status": r[0].status, "current_step": r[0].current_step, "final_score": r[0].final_score} for r in rows]


# ── HR 待终审 ──

@router.get("/hr/pending-reviews")
def hr_pending_reviews(user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(AssessmentRecord, Employee.name, AssessmentPlan.name, AssessmentPlan.cycle_type)
        .join(Employee, AssessmentRecord.employee_id == Employee.id)
        .join(AssessmentPlan, AssessmentRecord.plan_id == AssessmentPlan.id)
        .where(AssessmentRecord.status.in_([RecordStatus.MANAGER_EVAL_SUBMITTED.value, RecordStatus.VP_APPROVED.value]))
        .order_by(AssessmentRecord.created_at.desc())
    ).all()

    items = []
    for r in rows:
        record = r[0]
        details = db.execute(select(EvalDetail).where(EvalDetail.record_id == record.id)).scalars().all()
        final_score = None
        self_scores = [d.score for d in details if d.evaluator_role == "self" and d.score is not None]
        mgr_scores = [d.score for d in details if d.evaluator_role == "manager" and d.score is not None]
        if self_scores and mgr_scores:
            weights = {}
            for d in details:
                if d.dimension_name not in weights:
                    weights[d.dimension_name] = {"self": None, "manager": None, "weight": d.dimension_weight}
                if d.evaluator_role == "self" and d.score is not None:
                    weights[d.dimension_name]["self"] = d.score
                elif d.evaluator_role == "manager" and d.score is not None:
                    weights[d.dimension_name]["manager"] = d.score
            total = sum((s["self"] * 0.3 + s["manager"] * 0.7) * s["weight"] / 100 for s in weights.values())
            final_score = round(total, 1)
        items.append({"id": record.id, "employee_id": record.employee_id, "employee_name": r[1], "plan_name": r[2], "cycle_type": r[3], "status": record.status, "current_step": record.current_step, "final_score": final_score})
    return items


# ── 仪表盘详细统计 ──

@router.get("/dashboard/detail")
def dashboard_detail(user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    running_plans = db.execute(select(AssessmentPlan).where(AssessmentPlan.status == "running")).scalars().all()
    plan_stats = []
    for plan in running_plans:
        total = db.execute(select(func.count(AssessmentRecord.id)).where(AssessmentRecord.plan_id == plan.id)).scalar()
        done = db.execute(select(func.count(AssessmentRecord.id)).where(AssessmentRecord.plan_id == plan.id, AssessmentRecord.status.in_([RecordStatus.LOCKED.value, RecordStatus.HR_APPROVED.value]))).scalar()
        plan_stats.append({"name": plan.name, "total": total or 0, "done": done or 0, "percent": round(done / total * 100) if total else 0})

    submitted = db.execute(select(func.count(AssessmentRecord.id)).where(AssessmentRecord.status != RecordStatus.PENDING.value)).scalar() or 0

    dept_rows = db.execute(
        select(Department.name, func.count(AssessmentRecord.id).label("count"), func.avg(AssessmentRecord.final_score).label("avg_score"))
        .join(Employee, Employee.dept_id == Department.id, isouter=True)
        .join(AssessmentRecord, AssessmentRecord.employee_id == Employee.id, isouter=True)
        .where(AssessmentRecord.final_score.isnot(None))
        .group_by(Department.id)
    ).all()
    dept_stats = [{"name": r[0], "count": r[1], "avg_score": round(r[2], 1) if r[2] else None} for r in dept_rows]

    log_rows = db.execute(select(ApprovalLog, Employee.name).join(Employee, ApprovalLog.approver_id == Employee.id).order_by(ApprovalLog.created_at.desc()).limit(10)).all()
    recent_logs = [{"content": f"{r[1]} {r[0].action} 了 {r[0].to_step or '操作'}", "time": str(r[0].created_at)} for r in log_rows]

    return {"plan_stats": plan_stats, "submitted_count": submitted, "dept_stats": dept_stats, "recent_logs": recent_logs}


# ── 数据导出 ──

@router.get("/hr/export/preview")
def export_preview(plan_id: int = Query(...), dept_id: Optional[int] = Query(None), user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    stmt = (
        select(AssessmentRecord, Employee.name, Department.name)
        .join(Employee, AssessmentRecord.employee_id == Employee.id)
        .join(Department, Employee.dept_id == Department.id, isouter=True)
        .where(AssessmentRecord.plan_id == plan_id)
    )
    if dept_id:
        stmt = stmt.where(Employee.dept_id == dept_id)
    rows = db.execute(stmt).all()

    items = []
    for r in rows:
        record = r[0]
        details = db.execute(select(EvalDetail).where(EvalDetail.record_id == record.id)).scalars().all()
        self_s = [d for d in details if d.evaluator_role == "self"]
        mgr_s = [d for d in details if d.evaluator_role == "manager"]
        items.append({
            "姓名": r[1], "部门": r[2] or "-",
            "自评得分": round(sum(d.score or 0 for d in self_s) / len(self_s), 1) if self_s else None,
            "上级评分": round(sum(d.score or 0 for d in mgr_s) / len(mgr_s), 1) if mgr_s else None,
            "最终得分": record.final_score,
        })
    return items


@router.get("/hr/export")
def export_data(plan_id: int = Query(...), dept_id: Optional[int] = Query(None), fields: str = "basic,self_score,manager_score,final_score", format: str = "csv", user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    stmt = (
        select(AssessmentRecord, Employee.name, Department.name)
        .join(Employee, AssessmentRecord.employee_id == Employee.id)
        .join(Department, Employee.dept_id == Department.id, isouter=True)
        .where(AssessmentRecord.plan_id == plan_id)
    )
    if dept_id:
        stmt = stmt.where(Employee.dept_id == dept_id)
    rows = db.execute(stmt).all()

    output = io.StringIO()
    writer = csv.writer(output)
    field_list = fields.split(",")
    headers = ["姓名", "部门"]
    if "self_score" in field_list: headers.append("自评得分")
    if "manager_score" in field_list: headers.append("上级评分")
    if "final_score" in field_list: headers.append("最终得分")
    writer.writerow(headers)

    for r in rows:
        record = r[0]
        details = db.execute(select(EvalDetail).where(EvalDetail.record_id == record.id)).scalars().all()
        self_s = [d for d in details if d.evaluator_role == "self"]
        mgr_s = [d for d in details if d.evaluator_role == "manager"]
        row = [r[1], r[2] or "-"]
        if "self_score" in field_list: row.append(round(sum(d.score or 0 for d in self_s) / len(self_s), 1) if self_s else "")
        if "manager_score" in field_list: row.append(round(sum(d.score or 0 for d in mgr_s) / len(mgr_s), 1) if mgr_s else "")
        if "final_score" in field_list: row.append(record.final_score or "")
        writer.writerow(row)

    output.seek(0)
    filename = f"perf_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8-sig", headers={"Content-Disposition": f"attachment; filename={filename}"})
