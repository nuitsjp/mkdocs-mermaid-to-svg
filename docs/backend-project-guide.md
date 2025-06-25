---
title: バックエンドプロジェクトガイド
created_at: 2025-06-14
updated_at: 2025-06-15
---

このドキュメントはFastAPIを使用したバックエンドプロジェクト用の設定とベストプラクティスを提供します。

## バックエンド特化の依存関係

### 基本パッケージ

```toml
# pyproject.toml に追加
dependencies = [
    # API フレームワーク
    "fastapi>=X.X.X",
    "uvicorn[standard]>=X.X.X",

    # データバリデーション
    "pydantic>=X.X.X",
    "pydantic-settings>=X.X.X",

    # データベース
    "sqlalchemy>=X.X.X",
    "alembic>=X.X.X",
    "asyncpg>=X.X.X",  # PostgreSQL
    # "aiomysql>=0.2.0",  # MySQL

    # 認証・セキュリティ
    "python-jose[cryptography]>=X.X.X",
    "passlib[bcrypt]>=X.X.X",
    "python-multipart>=X.X.X",

    # HTTP クライアント
    "httpx>=X.X.X",
    "aiohttp>=X.X.X",

    # 設定・環境変数
    "python-dotenv>=X.X.X",

    # ロギング・監視
    "structlog>=X.X.X",
    "prometheus-client>=X.X.X",

    # ユーティリティ
    "python-slugify>=X.X.X",
    "pendulum>=X.X.X",  # 日時処理
]

[project.optional-dependencies]
backend = [
    # 開発ツール
    "httpie>=X.X.X",

    # テスト
    "pytest-asyncio>=X.X.X",
    "pytest-mock>=X.X.X",
    "factory-boy>=X.X.X",
    "freezegun>=X.X.X",

    # データベーステスト
    "pytest-postgresql>=X.X.X",

    # APIドキュメント生成
    "mkdocs>=X.X.X",
    "mkdocs-material>=X.X.X",
]
```

## プロジェクト構造（一例。必要に応じて省略・追加）

```
backend-project/
├── src/
│   └── project_name/
│       ├── api/                # API エンドポイント
│       │   ├── __init__.py
│       │   ├── deps.py         # 依存性注入
│       │   ├── routes/         # ルート定義
│       │   │   ├── __init__.py
│       │   │   ├── auth.py
│       │   │   ├── users.py
│       │   │   └── health.py
│       │   └── middleware/     # ミドルウェア
│       │       ├── __init__.py
│       │       ├── auth.py
│       │       ├── cors.py
│       │       └── logging.py
│       ├── core/               # コア設定
│       │   ├── __init__.py
│       │   ├── config.py       # アプリケーション設定
│       │   ├── security.py     # セキュリティ関連
│       │   └── exceptions.py   # カスタム例外
│       ├── db/                 # データベース関連
│       │   ├── __init__.py
│       │   ├── base.py         # Base model
│       │   ├── session.py      # DB セッション
│       │   └── models/         # SQLAlchemy モデル
│       │       ├── __init__.py
│       │       ├── user.py
│       │       └── base.py
│       ├── schemas/            # Pydantic スキーマ
│       │   ├── __init__.py
│       │   ├── user.py
│       │   └── common.py
│       ├── services/           # ビジネスロジック
│       │   ├── __init__.py
│       │   ├── user_service.py
│       │   └── auth_service.py
│       └── utils/              # ユーティリティ
│           ├── __init__.py
│           ├── logger.py
│           └── helpers.py
├── migrations/                 # Alembic マイグレーション
├── tests/
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_db/
├── scripts/                    # 運用スクリプト
│   ├── init_db.py
│   └── create_superuser.py
├── docker-compose.yml          # 開発環境
├── Dockerfile
└── .env.example
```

## FastAPI アプリケーション設定

### メインアプリケーション

