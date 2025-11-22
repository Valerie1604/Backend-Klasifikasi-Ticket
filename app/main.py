from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import SessionLocal, engine
from .model_loader import ModelWrapper
import os

# ----------------------------------------
# DB INIT
# ----------------------------------------
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ticketing Classifier API")

# ----------------------------------------
# CORS
# ----------------------------------------
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ----------------------------------------
# DB SESSION PER REQUEST
# ----------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------
# LOAD MODEL
# ----------------------------------------
MODEL_DIR = os.environ.get("MODEL_DIR", "app/model")
model_wrapper = ModelWrapper(MODEL_DIR)

# ----------------------------------------
# ROUTES
# ----------------------------------------

# ======== PREDICT CATEGORY ========
@app.post("/predict", response_model=schemas.PredictResponse)
def predict(req: schemas.PredictRequest):
    if not req.text or req.text.strip() == "":
        raise HTTPException(status_code=400, detail="Text is empty")

    category, scores = model_wrapper.predict(req.text)
    return {"category": category, "scores": scores}


# ======== CREATE TICKET ========
@app.post("/tickets", response_model=schemas.TicketOut)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):

    # jika frontend tidak mengirim category → auto predict
    if not ticket.category:
        text_for_pred = ticket.masalah + (". " + ticket.deskripsi if ticket.deskripsi else "")
        category, _ = model_wrapper.predict(text_for_pred)
        ticket.category = category

    db_ticket = crud.create_ticket(db, ticket)
    return db_ticket


# ======== LIST ALL TICKETS ========
@app.get("/tickets", response_model=list[schemas.TicketOut])
def list_tickets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tickets = crud.get_tickets(db, skip=skip, limit=limit)
    return tickets


# ======== GET ONE TICKET ========
@app.get("/tickets/{ticket_id}", response_model=schemas.TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


# ======== UPDATE CATEGORY (ADMIN) ========
@app.put("/tickets/{ticket_id}/category", response_model=schemas.TicketOut)
def update_category(ticket_id: int, payload: schemas.TicketUpdateCategory, db: Session = Depends(get_db)):
    ticket = crud.update_ticket_category(db, ticket_id, payload.category)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


# ======== UPDATE STATUS (ADMIN) ========
@app.put("/tickets/{ticket_id}/status", response_model=schemas.TicketOut)
def update_status(ticket_id: int, payload: schemas.TicketUpdateStatus, db: Session = Depends(get_db)):
    ticket = crud.update_ticket_status(db, ticket_id, payload.status)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket
