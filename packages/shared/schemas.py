from pydantic import BaseModel, ConfigDict, EmailStr, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class SignUpResponse(BaseModel):
    detail: str
    verification_token: str | None = None


class VerifyEmailRequest(BaseModel):
    token: str


class SongCandidate(BaseModel):
    source_provider: str = "youtube"
    source_id: str
    title: str
    channel: str
    duration_sec: int | None = None
    confidence_score: float


class SearchResponse(BaseModel):
    candidates: list[SongCandidate]
    scoring_meta: dict


class ImportSongRequest(BaseModel):
    source_provider: str = "youtube"
    source_id: str
    title: str | None = None
    artist: str | None = None
    candidate_meta: dict = Field(default_factory=dict)


class SongOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    artist: str
    album: str | None = None
    duration_sec: int | None = None
    source_provider: str
    source_id: str
    source_channel: str | None = None
    quality_score: float | None = None
    storage_key: str | None = None
    codec: str | None = None
    bitrate_kbps: int | None = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    source_provider: str
    source_id: str
    status: str
    failure_reason: str | None = None
