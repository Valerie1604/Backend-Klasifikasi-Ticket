from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    category: str
    scores: Dict[str, float] = {}

# Ticket create request
class TicketCreate(BaseModel):
    nama: Optional[str] = None
    instansi: Optional[str] = None
    tanggal_pengajuan: Optional[str] = None
    masalah: str
    deskripsi: Optional[str] = None
    category: Optional[str] = None  # optional, can be provided by frontend

class TicketUpdateCategory(BaseModel):
    category: str

class TicketUpdateStatus(BaseModel):
    status: str

class TicketOut(BaseModel):
    id: int
    nama: Optional[str]
    instansi: Optional[str]
    tanggal_pengajuan: Optional[str]
    masalah: str
    deskripsi: Optional[str]
    category: Optional[str]
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
