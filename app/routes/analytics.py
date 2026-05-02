from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app import schemas, crud, auth, models
from app.database import get_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.post("/check-conflict", response_model=schemas.ConflictCheckResponse)
def check_conflict(request: schemas.ConflictCheckRequest, db: Session = Depends(get_db),
                   current_user=Depends(auth.get_current_user)):
    """Проверка конфликтов бронирования - бизнес-задача с алгоритмическим компонентом"""
    conflicts = crud.check_conflict(
        db, request.room_id, request.start_time, request.end_time, request.exclude_booking_id
    )
    return {
        "has_conflict": len(conflicts) > 0,
        "conflicting_bookings": conflicts
    }

@router.get("/room-utilization")
def get_room_utilization(db: Session = Depends(get_db), 
                         current_user=Depends(auth.get_current_user)):
    """Расчет загруженности переговорных комнат за последние 30 дней (алгоритмический компонент)"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    rooms = crud.get_rooms(db, limit=100)
    utilization = []
    
    for room in rooms:
        # Получаем все бронирования комнаты за период
        bookings = db.query(models.Booking).filter(
            and_(
                models.Booking.room_id == room.id,
                models.Booking.start_time >= start_date,
                models.Booking.end_time <= end_date
            )
        ).all()
        
        # Вычисляем общее время бронирований в часах
        total_booking_hours = sum(
            (booking.end_time - booking.start_time).total_seconds() / 3600
            for booking in bookings
        )
        
        # Всего часов в периоде (30 дней * 9 рабочих часов в день)
        # Предполагаем рабочий день с 9:00 до 18:00
        working_hours_per_day = 9
        total_available_hours = 30 * working_hours_per_day
        
        utilization_percentage = (total_booking_hours / total_available_hours * 100) if total_available_hours > 0 else 0
        
        # Рекомендация по оптимизации (алгоритмический компонент)
        recommendation = ""
        if utilization_percentage > 80:
            recommendation = f"Комната {room.name} перегружена. Рекомендуется добавить переговорные или оптимизировать время встреч."
        elif utilization_percentage < 20 and room.is_active:
            recommendation = f"Комната {room.name} недогружена. Рекомендуется провести маркетинговую кампанию или пересмотреть назначение."
        else:
            recommendation = f"Загруженность комнаты {room.name} оптимальная."
        
        utilization.append({
            "room_id": room.id,
            "room_name": room.name,
            "capacity": room.capacity,
            "total_bookings": len(bookings),
            "total_booking_hours": round(total_booking_hours, 2),
            "utilization_percentage": round(utilization_percentage, 2),
            "recommendation": recommendation
        })
    
    # Сортируем по загруженности
    utilization.sort(key=lambda x: x["utilization_percentage"], reverse=True)
    
    return {
        "period_days": 30,
        "start_date": start_date,
        "end_date": end_date,
        "rooms_utilization": utilization
    }

@router.get("/user-booking-stats")
def get_user_booking_stats(db: Session = Depends(get_db),
                           current_user=Depends(auth.get_current_user)):
    """Статистика бронирований пользователя с рекомендациями (алгоритмический компонент)"""
    # Получаем все бронирования пользователя за все время
    user_bookings = db.query(models.Booking).filter(
        models.Booking.user_id == current_user.id
    ).all()
    
    # Анализ времени бронирований
    booking_hours = {}
    for booking in user_bookings:
        hour = booking.start_time.hour
        booking_hours[hour] = booking_hours.get(hour, 0) + 1
    
    # Находим самое популярное время для бронирований
    most_popular_hour = max(booking_hours.items(), key=lambda x: x[1])[0] if booking_hours else None
    
    # Рекомендация
    recommendation = ""
    if most_popular_hour:
        if most_popular_hour < 12:
            recommendation = f"Вы чаще бронируете в утренние часы (около {most_popular_hour}:00). Попробуйте бронировать после обеда для большей доступности комнат."
        elif most_popular_hour > 16:
            recommendation = f"Вы предпочитаете бронировать после 16:00. Обратите внимание на утренние часы, они часто менее загружены."
        else:
            recommendation = f"Ваше популярное время бронирования - {most_popular_hour}:00. Это среднее время, комнаты могут быть загружены."
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "total_bookings": len(user_bookings),
        "average_booking_duration_hours": round(
            sum((b.end_time - b.start_time).total_seconds() / 3600 for b in user_bookings) / len(user_bookings), 2
        ) if user_bookings else 0,
        "most_popular_booking_hour": most_popular_hour,
        "booking_hours_distribution": booking_hours,
        "recommendation": recommendation
    }