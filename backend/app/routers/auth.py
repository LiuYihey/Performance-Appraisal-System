from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import secrets

from app.config import get_settings
from app.database import get_db
from app.models import Employee, Department
from app.services.wecom import wecom_service

router = APIRouter(prefix="/auth", tags=["认证"])
settings = get_settings()

# 简易 token 存储（生产环境用 Redis）
_token_store: dict[str, dict] = {}


class UserInfo(BaseModel):
    id: int
    name: str
    wecom_userid: str
    dept_id: int | None = None
    dept_name: str | None = None
    position: str | None = None
    level: str | None = None
    avatar: str | None = None
    role: str = "employee"  # employee / manager / hr / admin


def _build_oauth_url(redirect_uri: str, state: str) -> str:
    return (
        f"https://open.weixin.qq.com/connect/oauth2/authorize"
        f"?appid={settings.WECOM_CORP_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=snsapi_base"
        f"&state={state}#wechat_redirect"
    )


def _create_session(user: UserInfo) -> str:
    token = secrets.token_urlsafe(32)
    _token_store[token] = {
        "user": user.model_dump(),
        "expires": datetime.now() + timedelta(hours=24),
    }
    return token


def _get_current_user(token: str) -> UserInfo | None:
    if not token:
        return None
    session = _token_store.get(token)
    if not session:
        return None
    if datetime.now() > session["expires"]:
        _token_store.pop(token, None)
        return None
    return UserInfo(**session["user"])


# ── 依赖注入 ──

async def get_login_user(request: Request, db: Session = Depends(get_db)) -> UserInfo:
    """获取当前登录用户（未登录则 401）"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
    else:
        token = request.cookies.get("token", "")
    user = _get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return user


# ── 接口 ──

@router.get("/login")
async def login(request: Request):
    """跳转到企微 OAuth 授权页"""
    state = secrets.token_urlsafe(16)
    redirect_uri = f"{settings.APP_BASE_URL}/auth/callback"
    url = _build_oauth_url(redirect_uri, state)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url)


@router.get("/callback")
async def callback(code: str, state: str, db: Session = Depends(get_db)):
    """企微 OAuth 回调"""
    from fastapi.responses import RedirectResponse, Response
    import logging

    logger = logging.getLogger(__name__)

    if not code:
        raise HTTPException(status_code=400, detail="缺少 code 参数")

    try:
        # 1. 用 code 换取 userid
        logger.info(f"开始用 code 换取用户信息: code={code[:10]}...")
        user_info = await wecom_service.get_user_info_by_code(code)
        userid = user_info["userid"]
        logger.info(f"成功获取 userid: {userid}")

        # 2. 获取企微成员详情
        logger.info(f"开始获取成员详情: userid={userid}")
        detail = await wecom_service.get_employee_detail(userid)
        logger.info(f"成功获取成员详情: name={detail.get('name')}")
    except Exception as e:
        logger.error(f"企微 OAuth 回调失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"企微认证失败: {str(e)}")

    try:
        # 3. 查找或自动创建本地员工记录
        logger.info(f"查找本地员工记录: userid={userid}")
        stmt = select(Employee).where(Employee.wecom_userid == userid)
        employee = db.execute(stmt).scalar_one_or_none()

        if not employee:
            logger.info(f"创建新员工记录: userid={userid}")
            # 企微 API 返回的 department 可能是列表，取第一个
            dept_id = detail.get("department")
            if isinstance(dept_id, list) and dept_id:
                dept_id = dept_id[0]

            # 如果部门不存在，先创建部门（包括所有父部门）
            if dept_id:
                dept_stmt = select(Department).where(Department.id == dept_id)
                dept = db.execute(dept_stmt).scalar_one_or_none()
                if not dept:
                    logger.info(f"部门 {dept_id} 不存在，尝试从企微同步")
                    try:
                        dept_list = await wecom_service.get_department_list()
                        dept_dict = {d["id"]: d for d in dept_list}

                        # 递归创建部门及其所有父部门
                        def create_dept_recursive(dept_id_to_create):
                            if dept_id_to_create in dept_dict:
                                # 检查是否已存在
                                existing = db.execute(
                                    select(Department).where(Department.id == dept_id_to_create)
                                ).scalar_one_or_none()
                                if existing:
                                    return

                                dept_data = dept_dict[dept_id_to_create]
                                parent_id = dept_data.get("parentid")

                                # 先创建父部门
                                if parent_id and parent_id != 0:
                                    create_dept_recursive(parent_id)

                                # 再创建当前部门
                                new_dept = Department(
                                    id=dept_data["id"],
                                    name=dept_data["name"],
                                    parent_id=parent_id if parent_id != 0 else None
                                )
                                db.add(new_dept)
                                db.flush()
                                logger.info(f"成功创建部门: {dept_data['name']} (ID: {dept_id_to_create})")

                        create_dept_recursive(dept_id)
                    except Exception as dept_err:
                        logger.warning(f"同步部门失败: {dept_err}，将不关联部门")
                        dept_id = None
                        db.rollback()  # 回滚失败的事务

            # level 字段也可能是列表
            level = detail.get("order") or detail.get("status")
            if isinstance(level, list) and level:
                level = level[0]

            employee = Employee(
                name=detail.get("name", userid),
                wecom_userid=userid,
                dept_id=dept_id,
                position=detail.get("position"),
                level=str(level) if level is not None else None,
                avatar=detail.get("avatar"),
                phone=detail.get("mobile"),
            )
            db.add(employee)
            db.flush()
            logger.info(f"员工记录创建成功: id={employee.id}")

        # 4. 获取部门名称
        dept_name = None
        if employee.dept_id:
            dept_stmt = select(Department).where(Department.id == employee.dept_id)
            dept = db.execute(dept_stmt).scalar_one_or_none()
            if dept:
                dept_name = dept.name
            else:
                try:
                    dept_list = await wecom_service.get_department_list()
                    for d in dept_list:
                        if d.get("id") == employee.dept_id:
                            new_dept = Department(id=d["id"], name=d["name"], parent_id=d.get("parentid"))
                            db.add(new_dept)
                            db.flush()
                            dept_name = d["name"]
                            break
                except Exception as dept_err:
                    logger.warning(f"获取部门信息失败: {dept_err}")

        # 5. 判断角色（使用权限模块）
        from app.permissions import get_user_role
        temp_user = UserInfo(
            id=employee.id,
            name=employee.name,
            wecom_userid=employee.wecom_userid,
            dept_id=employee.dept_id,
            dept_name=dept_name,
            position=employee.position,
            level=employee.level,
            avatar=employee.avatar,
            role="employee",  # 临时角色
        )
        role = get_user_role(temp_user, db)

        # 6. 构造用户信息并创建会话
        user = UserInfo(
            id=employee.id,
            name=employee.name,
            wecom_userid=employee.wecom_userid,
            dept_id=employee.dept_id,
            dept_name=dept_name,
            position=employee.position,
            level=employee.level,
            avatar=employee.avatar,
            role=role,
        )
        token = _create_session(user)
        logger.info(f"登录成功: user_id={employee.id}, name={employee.name}")

        # 7. 设置 cookie 并重定向到前端首页
        redirect_url = f"{settings.APP_BASE_URL}/"
        logger.info(f"重定向到: {redirect_url}, token已设置到cookie")
        response = RedirectResponse(url=redirect_url)
        response.set_cookie("token", token, httponly=False, max_age=86400, samesite="lax")
        db.commit()  # 提交数据库事务
        return response
    except Exception as e:
        logger.error(f"处理用户数据失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"处理用户数据失败: {str(e)}")


@router.get("/me")
async def get_me(user: UserInfo = Depends(get_login_user), db: Session = Depends(get_db)):
    from app.permissions import get_user_role
    role = get_user_role(user, db)
    user_dict = user.model_dump()
    user_dict["role"] = role  # 更新为实际角色
    return user_dict


@router.post("/logout")
async def logout(request: Request):
    from fastapi.responses import Response
    auth = request.headers.get("Authorization", "")
    token = ""
    if auth.startswith("Bearer "):
        token = auth[7:]
    if not token:
        token = request.cookies.get("token", "")
    if token:
        _token_store.pop(token, None)

    from fastapi.responses import JSONResponse
    response = JSONResponse(content={"message": "已退出"})
    response.delete_cookie("token")
    return response
