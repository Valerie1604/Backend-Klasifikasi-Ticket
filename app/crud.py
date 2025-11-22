from sqlalchemy.orm import Session
from . import models, schemas

def create_ticket(db: Session, ticket: schemas.TicketCreate):
    db_ticket = models.Ticket(
        nama=ticket.nama,
        instansi=ticket.instansi,
        tanggal_pengajuan=ticket.tanggal_pengajuan,
        masalah=ticket.masalah,
        deskripsi=ticket.deskripsi,
        category=ticket.category or None,
        status="Pengajuan"
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def get_ticket(db: Session, ticket_id: int):
    return db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

def get_tickets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Ticket).order_by(models.Ticket.created_at.desc()).offset(skip).limit(limit).all()

def update_ticket_category(db: Session, ticket_id: int, new_category: str):
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        return None
    ticket.category = new_category
    db.commit()
    db.refresh(ticket)
    return ticket

def update_ticket_status(db: Session, ticket_id: int, new_status: str):
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        return None
    ticket.status = new_status
    db.commit()
    db.refresh(ticket)
    return ticket
