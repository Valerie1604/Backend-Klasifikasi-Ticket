from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from . import models, schemas, crud, security # Import security
from .database import SessionLocal, engine
from .model_loader import ModelWrapper
import os

# DB INIT
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ticketing Classifier API")

# CORS setup (Tetap sama)
origins = ["*"] # Buka untuk semua origin sementara development
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Dependency DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Load Model (Tetap sama)
MODEL_DIR = os.environ.get("MODEL_DIR", "app/model")
model_wrapper = ModelWrapper(MODEL_DIR)

# Auth Configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.post("/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Endpoint untuk mendaftarkan user baru (Mahasiswa/Pegawai/Super Admin).
    Gunakan ini untuk membuat user pertama kali.
    """
    db_user = crud.get_user_by_identifier(db, identifier=user.identifier)
    if db_user:
        raise HTTPException(status_code=400, detail="NIM/NIP sudah terdaftar")
    
    # Validasi Role
    valid_roles = ["mahasiswa", "pegawai/dosen", "super admin"]
    if user.role not in valid_roles:
         raise HTTPException(status_code=400, detail=f"Role harus salah satu dari: {valid_roles}")

    return crud.create_user(db=db, user=user)

@app.post("/login", response_model=schemas.Token)
def login(login_req: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Endpoint Login. Input: NIM/NIP (identifier) dan Password.
    Output: Access Token JWT dan Role.
    """
    user = crud.get_user_by_identifier(db, identifier=login_req.identifier)
    
    # Cek apakah user ada dan password benar
    if not user or not security.verify_password(login_req.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NIM/NIP atau Password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Buat Token
    access_token_expires = security.timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.identifier, "role": user.role}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": user.role,
        "identifier": user.identifier
    }

# Dependency untuk mendapatkan user yang sedang login (Proteksi Route)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        identifier: str = payload.get("sub")
        role: str = payload.get("role")
        if identifier is None:
            raise credentials_exception
        token_data = schemas.TokenData(identifier=identifier, role=role)
    except JWTError:
        raise credentials_exception
        
    user = crud.get_user_by_identifier(db, identifier=token_data.identifier)
    if user is None:
        raise credentials_exception
    return user

# ==========================================
# TICKETING ROUTES
# ==========================================

# Endpoint contoh yang diproteksi (Hanya user login yang bisa akses)
@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# ======== ROUTES TICKET LAMA (TETAP SAMA) ========
# Anda bisa menambahkan Depends(get_current_user) pada endpoint di bawah 
# jika ingin mewajibkan login untuk membuat/melihat tiket.

@app.post("/predict", response_model=schemas.PredictResponse)
def predict(req: schemas.PredictRequest):
    # ... logic lama ...
    if not req.text or req.text.strip() == "":
        raise HTTPException(status_code=400, detail="Text is empty")
    category, scores = model_wrapper.predict(req.text)
    return {"category": category, "scores": scores}

@app.post("/tickets", response_model=schemas.TicketOut)
def create_ticket(
    ticket: schemas.TicketCreate, 
    db: Session = Depends(get_db),
    # Uncomment baris bawah ini jika pembuatan tiket WAJIB login:
    # current_user: models.User = Depends(get_current_user) 
):
    # Jika frontend tidak mengirim category → auto predict
    if not ticket.category:
        text_for_pred = ticket.masalah + (". " + ticket.deskripsi if ticket.deskripsi else "")
        category, _ = model_wrapper.predict(text_for_pred)
        ticket.category = category

    db_ticket = crud.create_ticket(db, ticket)
    return db_ticket

@app.get("/tickets", response_model=list[schemas.TicketOut])
def list_tickets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tickets = crud.get_tickets(db, skip=skip, limit=limit)
    return tickets

@app.get("/tickets/{ticket_id}", response_model=schemas.TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.put("/tickets/{ticket_id}/category", response_model=schemas.TicketOut)
def update_category(
    ticket_id: int, 
    payload: schemas.TicketUpdateCategory, 
    db: Session = Depends(get_db),
    # Disarankan endpoint ini diproteksi khusus Admin/Pegawai
    # current_user: models.User = Depends(get_current_user) 
):
    # Logic tambahan untuk cek role admin bisa ditaruh di sini
    ticket = crud.update_ticket_category(db, ticket_id, payload.category)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.put("/tickets/{ticket_id}/status", response_model=schemas.TicketOut)
def update_status(ticket_id: int, payload: schemas.TicketUpdateStatus, db: Session = Depends(get_db)):
    ticket = crud.update_ticket_status(db, ticket_id, payload.status)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket