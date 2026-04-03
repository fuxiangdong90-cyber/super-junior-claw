"""测试 - 用户API"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.user import User, UserStatus


# 测试数据库URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试引擎
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    """覆盖数据库依赖"""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    """测试客户端"""
    app.dependency_overrides[get_db] = override_get_db
    
    # 初始化测试数据库
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # 清理
    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_user():
    """测试用户"""
    async with TestSessionLocal() as db:
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("testpass123"),
            status=UserStatus.ACTIVE,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


class TestAuthAPI:
    """认证API测试"""
    
    @pytest.mark.asyncio
    async def test_register(self, client: AsyncClient):
        """测试用户注册"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@example.com"
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """测试登录成功"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """测试密码错误"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_me(self, client: AsyncClient, test_user):
        """测试获取当前用户"""
        # 先登录获取token
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        token = login_response.json()["access_token"]
        
        # 获取用户信息
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"


class TestTasksAPI:
    """任务API测试"""
    
    @pytest.mark.asyncio
    async def test_create_task_unauthorized(self, client: AsyncClient):
        """测试未授权创建任务"""
        response = await client.post(
            "/api/v1/tasks",
            json={
                "name": "Test Task",
                "evaluation_type": "performance",
                "evaluation_target": "model",
                "required_gpu_count": 1
            }
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, client: AsyncClient, test_user):
        """测试获取空任务列表"""
        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        token = login_response.json()["access_token"]
        
        # 获取任务列表
        response = await client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)