```python
# src/project_name/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

from project_name.api.routes import auth, users, health
from project_name.api.middleware.cors import setup_cors
from project_name.api.middleware.logging import setup_logging
from project_name.core.config import get_settings
from project_name.core.exceptions import CustomException
from project_name.db.session import engine

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # 起動時
    logger.info("Starting up application")
    yield
    # 終了時
    logger.info("Shutting down application")
    await engine.dispose()

def create_app() -> FastAPI:
    """FastAPIアプリケーションファクトリー"""
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ミドルウェア設定
    setup_cors(app)
    setup_logging(app)

    # ルート設定
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(users.router, prefix="/users", tags=["users"])

    # グローバル例外ハンドラー
    @app.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "error_code": exc.error_code}
        )

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
```

### 設定管理

```python
# src/project_name/core/config.py
from functools import lru_cache
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # アプリケーション設定
    PROJECT_NAME: str = "Backend Project"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "FastAPI Backend Template"
    DEBUG: bool = False

    # サーバー設定
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # セキュリティ設定
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # データベース設定
    DATABASE_URL: str

    # CORS設定
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # ログ設定
    LOG_LEVEL: str = "INFO"

    # 外部サービス設定
    REDIS_URL: str | None = None
    CELERY_BROKER_URL: str | None = None

    # メール設定
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### データベース設定

```python
# src/project_name/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from project_name.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """データベースセッション依存性"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

```python
# src/project_name/db/base.py
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class TimestampMixin:
    """タイムスタンプミックスイン"""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BaseModel(Base, TimestampMixin):
    """ベースモデル"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
```

### Pydantic スキーマ

```python
# src/project_name/schemas/common.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class TimestampSchema(BaseModel):
    """タイムスタンプスキーマ"""
    created_at: datetime
    updated_at: datetime | None = None

class BaseResponse(BaseModel):
    """基本レスポンススキーマ"""
    success: bool = True
    message: str = "Success"

class ErrorResponse(BaseModel):
    """エラーレスポンススキーマ"""
    success: bool = False
    message: str
    error_code: str | None = None
    details: dict | None = None

class PaginationParams(BaseModel):
    """ページネーションパラメータ"""
    page: int = 1
    size: int = 10

    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
    )

class PaginatedResponse(BaseResponse):
    """ページネーションレスポンス"""
    data: list
    pagination: dict
```

```python
# src/project_name/schemas/user.py
from pydantic import BaseModel, EmailStr, ConfigDict
from project_name.schemas.common import TimestampSchema

class UserBase(BaseModel):
    """ユーザーベーススキーマ"""
    email: EmailStr
    username: str
    full_name: str | None = None
    is_active: bool = True

class UserCreate(UserBase):
    """ユーザー作成スキーマ"""
    password: str

class UserUpdate(BaseModel):
    """ユーザー更新スキーマ"""
    email: EmailStr | None = None
    username: str | None = None
    full_name: str | None = None
    is_active: bool | None = None

class UserInDB(UserBase, TimestampSchema):
    """データベース内ユーザースキーマ"""
    id: int
    hashed_password: str

    model_config = ConfigDict(from_attributes=True)

class User(UserBase, TimestampSchema):
    """ユーザーレスポンススキーマ"""
    id: int

    model_config = ConfigDict(from_attributes=True)
```

### 認証・セキュリティ

```python
# src/project_name/core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from project_name.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワード検証"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """パスワードハッシュ化"""
    return pwd_context.hash(password)

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
) -> str:
    """アクセストークン作成"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> dict:
    """トークン検証"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
```

### API エンドポイント例

```python
# src/project_name/api/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from project_name.db.session import get_db
from project_name.schemas.user import User, UserCreate, UserUpdate
from project_name.schemas.common import BaseResponse, PaginationParams
from project_name.services.user_service import UserService
from project_name.api.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """ユーザー作成"""
    user_service = UserService(db)
    return await user_service.create_user(user_data)

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """現在のユーザー情報取得"""
    return current_user

@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """現在のユーザー情報更新"""
    user_service = UserService(db)
    return await user_service.update_user(current_user.id, user_update)

@router.get("/", response_model=list[User])
async def list_users(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ユーザー一覧取得"""
    user_service = UserService(db)
    return await user_service.list_users(
        offset=(pagination.page - 1) * pagination.size,
        limit=pagination.size
    )
```

### サービス層

