from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List, Optional
from app import models, schemas
from app.auth import get_password_hash

# User CRUD
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    try:
        # Хешируем пароль
        hashed_password = get_password_hash(user.password)
        
        db_user = models.User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise Exception(f"Error creating user: {str(e)}")

# Room CRUD
def get_rooms(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Room).filter(models.Room.is_active == True).offset(skip).limit(limit).all()

def get_room_by_id(db: Session, room_id: int):
    return db.query(models.Room).filter(models.Room.id == room_id).first()

def create_room(db: Session, room: schemas.RoomCreate):
    db_room = models.Room(**room.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def update_room(db: Session, room_id: int, room_update: schemas.RoomUpdate):
    db_room = get_room_by_id(db, room_id)
    if not db_room:
        return None
    update_data = room_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_room, field, value)
    db.commit()
    db.refresh(db_room)
    return db_room

def delete_room(db: Session, room_id: int):
    db_room = get_room_by_id(db, room_id)
    if not db_room:
        return False
    db_room.is_active = False
    db.commit()
    return True

# Booking CRUD
def get_bookings(db: Session, skip: int = 0, limit: int = 100, user_id: Optional[int] = None):
    query = db.query(models.Booking)
    if user_id:
        query = query.filter(models.Booking.user_id == user_id)
    return query.order_by(models.Booking.start_time).offset(skip).limit(limit).all()

def get_booking_by_id(db: Session, booking_id: int):
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()

def check_conflict(db: Session, room_id: int, start_time: datetime, end_time: datetime, exclude_booking_id: Optional[int] = None):
    query = db.query(models.Booking).filter(
        and_(
            models.Booking.room_id == room_id,
            models.Booking.start_time < end_time,
            models.Booking.end_time > start_time
        )
    )
    if exclude_booking_id:
        query = query.filter(models.Booking.id != exclude_booking_id)
    return query.all()

def create_booking(db: Session, booking: schemas.BookingCreate, user_id: int):
    # Проверка времени
    if booking.start_time >= booking.end_time:
        raise ValueError("Start time must be before end time")
    
    # Проверка конфликта
    conflicts = check_conflict(db, booking.room_id, booking.start_time, booking.end_time)
    if conflicts:
        raise ValueError("Booking time conflicts with existing booking")
    
    db_booking = models.Booking(
        room_id=booking.room_id,
        title=booking.title,
        start_time=booking.start_time,
        end_time=booking.end_time,
        description=booking.description,
        user_id=user_id
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def update_booking(db: Session, booking_id: int, booking_update: schemas.BookingCreate, user_id: int):
    db_booking = get_booking_by_id(db, booking_id)
    if not db_booking:
        return None
    if db_booking.user_id != user_id:
        raise PermissionError("You can only update your own bookings")
    
    # Проверка времени
    if booking_update.start_time >= booking_update.end_time:
        raise ValueError("Start time must be before end time")
    
    # Проверка конфликта
    conflicts = check_conflict(db, booking_update.room_id, booking_update.start_time, 
                               booking_update.end_time, exclude_booking_id=booking_id)
    if conflicts:
        raise ValueError("Booking time conflicts with existing booking")
    
    db_booking.room_id = booking_update.room_id
    db_booking.title = booking_update.title
    db_booking.start_time = booking_update.start_time
    db_booking.end_time = booking_update.end_time
    db_booking.description = booking_update.description
    
    db.commit()
    db.refresh(db_booking)
    return db_booking

def delete_booking(db: Session, booking_id: int, user_id: int):
    db_booking = get_booking_by_id(db, booking_id)
    if not db_booking:
        return False
    if db_booking.user_id != user_id:
        raise PermissionError("You can only delete your own bookings")
    db.delete(db_booking)
    db.commit()
    return True