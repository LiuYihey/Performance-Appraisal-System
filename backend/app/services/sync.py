"""
企业微信组织架构同步服务
自动同步部门和员工信息
"""
import asyncio
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Department, Employee, EmployeeStatus
from app.services.wecom import wecom_service

logger = logging.getLogger(__name__)


class SyncService:
    """组织架构同步服务"""

    @staticmethod
    async def sync_departments(db: Session) -> int:
        """
        同步所有部门
        返回同步的部门数量
        """
        try:
            logger.info("开始同步部门...")
            dept_list = await wecom_service.get_department_list()

            # 按照 id 排序，确保父部门先创建
            dept_list.sort(key=lambda d: d.get('id', 0))

            synced_count = 0
            # 分两轮处理：第一轮创建所有部门（parent_id 暂时设为 None），第二轮更新 parent_id
            dept_ids = set()

            # 第一轮：创建或更新部门基本信息
            for dept_data in dept_list:
                dept_id = dept_data.get('id')
                if not dept_id:
                    continue

                dept_ids.add(dept_id)

                # 检查部门是否已存在
                stmt = select(Department).where(Department.id == dept_id)
                existing = db.execute(stmt).scalar_one_or_none()

                if existing:
                    # 更新部门名称
                    existing.name = dept_data.get('name', existing.name)
                else:
                    # 创建新部门（parent_id 暂时为 None）
                    new_dept = Department(
                        id=dept_id,
                        name=dept_data.get('name', f'部门{dept_id}'),
                        parent_id=None
                    )
                    db.add(new_dept)
                    synced_count += 1

            db.flush()

            # 第二轮：更新 parent_id
            for dept_data in dept_list:
                dept_id = dept_data.get('id')
                if not dept_id:
                    continue

                parent_id = dept_data.get('parentid')
                if parent_id == 0:
                    parent_id = None

                # 只有当 parent_id 存在于同步的部门列表中时才设置
                if parent_id and parent_id not in dept_ids:
                    logger.warning(f"部门 {dept_id} 的父部门 {parent_id} 不存在，跳过")
                    parent_id = None

                stmt = select(Department).where(Department.id == dept_id)
                dept = db.execute(stmt).scalar_one_or_none()
                if dept:
                    dept.parent_id = parent_id

            db.commit()
            logger.info(f"部门同步完成，新增 {synced_count} 个部门")
            return synced_count

        except Exception as e:
            logger.error(f"同步部门失败: {str(e)}", exc_info=True)
            db.rollback()
            return 0

    @staticmethod
    async def sync_employees_in_department(db: Session, dept_id: int) -> int:
        """
        同步指定部门的员工（递归包含子部门）
        返回同步的员工数量
        """
        try:
            logger.info(f"同步部门 {dept_id} 及其子部门的员工...")

            # 获取部门成员列表（完整信息，包含子部门）
            user_list = await wecom_service.get_department_users(dept_id, fetch_child=1)

            # 获取所有有效的部门 ID
            dept_stmt = select(Department.id)
            valid_dept_ids = set(db.execute(dept_stmt).scalars().all())

            synced_count = 0
            for user_data in user_list:
                userid = user_data.get('userid')
                if not userid:
                    continue

                # 处理部门ID（可能是列表）
                emp_dept_id = user_data.get('department')
                if isinstance(emp_dept_id, list) and emp_dept_id:
                    # 找到第一个有效的部门 ID
                    emp_dept_id = next((did for did in emp_dept_id if did in valid_dept_ids), None)
                    if not emp_dept_id:
                        logger.warning(f"员工 {userid} 的所有部门 ID 都无效，跳过")
                        continue
                elif emp_dept_id not in valid_dept_ids:
                    logger.warning(f"员工 {userid} 的部门 ID {emp_dept_id} 不存在，跳过")
                    continue

                # 检查员工是否已存在
                stmt = select(Employee).where(Employee.wecom_userid == userid)
                existing = db.execute(stmt).scalar_one_or_none()

                if existing:
                    # 更新基本信息
                    existing.name = user_data.get('name', existing.name)
                    existing.dept_id = emp_dept_id
                    existing.position = user_data.get('position', existing.position)
                    existing.avatar = user_data.get('avatar', existing.avatar)
                    existing.phone = user_data.get('mobile', existing.phone)

                    # 更新状态（1=已激活 2=已禁用 4=未激活 5=退出企业）
                    status_map = {1: EmployeeStatus.ACTIVE.value, 2: EmployeeStatus.INACTIVE.value,
                                  4: EmployeeStatus.INACTIVE.value, 5: EmployeeStatus.INACTIVE.value}
                    existing.status = status_map.get(user_data.get('status', 1), EmployeeStatus.ACTIVE.value)
                else:
                    # 处理职级
                    level = user_data.get('order')
                    if isinstance(level, list) and level:
                        level = level[0]

                    # 处理直属上级
                    direct_leader_id = None
                    main_department = user_data.get('main_department')
                    if main_department and main_department in valid_dept_ids:
                        # 查找部门负责人
                        dept_stmt = select(Department).where(Department.id == main_department)
                        dept = db.execute(dept_stmt).scalar_one_or_none()
                        if dept and dept.leader_id:
                            direct_leader_id = dept.leader_id

                    # 创建员工记录
                    new_employee = Employee(
                        name=user_data.get('name', userid),
                        wecom_userid=userid,
                        dept_id=emp_dept_id,
                        position=user_data.get('position'),
                        level=str(level) if level is not None else None,
                        avatar=user_data.get('avatar'),
                        phone=user_data.get('mobile'),
                        status=EmployeeStatus.ACTIVE.value,
                        direct_leader_id=direct_leader_id
                    )
                    db.add(new_employee)
                    synced_count += 1

                db.flush()

            db.commit()
            logger.info(f"部门 {dept_id} 及子部门员工同步完成，新增 {synced_count} 人")
            return synced_count

        except Exception as e:
            logger.error(f"同步部门 {dept_id} 员工失败: {str(e)}", exc_info=True)
            db.rollback()
            return 0

    @staticmethod
    async def sync_all_employees(db: Session) -> int:
        """
        同步所有部门的员工
        返回同步的员工总数
        """
        try:
            # 先同步部门
            await SyncService.sync_departments(db)

            # 从根部门（ID=1）递归获取所有成员，避免重复同步
            # fetch_child=1 会自动包含所有子部门成员
            logger.info("从根部门递归同步所有员工...")
            total_synced = await SyncService.sync_employees_in_department(db, dept_id=1)

            logger.info(f"全量同步完成，共同步 {total_synced} 名员工")
            return total_synced

        except Exception as e:
            logger.error(f"全量同步失败: {str(e)}", exc_info=True)
            return 0

    @staticmethod
    async def update_leader_relationships(db: Session):
        """
        更新员工的直属上级关系
        基于部门负责人信息
        """
        try:
            logger.info("开始更新上下级关系...")

            # 获取所有员工
            stmt = select(Employee)
            employees = db.execute(stmt).scalars().all()

            updated_count = 0
            for emp in employees:
                if not emp.dept_id:
                    continue

                # 查找部门信息
                dept_stmt = select(Department).where(Department.id == emp.dept_id)
                dept = db.execute(dept_stmt).scalar_one_or_none()

                if dept and dept.leader_id and dept.leader_id != emp.id:
                    # 设置直属上级为部门负责人
                    if emp.direct_leader_id != dept.leader_id:
                        emp.direct_leader_id = dept.leader_id
                        updated_count += 1

            db.commit()
            logger.info(f"上下级关系更新完成，更新 {updated_count} 人")

        except Exception as e:
            logger.error(f"更新上下级关系失败: {str(e)}", exc_info=True)
            db.rollback()


# 单例
sync_service = SyncService()


async def run_full_sync():
    """执行完整同步（可以作为定时任务）"""
    db = SessionLocal()
    try:
        logger.info("=" * 50)
        logger.info("开始执行组织架构全量同步")
        logger.info("=" * 50)

        # 同步所有员工
        total = await sync_service.sync_all_employees(db)

        # 更新上下级关系
        await sync_service.update_leader_relationships(db)

        logger.info("=" * 50)
        logger.info(f"组织架构全量同步完成，共同步 {total} 名员工")
        logger.info("=" * 50)

    finally:
        db.close()
