import httpx
from app.config import get_settings

settings = get_settings()

# 企微 API 基础地址
WECOM_API_BASE = "https://qyapi.weixin.qq.com/cgi-bin"


class WeComService:
    """企业微信 API 封装"""

    def __init__(self):
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    async def get_access_token(self) -> str:
        """获取 access_token（带缓存，7200秒有效期）"""
        import time
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        url = f"{WECOM_API_BASE}/gettoken"
        params = {
            "corpid": settings.WECOM_CORP_ID,
            "corpsecret": settings.WECOM_SECRET,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        if data.get("errcode") != 0:
            raise Exception(f"获取 access_token 失败: {data}")

        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 7200) - 300  # 提前5分钟刷新
        return self._access_token

    async def get_user_info_by_code(self, code: str) -> dict:
        """通过 OAuth code 获取用户身份信息"""
        token = await self.get_access_token()
        url = f"{WECOM_API_BASE}/user/getuserinfo"
        params = {"access_token": token, "code": code}

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        if data.get("errcode") != 0:
            raise Exception(f"OAuth code 换取用户信息失败: {data}")

        # 企微 API 返回的字段名可能是 UserId（大写）或 userid（小写）
        # 企微成员返回 UserId/userid；若不在可见范围内则返回 OpenId/openid
        userid = (data.get("UserId") or data.get("userid") or
                  data.get("OpenId") or data.get("openid"))
        if not userid:
            raise Exception(f"未获取到用户标识: {data}")

        return {"userid": userid}

    async def get_employee_detail(self, userid: str) -> dict:
        """获取成员详细信息"""
        token = await self.get_access_token()
        url = f"{WECOM_API_BASE}/user/get"
        params = {"access_token": token, "userid": userid}

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        if data.get("errcode") != 0:
            raise Exception(f"获取成员详情失败: {data}")

        return data

    async def get_department_list(self, dept_id: int = 0) -> list:
        """获取部门列表（dept_id=0 获取全部）"""
        token = await self.get_access_token()
        url = f"{WECOM_API_BASE}/department/list"
        params = {"access_token": token, "id": dept_id}

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        if data.get("errcode") != 0:
            raise Exception(f"获取部门列表失败: {data}")

        return data.get("department", [])

    async def get_department_users(self, dept_id: int, fetch_child: int = 1) -> list:
        """获取部门成员详情（fetch_child=1 递归获取子部门成员）"""
        token = await self.get_access_token()
        url = f"{WECOM_API_BASE}/user/list"
        params = {
            "access_token": token,
            "department_id": dept_id,
            "fetch_child": fetch_child
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        if data.get("errcode") != 0:
            raise Exception(f"获取部门成员失败: {data}")

        return data.get("userlist", [])

    async def send_app_message(self, touser: str, msgtype: str = "text",
                                agentid: int | None = None, content: str = "") -> dict:
        """发送应用消息"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            token = await self.get_access_token()
            url = f"{WECOM_API_BASE}/message/send?access_token={token}"
            body = {
                "touser": touser,
                "msgtype": msgtype,
                "agentid": agentid or int(settings.WECOM_AGENT_ID),
                "text": {"content": content},
            }

            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=body)
                data = resp.json()

            if data.get("errcode") != 0:
                logger.error(f"发送应用消息失败 - 用户:{touser}, 错误码:{data.get('errcode')}, 错误信息:{data.get('errmsg')}")
                raise Exception(f"发送消息失败: {data}")

            logger.info(f"成功发送应用消息给用户 {touser}")
            return data

        except Exception as e:
            logger.error(f"发送应用消息异常 - 用户:{touser}, 异常:{str(e)}")
            raise

    async def send_textcard(self, touser: str, title: str, description: str,
                             url: str, agentid: int | None = None) -> dict:
        """发送图文卡片消息（适合考核通知）"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            token = await self.get_access_token()
            api_url = f"{WECOM_API_BASE}/message/send?access_token={token}"
            body = {
                "touser": touser,
                "msgtype": "textcard",
                "agentid": agentid or int(settings.WECOM_AGENT_ID),
                "textcard": {
                    "title": title,
                    "description": description,
                    "url": url,
                },
            }

            async with httpx.AsyncClient() as client:
                resp = await client.post(api_url, json=body)
                data = resp.json()

            if data.get("errcode") != 0:
                logger.error(f"发送卡片消息失败 - 用户:{touser}, 错误码:{data.get('errcode')}, 错误信息:{data.get('errmsg')}")
                raise Exception(f"发送卡片消息失败: {data}")

            logger.info(f"成功发送卡片消息给用户 {touser}: {title}")
            return data

        except Exception as e:
            logger.error(f"发送卡片消息异常 - 用户:{touser}, 标题:{title}, 异常:{str(e)}")
            raise


# 单例
wecom_service = WeComService()
