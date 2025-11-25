from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 1. 필수 항목 (Default 값을 지움 -> .env에 없으면 에러 발생)
    # 보안이 필요한 값들은 절대 코드에 적지 않습니다.
    DB_PATH: str
    
    API_SALT: str
    PASSWORD_SALT: str
    
    JWT_SECRET: str
    
    # 2. 선택 항목 (공개되어도 되거나, 변경이 적은 설정은 기본값 유지 가능)
    JWT_ALGORITHM: str
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    TOKEN_REFRESH_THRESHOLD_SECONDS: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 인스턴스 생성
# .env 파일이 없거나, 필수 변수가 빠져있으면 여기서 에러가 발생해서 서버가 안 켜집니다. (안전)
try:
    Config = Settings()
except Exception as e:
    print("❌ [설정 오류] .env 파일을 확인해주세요:", e)
    raise