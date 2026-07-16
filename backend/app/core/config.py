from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- 应用基础配置 ---
    APP_NAME: str = "IoT-Platform"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    SECRET_KEY: str = "change-me-to-a-random-secret-string-at-least-32-chars"

    # --- MySQL ---
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "iot_platform"
    DB_POOL_SIZE: int = 10
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False
    DB_SSL: bool = False  # 云数据库通常需要开启 SSL

    # --- Database type: "mysql" | "sqlite" ---
    DB_TYPE: str = "mysql"

    # --- Redis ---
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_SSL: bool = False
    REDIS_POOL_MAX_CONNECTIONS: int = 20

    # --- 服务端口 ---
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def database_url(self) -> str:
        if self.DB_TYPE == "sqlite":
            return "sqlite+aiosqlite:///./data/iot.db"
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
