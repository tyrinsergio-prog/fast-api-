from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import schemas, crud, auth
from app.database import get_db

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.get("/", response_model=List[schemas.BookingResponse])
def get_bookings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                 current_user=Depends(auth.get_current_user)):
    return crud.get_bookings(db, skip=skip, limit=limit, user_id=current_user.id)

@router.get("/{booking_id}", response_model=schemas.BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db),
                current_user=Depends(auth.get_current_user)):
    booking = crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this booking")
    return booking

@router.post("/", response_model=schemas.BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db),
                   current_user=Depends(auth.get_current_user)):
    try:
        return crud.create_booking(db, booking, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.put("/{booking_id}", response_model=schemas.BookingResponse)
def update_booking(booking_id: int, booking_update: schemas.BookingCreate, 
                   db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    try:
        booking = crud.update_booking(db, booking_id, booking_update, current_user.id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, db: Session = Depends(get_db),
                   current_user=Depends(auth.get_current_user)):
    try:
        if not crud.delete_booking(db, booking_id, current_user.id):
            raise HTTPException(status_code=404, detail="Booking not found")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))