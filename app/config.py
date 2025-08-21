from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    app_name: str = "Task Manager API"
    version: str = "1.0.0"
    description: str = "API для управления задачами с CRUD операциями"
    
    # Database settings
    database_host: str = "localhost"
    database_port: str = "5432"
    database_name: str = "task_manager"
    database_user: str = "postgres"
    database_password: str = "postgres"
    
    @property
    def database_url(self):
        if os.getenv("TESTING"):
            return "sqlite:///:memory:"
        return f"postgresql+psycopg2://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()