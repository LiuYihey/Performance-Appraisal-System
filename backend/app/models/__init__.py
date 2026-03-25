from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Enum as SAEnum, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


# ── 枚举 ──

class EmployeeStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    SELF_EVAL = "self_eval"
    MANAGER_EVAL = "manager_eval"
    VP_APPROVAL = "vp_approval"
    HR_FINAL = "hr_final"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class RecordStatus(str, enum.Enum):
    PENDING = "pending"
    SELF_EVAL_SUBMITTED = "self_eval_submitted"
    MANAGER_EVAL_SUBMITTED = "manager_eval_submitted"
    VP_APPROVED = "vp_approved"
    HR_APPROVED = "hr_approved"
    RETURNED = "returned"
    NOT_SUBMITTED = "not_submitted"
    LOCKED = "locked"


class ApprovalAction(str, enum.Enum):
    SUBMIT = "submit"
    APPROVE = "approve"
    RETURN = "return"


# ── 部门 ──

class Department(Base):
    __tablename__ = "department"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="部门名称")
    parent_id = Column(Integer, ForeignKey("department.id"), nullable=True, comment="上级部门ID")
    leader_id = Column(Integer, ForeignKey("employee.id"), nullable=True, comment="部门负责人ID")

    # 关系
    parent = relationship("Department", remote_side=[id], backref="children")
    leader = relationship("Employee", foreign_keys=[leader_id])
    employees = relationship("Employee", foreign_keys="Employee.dept_id", back_populates="department")


# ── 员工 ──

class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="姓名")
    wecom_userid = Column(String(64), unique=True, nullable=False, index=True, comment="企微 userid")
    dept_id = Column(Integer, ForeignKey("department.id"), nullable=True, comment="部门ID")
    position = Column(String(50), nullable=True, comment="职位")
    level = Column(String(20), nullable=True, comment="职级")
    avatar = Column(String(255), nullable=True, comment="头像URL")
    phone = Column(String(20), nullable=True, comment="手机号")
    status = Column(String(20), default=EmployeeStatus.ACTIVE.value, comment="状态")
    direct_leader_id = Column(Integer, ForeignKey("employee.id"), nullable=True, comment="直属上级ID")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    department = relationship("Department", foreign_keys=[dept_id], back_populates="employees")
    direct_leader = relationship("Employee", remote_side=[id], foreign_keys=[direct_leader_id])


# ── 评估模板 ──

class EvalTemplate(Base):
    __tablename__ = "eval_template"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="模板名称")
    type = Column(String(20), nullable=False, comment="模板类型: okr/kpi/360/custom")
    dimensions_json = Column(JSON, nullable=False, comment='维度配置 [{"name":"目标达成","weight":40,"type":"kpi"}]')
    is_default = Column(Boolean, default=False, comment="是否默认模板")
    created_by = Column(Integer, ForeignKey("employee.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ── 考核计划 ──

class AssessmentPlan(Base):
    __tablename__ = "assessment_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="计划名称")
    cycle_type = Column(String(20), nullable=False, comment="周期类型: monthly/quarterly/yearly/custom")
    start_date = Column(DateTime, nullable=False, comment="开始日期")
    end_date = Column(DateTime, nullable=False, comment="结束日期")
    self_eval_start = Column(DateTime, nullable=True, comment="自评开始时间")
    self_eval_end = Column(DateTime, nullable=True, comment="自评截止时间")
    manager_eval_end = Column(DateTime, nullable=True, comment="上级评估截止时间")
    template_id = Column(Integer, ForeignKey("eval_template.id"), nullable=False, comment="评估模板")
    approval_chain = Column(JSON, nullable=False, comment='审批链 ["direct_leader","vp","hr"]')
    status = Column(String(20), default=PlanStatus.DRAFT.value, comment="计划状态")
    created_by = Column(Integer, ForeignKey("employee.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    template = relationship("EvalTemplate")
    records = relationship("AssessmentRecord", back_populates="plan")


# ── 个人考核记录 ──

class AssessmentRecord(Base):
    __tablename__ = "assessment_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("assessment_plan.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    status = Column(String(30), default=RecordStatus.PENDING.value, comment="当前状态")
    current_step = Column(String(30), default="self_eval", comment="当前审批步骤")
    final_score = Column(Float, nullable=True, comment="最终得分")
    final_comment = Column(Text, nullable=True, comment="最终评语")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    plan = relationship("AssessmentPlan", back_populates="records")
    employee = relationship("Employee")
    eval_details = relationship("EvalDetail", back_populates="record")
    approval_logs = relationship("ApprovalLog", back_populates="record")


# ── 评估明细 ──

class EvalDetail(Base):
    __tablename__ = "eval_detail"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey("assessment_record.id"), nullable=False)
    dimension_name = Column(String(100), nullable=False, comment="维度名称")
    dimension_weight = Column(Float, nullable=False, comment="维度权重")
    dimension_type = Column(String(20), nullable=False, comment="维度类型")
    evaluator_id = Column(Integer, ForeignKey("employee.id"), nullable=False, comment="评估人ID")
    evaluator_role = Column(String(20), nullable=False, comment="评估人角色: self/manager/vp/hr/peer")
    score = Column(Float, nullable=True, comment="评分")
    comment = Column(Text, nullable=True, comment="评语")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    record = relationship("AssessmentRecord", back_populates="eval_details")
    evaluator = relationship("Employee")


# ── 审批流水 ──

class ApprovalLog(Base):
    __tablename__ = "approval_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey("assessment_record.id"), nullable=False)
    from_step = Column(String(30), nullable=True, comment="来源步骤")
    to_step = Column(String(30), nullable=True, comment="目标步骤")
    approver_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    action = Column(String(20), nullable=False, comment="操作: submit/approve/return")
    comment = Column(Text, nullable=True, comment="批注意见")
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    record = relationship("AssessmentRecord", back_populates="approval_logs")
    approver = relationship("Employee")
