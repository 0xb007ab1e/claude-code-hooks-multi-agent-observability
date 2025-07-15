from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import time

class HookEvent(BaseModel):
    id: Optional[int] = None
    source_app: str
    session_id: str
    hook_event_type: str
    payload: Dict[str, Any]
    chat: Optional[List[Any]] = None
    summary: Optional[str] = None
    timestamp: Optional[int] = Field(default_factory=lambda: int(time.time() * 1000))


class FilterOptions(BaseModel):
    source_apps: List[str]
    session_ids: List[str]
    hook_event_types: List[str]


class ThemeColors(BaseModel):
    primary: str
    primaryHover: str
    primaryLight: str
    primaryDark: str
    bgPrimary: str
    bgSecondary: str
    bgTertiary: str
    bgQuaternary: str
    textPrimary: str
    textSecondary: str
    textTertiary: str
    textQuaternary: str
    borderPrimary: str
    borderSecondary: str
    borderTertiary: str
    accentSuccess: str
    accentWarning: str
    accentError: str
    accentInfo: str
    shadow: str
    shadowLg: str
    hoverBg: str
    activeBg: str
    focusRing: str


class Theme(BaseModel):
    id: str
    name: str
    displayName: str
    description: Optional[str] = None
    colors: ThemeColors
    isPublic: bool
    authorId: Optional[str] = None
    authorName: Optional[str] = None
    createdAt: int
    updatedAt: int
    tags: List[str]
    downloadCount: Optional[int] = 0
    rating: Optional[float] = None
    ratingCount: Optional[int] = 0


class ThemeSearchQuery(BaseModel):
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    authorId: Optional[str] = None
    isPublic: Optional[bool] = None
    sortBy: Optional[str] = 'name'
    sortOrder: Optional[str] = 'asc'
    limit: Optional[int] = 10
    offset: Optional[int] = 0


class ThemeValidationError(BaseModel):
    field: str
    message: str
    code: str


class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None
    validationErrors: Optional[List[ThemeValidationError]] = None


class EventCount(BaseModel):
    count: int


class HealthResponse(BaseModel):
    status: str
    timestamp: str
