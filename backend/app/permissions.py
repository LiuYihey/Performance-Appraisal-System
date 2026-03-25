"""
权限管理模块
定义角色和权限验证装饰器
"""
from functools import wraps
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Callable

from app.routers.auth import UserInfo, get_login_user
from app.database import get_db
from app.models import Employee


# 角色定义
class Role:
    EMPLOYEE = "employee"      # 普通员工
    MANAGER = "manager"        # 部门经理
    HR = "hr"                  # HR
    ADMIN = "admin"            # 系统管理员


# 管理员用户列表（企微userid）
ADMIN_USERS = ["LiuYiHao"]


def get_user_role(user: UserInfo, db: Session) -> str:
    """
    获取用户角色
    优先级：admin > hr > manager > employee
    """
    # 检查是否为管理员
    if user.wecom_userid in ADMIN_USERS:
        return Role.ADMIN

    # 检查是否为HR（可以通过部门名称或职位判断）
    if user.position and ("hr" in user.position.lower() or "人力" in user.position):
        return Role.HR

    # 检查是否为经理
    stmt = select(Employee).where(Employee.id == user.id)
    employee = db.execute(stmt).scalar_one_or_none()
    if employee:
        # 检查是否有下属
        stmt_subordinates = select(Employee).where(Employee.direct_leader_id == employee.id).limit(1)
        has_subordinates = db.execute(stmt_subordinates).scalar_one_or_none()
        if has_subordinates:
            return Role.MANAGER

    return Role.EMPLOYEE


def require_role(*allowed_roles: str):
    """
    权限验证装饰器
    用法：
    @require_role(Role.ADMIN, Role.HR)
    async def some_endpoint(user: UserInfo = Depends(get_login_user)):
        ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取user和db
            user = kwargs.get("user")
            db = kwargs.get("db")

            if not user:
                raise HTTPException(status_code=401, detail="未登录")

            if not db:
                raise HTTPException(status_code=500, detail="数据库连接失败")

            # 获取用户角色
            user_role = get_user_role(user, db)

            # 管理员拥有所有权限
            if user_role == Role.ADMIN:
                return await func(*args, **kwargs) if callable(getattr(func, '__call__', None)) and hasattr(func, '__await__') else func(*args, **kwargs)

            # 检查角色权限
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"权限不足，需要以下角色之一: {', '.join(allowed_roles)}"
                )

            return await func(*args, **kwargs) if callable(getattr(func, '__call__', None)) and hasattr(func, '__await__') else func(*args, **kwargs)

        return wrapper
    return decorator


def require_admin(func: Callable):
    """管理员权限装饰器"""
    return require_role(Role.ADMIN)(func)


def require_hr(func: Callable):
    """HR权限装饰器（HR和管理员可访问）"""
    return require_role(Role.HR, Role.ADMIN)(func)


def require_manager(func: Callable):
    """经理权限装饰器（经理、HR和管理员可访问）"""
    return require_role(Role.MANAGER, Role.HR, Role.ADMIN)(func)


# 依赖注入函数
async def get_current_user_with_role(
    user: UserInfo = Depends(get_login_user),
    db: Session = Depends(get_db)
) -> tuple[UserInfo, str]:
    """获取当前用户及其角色"""
    role = get_user_role(user, db)
    return user, role


async def require_admin_user(
    user: UserInfo = Depends(get_login_user),
    db: Session = Depends(get_db)
) -> UserInfo:
    """要求管理员权限的依赖注入"""
    role = get_user_role(user, db)
    if role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


async def require_hr_user(
    user: UserInfo = Depends(get_login_user),
    db: Session = Depends(get_db)
) -> UserInfo:
    """要求HR权限的依赖注入"""
    role = get_user_role(user, db)
    if role not in [Role.HR, Role.ADMIN]:
        raise HTTPException(status_code=403, detail="需要HR或管理员权限")
    return user


async def require_manager_user(
    user: UserInfo = Depends(get_login_user),
    db: Session = Depends(get_db)
) -> UserInfo:
    """要求经理权限的依赖注入"""
    role = get_user_role(user, db)
    if role not in [Role.MANAGER, Role.HR, Role.ADMIN]:
        raise HTTPException(status_code=403, detail="需要经理、HR或管理员权限")
    return user
