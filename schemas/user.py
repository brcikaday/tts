from pydantic import BaseModel, EmailStr, ConfigDict, model_validator

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    name: str
    password: str


class UserSettings(BaseModel):
    darkMode: bool
    autoPlay: bool
    highQuality: bool


class UserResponse(UserBase):
    id: int
    name: str
    role: str
    settings: UserSettings

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def _assemble_settings(cls, data):
        # The User ORM model stores dark_mode/auto_play/high_quality as flat
        # columns; assemble them into the nested "settings" shape the API
        # contract expects before field validation runs.
        if hasattr(data, "dark_mode"):
            return {
                "id": data.id,
                "name": data.name,
                "email": data.email,
                "role": data.role,
                "settings": {
                    "darkMode": data.dark_mode,
                    "autoPlay": data.auto_play,
                    "highQuality": data.high_quality,
                },
            }
        return data

class UserLogin(UserBase):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user : UserResponse

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    document_id: int
    title: str
    source_type: str
    extracted_text: str
    file_name: str
    text: str
    file_size: int
    file_type: str
    word_count: int

    model_config = ConfigDict(from_attributes=True)
