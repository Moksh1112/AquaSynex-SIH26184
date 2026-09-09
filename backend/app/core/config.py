import os

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/sih26184")
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    JWT_SECRET = os.getenv("JWT_SECRET", "secret")

settings = Settings()
