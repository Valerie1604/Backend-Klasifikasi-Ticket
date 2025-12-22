from sqlalchemy.orm import Session
from .security import get_password_hash
from . import models, schemas

def create_ticket(db: Session, ticket: schemas.TicketCreate, user_id: int):
    db_ticket = models.Ticket(
        nama=ticket.nama,
        instansi=ticket.instansi,
        tanggal_pengajuan=ticket.tanggal_pengajuan,
        masalah=ticket.masalah,
        deskripsi=ticket.deskripsi,
        category=ticket.category or None,
        status="Pengajuan",
        owner_id=user_id  # Simpan ID pemilik
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def get_ticket(db: Session, ticket_id: int, user: models.User):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    
    if not ticket:
        return None
        
    # Validasi: Jika bukan admin DAN bukan pemilik tiket, anggap tidak ada
    if user.role != "admin" and ticket.owner_id != user.id:
        return None
        
    return ticket

def get_tickets(db: Session, user: models.User, skip: int = 0, limit: int = 100):
    # Jika Admin, ambil semua
    if user.role == "admin":
        return db.query(models.Ticket).order_by(models.Ticket.created_at.desc()).offset(skip).limit(limit).all()
    
    # Jika User biasa, ambil hanya milik sendiri
    return db.query(models.Ticket).filter(models.Ticket.owner_id == user.id).order_by(models.Ticket.created_at.desc()).offset(skip).limit(limit).all()

def update_ticket_category(db: Session, ticket_id: int, new_category: str):
    # Note: Update biasanya dilakukan admin/sistem, jadi sementara tidak diprotect owner
    # Atau bisa gunakan get_ticket dengan user=admin jika ingin bebas
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        return None
    ticket.category = new_category
    db.commit()
    db.refresh(ticket)
    return ticket

def update_ticket_status(db: Session, ticket_id: int, new_status: str):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        return None
    ticket.status = new_status
    db.commit()
    db.refresh(ticket)
    return ticket

# === CRUD USER ===

def get_user_by_identifier(db: Session, identifier: str):
    return db.query(models.User).filter(models.User.identifier == identifier).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        identifier=user.identifier,
        password=hashed_password,
        nama_lengkap=user.nama_lengkap,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user