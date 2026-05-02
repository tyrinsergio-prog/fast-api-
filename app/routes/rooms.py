from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import schemas, crud, auth
from app.database import get_db

router = APIRouter(prefix="/rooms", tags=["Rooms"])

@router.get("/", response_model=List[schemas.RoomResponse])
def get_rooms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_rooms(db, skip=skip, limit=limit)

@router.get("/{room_id}", response_model=schemas.RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = crud.get_room_by_id(db, room_id)
    if not room or not room.is_active:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@router.post("/", response_model=schemas.RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(room: schemas.RoomCreate, db: Session = Depends(get_db), 
                current_user=Depends(auth.get_current_user)):
    return crud.create_room(db, room)

@router.put("/{room_id}", response_model=schemas.RoomResponse)
def update_room(room_id: int, room_update: schemas.RoomUpdate, db: Session = Depends(get_db),
                current_user=Depends(auth.get_current_user)):
    room = crud.update_room(db, room_id, room_update)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: int, db: Session = Depends(get_db),
                current_user=Depends(auth.get_current_user)):
    if not crud.delete_room(db, room_id):
        raise HTTPException(status_code=404, detail="Room not found")