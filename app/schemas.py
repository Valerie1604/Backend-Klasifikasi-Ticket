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
    category: Optional[str] = None 

class TicketUpdateCategory(BaseModel):
    category: str

class TicketUpdateStatus(BaseModel):
    status: str

class TicketOut(BaseModel):
    id: int
    nomor_resi: str
    nama: Optional[str]
    instansi: Optional[str]
    tanggal_pengajuan: Optional[str]
    masalah: str
    deskripsi: Optional[str]
    category: Optional[str]
    status: str
    created_at: datetime
    owner_id: Optional[int] = None  # Tambahan field

    class Config:
        orm_mode = True

# === SCHEMA USER & LOGIN ===

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    identifier: str

class TokenData(BaseModel):
    identifier: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    identifier: str
    password: str

class UserCreate(BaseModel):
    identifier: str 
    password: str
    nama_lengkap: str
    role: str = "mahasiswa" 

class UserOut(BaseModel):
    id: int
    identifier: str
    nama_lengkap: str
    role: str
    created_at: datetime

    class Config:
        orm_mode = True