```python
# src/project_name/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from project_name.db.models.user import User as UserModel
from project_name.schemas.user import UserCreate, UserUpdate, User
from project_name.core.security import get_password_hash

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """ユーザー作成"""
        # 既存ユーザーチェック
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # パスワードハッシュ化
        hashed_password = get_password_hash(user_data.password)

        # ユーザー作成
        db_user = UserModel(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=user_data.is_active,
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)

        return User.model_validate(db_user)

    async def get_user_by_email(self, email: str) -> UserModel | None:
        """メールアドレスでユーザー取得"""
        result = await self.db.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> UserModel | None:
        """IDでユーザー取得"""
        result = await self.db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        """ユーザー更新"""
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        await self.db.commit()
        await self.db.refresh(db_user)

        return User.model_validate(db_user)

    async def list_users(
        self,
        offset: int = 0,
        limit: int = 10
    ) -> list[User]:
        """ユーザー一覧取得"""
        result = await self.db.execute(
            select(UserModel)
            .offset(offset)
            .limit(limit)
            .order_by(UserModel.created_at.desc())
        )
        db_users = result.scalars().all()
        return [User.model_validate(user) for user in db_users]
```

## よく使うコマンド

```bash
# 開発サーバー起動
uv run uvicorn src.project_name.main:app --reload --host 0.0.0.0 --port 8000

# マイグレーション作成
uv run alembic revision --autogenerate -m "Add user table"

# マイグレーション実行
uv run alembic upgrade head

# マイグレーション履歴確認
uv run alembic history

# データベース初期化スクリプト実行
uv run python scripts/init_db.py

# スーパーユーザー作成
uv run python scripts/create_superuser.py

# API テスト
http GET localhost:8000/docs  # Swagger UI
http GET localhost:8000/health  # ヘルスチェック

# HTTPie を使ったAPI テスト例
http POST localhost:8000/auth/login email=test@example.com password=password
http GET localhost:8000/users/me Authorization:"Bearer YOUR_TOKEN"

# Docker を使った開発環境
docker-compose up -d  # バックグラウンドで起動
docker-compose logs -f api  # ログ監視
docker-compose down  # 停止
```

## テスト

### テスト設定

```python
# tests/conftest.py
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from project_name.main import create_app
from project_name.db.base import Base
from project_name.db.session import get_db
from project_name.core.config import get_settings

settings = get_settings()

# テスト用データベースURL
TEST_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncio://")
TEST_DATABASE_URL += "_test"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session(db_engine):
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

### API テスト例

```python
# tests/test_api/test_users.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    """ユーザー作成テスト"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }

    response = await client.post("/users/", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data
    assert "hashed_password" not in data  # パスワードが含まれていないことを確認

@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    """ユーザーログインテスト"""
    # まずユーザーを作成
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    await client.post("/users/", json=user_data)

    # ログインテスト
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }

    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

## Docker設定

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY pyproject.toml uv.lock ./
RUN pip install uv
RUN uv sync --frozen

# アプリケーションコード
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY scripts/ ./scripts/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.project_name.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: 'X.X'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncio://postgres:password@db:5432/project_db
      - SECRET_KEY=your-secret-key-here
      - DEBUG=true
    depends_on:
      - db
      - redis
    volumes:
      - ./src:/app/src
      - ./migrations:/app/migrations

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: project_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## プロダクション考慮事項

### パフォーマンス最適化

```python
# src/project_name/api/middleware/cache.py
from fastapi import Request, Response
from functools import wraps
import redis.asyncio as redis
import json

class CacheMiddleware:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def cache_response(self, expire: int = 300):
        """レスポンスキャッシュデコレータ"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # キャッシュキー生成
                cache_key = f"api:{func.__name__}:{hash(str(kwargs))}"

                # キャッシュから取得
                cached = await self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)

                # 関数実行
                result = await func(*args, **kwargs)

                # キャッシュに保存
                await self.redis.setex(
                    cache_key,
                    expire,
                    json.dumps(result, default=str)
                )

                return result
            return wrapper
        return decorator
```

### 監視・ログ

```python
# src/project_name/utils/logger.py
import structlog
import logging.config

def setup_logging():
    """構造化ログ設定"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
```
