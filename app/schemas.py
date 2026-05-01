from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, List

# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=1)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Room schemas
class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(..., ge=1, le=100)
    location: str = Field(..., min_length=1, max_length=200)
    has_projector: bool = False
    has_whiteboard: bool = False

class RoomCreate(RoomBase):
    pass

class RoomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None
    has_projector: Optional[bool] = None
    has_whiteboard: Optional[bool] = None
    is_active: Optional[bool] = None

class RoomResponse(RoomBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True

# Booking schemas
class BookingBase(BaseModel):
    room_id: int
    title: str = Field(..., min_length=1, max_length=200)
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    
    @validator('start_time', 'end_time', pre=True)
    def parse_datetime(cls, value):
        """Поддержка различных форматов даты"""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # Пробуем разные форматы
            formats = [
                "%Y-%m-%dT%H:%M:%S",  # 2024-12-25T10:00:00
                "%Y-%m-%d %H:%M:%S",  # 2024-12-25 10:00:00
                "%Y-%m-%dT%H:%M:%S.%f",  # 2024-12-25T10:00:00.000
                "%Y-%m-%d %H:%M:%S.%f",  # 2024-12-25 10:00:00.000
                "%Y-%m-%dT%H:%M:%SZ",  # 2024-12-25T10:00:00Z
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Invalid datetime format: {value}. Use format: 2024-12-25T10:00:00")
        return value
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class BookingCreate(BookingBase):
    pass

class BookingResponse(BookingBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class BookingWithDetails(BookingResponse):
    room: RoomResponse
    user: UserResponse

# Conflict check schema
class ConflictCheckRequest(BaseModel):
    room_id: int
    start_time: datetime
    end_time: datetime
    exclude_booking_id: Optional[int] = None
    
    @validator('start_time', 'end_time', pre=True)
    def parse_datetime(cls, value):
        """Поддержка различных форматов даты"""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Invalid datetime format: {value}")
        return value

class ConflictCheckResponse(BaseModel):
    has_conflict: bool
    conflicting_bookings: List[BookingResponse]

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None