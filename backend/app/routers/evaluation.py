from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import AssessmentRecord, AssessmentPlan, EvalDetail, ApprovalLog, Employee, EvalTemplate, Department, RecordStatus
from app.routers.auth import UserInfo, get_login_user
from app.services.wecom import wecom_service
from app.config import get_settings
from app.permissions import require_hr_user

router = APIRouter(prefix="/api/eval", tags=["评估"])
settings = get_settings()


class SelfEvalSubmit(BaseModel):
    record_id: int
    scores: list[dict]


@router.post("/self")
async def submit_self_eval(body: SelfEvalSubmit, user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    stmt = select(AssessmentRecord).where(AssessmentRecord.id == body.record_id, AssessmentRecord.employee_id == user.id)
    record = db.execute(stmt).scalar_one_or_none()
    if not record:
        raise HTTPException(404, "考核记录不存在")
    if record.status not in (RecordStatus.PENDING.value, RecordStatus.RETURNED.value):
        raise HTTPException(400, f"当前状态不允许自评: {record.status}")

    for item in body.scores:
        detail = EvalDetail(
            record_id=record.id, dimension_name=item["dimension_name"],
            dimension_weight=item.get("weight", 0), dimension_type=item.get("type", "custom"),
            evaluator_id=user.id, evaluator_role="self",
            score=item["score"], comment=item.get("comment", ""),
        )
        db.add(detail)

    record.status = RecordStatus.SELF_EVAL_SUBMITTED.value
    record.current_step = "manager_eval"
    log = ApprovalLog(record_id=record.id, from_step="self_eval", to_step="manager_eval", approver_id=user.id, action="submit", comment="员工提交自评")
    db.add(log)
    db.flush()

    # 通知直属上级
    if record.employee and record.employee.direct_leader_id:
        leader = db.execute(select(Employee).where(Employee.id == record.employee.direct_leader_id)).scalar_one_or_none()
        if leader:
            try:
                await wecom_service.send_textcard(touser=leader.wecom_userid, title="新评估待处理", description=f"{user.name} 已提交自评，请及时进行上级评估", url=f"{settings.APP_BASE_URL}/manager/eval/{record.id}")
            except Exception:
                pass
    return {"message": "自评已提交"}


class ManagerEvalSubmit(BaseModel):
    record_id: int
    scores: list[dict]
    action: str = "approve"
    return_comment: Optional[str] = None


@router.post("/manager")
async def submit_manager_eval(body: ManagerEvalSubmit, user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    record = db.execute(select(AssessmentRecord).where(AssessmentRecord.id == body.record_id)).scalar_one_or_none()
    if not record:
        raise HTTPException(404, "考核记录不存在")
    if record.status != RecordStatus.SELF_EVAL_SUBMITTED.value:
        raise HTTPException(400, f"当前状态不允许上级评估: {record.status}")

    if body.action == "return":
        record.status = RecordStatus.RETURNED.value
        record.current_step = "self_eval"
        db.add(ApprovalLog(record_id=record.id, from_step="manager_eval", to_step="self_eval", approver_id=user.id, action="return", comment=body.return_comment or "请修改后重新提交"))
        db.flush()
        emp = db.execute(select(Employee).where(Employee.id == record.employee_id)).scalar_one_or_none()
        if emp:
            try:
                await wecom_service.send_app_message(touser=emp.wecom_userid, content=f"您的自评已被退回，原因：{body.return_comment or '请修改后重新提交'}")
            except Exception:
                pass
        return {"message": "已退回"}

    for item in body.scores:
        db.add(EvalDetail(record_id=record.id, dimension_name=item["dimension_name"], dimension_weight=item.get("weight", 0), dimension_type=item.get("type", "custom"), evaluator_id=user.id, evaluator_role="manager", score=item["score"], comment=item.get("comment", "")))

    approval_chain = record.plan.approval_chain or [] if record.plan else []
    if "vp" in approval_chain:
        record.status = RecordStatus.MANAGER_EVAL_SUBMITTED.value
        record.current_step = "vp_approval"
        # TODO: 通知VP审批（需要VP角色系统）
    elif "hr" in approval_chain:
        record.status = RecordStatus.MANAGER_EVAL_SUBMITTED.value
        record.current_step = "hr_final"
        # 通知HR进行终审
        try:
            # 查找所有HR用户
            from app.permissions import Role
            hr_users = db.execute(
                select(Employee).where(
                    Employee.position.like('%HR%') | Employee.position.like('%人力%')
                )
            ).scalars().all()

            emp = db.execute(select(Employee).where(Employee.id == record.employee_id)).scalar_one_or_none()
            if emp and hr_users:
                for hr_user in hr_users[:3]:  # 最多通知3个HR
                    try:
                        await wecom_service.send_textcard(
                            touser=hr_user.wecom_userid,
                            title="新考核待终审",
                            description=f"{emp.name} 的考核已完成上级评估，请进行HR终审",
                            url=f"{settings.APP_BASE_URL}/hr/review"
                        )
                    except Exception:
                        pass
        except Exception:
            pass
    else:
        record.status = RecordStatus.HR_APPROVED.value
        record.current_step = "done"
    db.add(ApprovalLog(record_id=record.id, from_step="manager_eval", to_step=record.current_step, approver_id=user.id, action="approve", comment="上级评估通过"))
    db.flush()
    return {"message": "上级评估已提交", "next_step": record.current_step}


class HRFinalSubmit(BaseModel):
    record_id: int
    action: str = "approve"
    final_score: Optional[float] = None
    final_comment: Optional[str] = None


@router.post("/hr-final")
async def hr_final(body: HRFinalSubmit, user: UserInfo = Depends(require_hr_user), db: Session = Depends(get_db)):
    record = db.execute(select(AssessmentRecord).where(AssessmentRecord.id == body.record_id)).scalar_one_or_none()
    if not record:
        raise HTTPException(404, "考核记录不存在")

    if body.action == "return":
        record.status = RecordStatus.RETURNED.value
        record.current_step = "self_eval"
        db.add(ApprovalLog(record_id=record.id, from_step=record.current_step, to_step="self_eval", approver_id=user.id, action="return", comment=body.final_comment or "HR 退回"))
        db.flush()

        # 通知员工
        emp = db.execute(select(Employee).where(Employee.id == record.employee_id)).scalar_one_or_none()
        if emp:
            try:
                await wecom_service.send_textcard(
                    touser=emp.wecom_userid,
                    title="考核已退回",
                    description=f"HR已退回您的考核，原因：{body.final_comment or '请修改后重新提交'}",
                    url=f"{settings.APP_BASE_URL}/employee/self-eval/{record.id}"
                )
            except Exception:
                pass
        return {"message": "已退回"}

    record.status = RecordStatus.LOCKED.value
    record.final_score = body.final_score
    record.final_comment = body.final_comment
    db.add(ApprovalLog(record_id=record.id, from_step=record.current_step, to_step="done", approver_id=user.id, action="approve", comment=body.final_comment or "HR 终审通过"))
    db.flush()

    emp = db.execute(select(Employee).where(Employee.id == record.employee_id)).scalar_one_or_none()
    if emp:
        try:
            await wecom_service.send_textcard(touser=emp.wecom_userid, title="绩效结果已发布", description=f"本期绩效得分：{body.final_score or '待公布'}", url=f"{settings.APP_BASE_URL}/employee/result/{record.id}")
        except Exception:
            pass
    return {"message": "终审完成，结果已发布"}


@router.get("/record/{record_id}/logs")
def get_approval_logs(record_id: int, user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    """获取审批日志，显示审批人姓名而非步骤名"""
    rows = db.execute(
        select(ApprovalLog, Employee.name)
        .join(Employee, ApprovalLog.approver_id == Employee.id)
        .where(ApprovalLog.record_id == record_id)
        .order_by(ApprovalLog.created_at)
    ).all()

    # 获取考核记录以便查找相关人员
    record = db.execute(select(AssessmentRecord).where(AssessmentRecord.id == record_id)).scalar_one_or_none()
    if not record:
        return []

    # 获取员工信息
    employee = db.execute(select(Employee).where(Employee.id == record.employee_id)).scalar_one_or_none()

    # 获取直属上级信息
    manager = None
    if employee and employee.direct_leader_id:
        manager = db.execute(select(Employee).where(Employee.id == employee.direct_leader_id)).scalar_one_or_none()

    result = []
    for r in rows:
        log, approver_name = r[0], r[1]

        # 将步骤名转换为人名
        from_name = ""
        to_name = ""

        if log.from_step == "self_eval":
            from_name = employee.name if employee else "员工"
        elif log.from_step == "manager_eval":
            from_name = manager.name if manager else "上级"
        elif log.from_step in ["vp_approval", "hr_final"]:
            from_name = approver_name

        if log.to_step == "self_eval":
            to_name = employee.name if employee else "员工"
        elif log.to_step == "manager_eval":
            to_name = manager.name if manager else "上级"
        elif log.to_step in ["vp_approval", "hr_final", "done"]:
            to_name = "HR" if log.to_step == "hr_final" else ("完成" if log.to_step == "done" else "VP")

        result.append({
            "from": from_name,
            "to": to_name,
            "action": log.action,
            "comment": log.comment,
            "approver": approver_name,
            "created_at": str(log.created_at)
        })

    return result


@router.get("/record/{record_id}")
def get_eval_detail(record_id: int, user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    record = db.execute(select(AssessmentRecord).where(AssessmentRecord.id == record_id)).scalar_one_or_none()
    if not record:
        raise HTTPException(404, "考核记录不存在")

    emp_row = db.execute(select(Employee, Department.name).outerjoin(Department, Employee.dept_id == Department.id).where(Employee.id == record.employee_id)).one_or_none()
    employee_name = emp_row[0].name if emp_row else "未知"
    dept_name = emp_row[1] if emp_row else None

    plan_row = db.execute(select(AssessmentPlan, EvalTemplate).outerjoin(EvalTemplate, AssessmentPlan.template_id == EvalTemplate.id).where(AssessmentPlan.id == record.plan_id)).one_or_none()
    plan_info = None
    template_info = None
    if plan_row:
        plan, template = plan_row[0], plan_row[1]
        plan_info = {"id": plan.id, "name": plan.name, "cycle_type": plan.cycle_type, "status": plan.status, "start_date": str(plan.start_date), "end_date": str(plan.end_date), "self_eval_end": str(plan.self_eval_end) if plan.self_eval_end else None, "approval_chain": plan.approval_chain}
        if template:
            template_info = {"id": template.id, "name": template.name, "type": template.type, "dimensions": template.dimensions_json}

    details = db.execute(select(EvalDetail, Employee.name).join(Employee, EvalDetail.evaluator_id == Employee.id).where(EvalDetail.record_id == record_id)).all()

    return {
        "id": record.id, "status": record.status, "current_step": record.current_step,
        "final_score": record.final_score, "final_comment": record.final_comment,
        "employee_id": record.employee_id, "employee_name": employee_name, "dept_name": dept_name,
        "plan": plan_info, "template": template_info,
        "evaluations": [{"dimension": d[0].dimension_name, "weight": d[0].dimension_weight, "dimension_type": d[0].dimension_type, "evaluator_role": d[0].evaluator_role, "evaluator_name": d[1], "score": d[0].score, "comment": d[0].comment} for d in details],
    }
