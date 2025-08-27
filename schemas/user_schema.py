from pydantic import BaseModel

class UserCreateRequest(BaseModel):
    user_id: str
    password: str
    passwordCheck: str
    user_name: str
    permission_code: str
    use_yn: str

class UserUpdateRequest(BaseModel):
    user_name: str
    permission_code: str
    use_yn: str

class PasswordChangeRequest(BaseModel):
    new_password: str
