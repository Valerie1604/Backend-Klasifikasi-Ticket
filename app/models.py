from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.sql import func
from .database import Base
import enum

# Definisi Enum untuk Role agar konsisten
class UserRole(str, enum.Enum):
    MAHASISWA = "mahasiswa"
    PEGAWAI = "pegawai/dosen"
    SUPER_ADMIN = "super admin"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(150), nullable=True)
    instansi = Column(String(150), nullable=True)
    tanggal_pengajuan = Column(String(50), nullable=True)
    masalah = Column(String(300), nullable=False)
    deskripsi = Column(Text, nullable=True)
    category = Column(String(150), nullable=True)
    status = Column(String(50), default="Pengajuan")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # --- TAMBAHKAN BAGIAN INI ---
    @property
    def nomor_resi(self):
        # Format id menjadi 5 digit dengan awalan TCK-
        # Contoh: ID 1 -> TCK-00001, ID 23 -> TCK-00023
        return f"TCK-{self.id:05d}"

# --- Tambahan Model User ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(50), unique=True, index=True, nullable=False) # Ini untuk NIM atau NIP
    password = Column(String(255), nullable=False) # Password ter-hash
    nama_lengkap = Column(String(150))
    role = Column(String(50), default=UserRole.MAHASISWA) # Role user
    created_at = Column(DateTime(timezone=True), server_default=func.now())