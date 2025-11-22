from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(150), nullable=True)
    instansi = Column(String(150), nullable=True)
    tanggal_pengajuan = Column(String(50), nullable=True)  # simpan sebagai string 'YYYY-MM-DD' atau sesuai input
    masalah = Column(String(300), nullable=False)
    deskripsi = Column(Text, nullable=True)
    category = Column(String(150), nullable=True)
    status = Column(String(50), default="Pengajuan")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
