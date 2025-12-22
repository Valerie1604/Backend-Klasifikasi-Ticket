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
    nomor_resi: str
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

# === SCHEMA USER & LOGIN ===

# Schema untuk Token response
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    identifier: str

# Schema data dalam Token
class TokenData(BaseModel):
    identifier: Optional[str] = None
    role: Optional[str] = None

# Schema untuk Input Login
class LoginRequest(BaseModel):
    identifier: str  # Input NIM atau NIP disini
    password: str

# Schema untuk membuat User baru (Register)
class UserCreate(BaseModel):
    identifier: str # NIM / NIP
    password: str
    nama_lengkap: str
    role: str = "mahasiswa" # Default role

# Schema untuk output User (tanpa password)
class UserOut(BaseModel):
    id: int
    identifier: str
    nama_lengkap: str
    role: str
    created_at: datetime

    class Config:
        orm_mode = True