from fastapi import FastAPI, Depends, HTTPException, status, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from . import models, schemas, crud, security
from .database import SessionLocal, engine
from .model_loader import ModelWrapper
import os

# DB INIT
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ticketing Classifier API")

# CORS setup
# PENTING: Jika pakai Cookie, allow_origins TIDAK BOLEH ["*"]. 
# Harus spesifik url frontend, misal "http://localhost:3000" atau "http://localhost:5173"
origins = [
    "http://localhost:3000", 
    "http://localhost:5173",
    "http://127.0.0.1:3000"
] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # Wajib True agar cookie bisa dikirim
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Load Model
MODEL_DIR = os.environ.get("MODEL_DIR", "app/model")
model_wrapper = ModelWrapper(MODEL_DIR)

# ==========================================
# AUTHENTICATION ROUTES (COOKIES VERSION)
# ==========================================

@app.post("/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_identifier(db, identifier=user.identifier)
    if db_user:
        raise HTTPException(status_code=400, detail="NIM/NIP sudah terdaftar")
    
    valid_roles = ["mahasiswa", "pegawai", "admin"]
    if user.role not in valid_roles:
         raise HTTPException(status_code=400, detail=f"Role harus salah satu dari: {valid_roles}")

    return crud.create_user(db=db, user=user)

@app.post("/login")
def login(response: Response, login_req: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Login user dan set HttpOnly Cookie.
    Tidak lagi mengembalikan token di body response.
    """
    user = crud.get_user_by_identifier(db, identifier=login_req.identifier)
    
    if not user or not security.verify_password(login_req.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NIM/NIP atau Password salah",
        )
    
    # Buat Token
    access_token_expires = security.timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.identifier, "role": user.role}, 
        expires_delta=access_token_expires
    )
    
    # SET COOKIE
    # httponly=True -> JavaScript tidak bisa baca cookie ini (Aman dari XSS)
    # samesite="lax" -> Proteksi CSRF standar
    # secure=False -> Gunakan False untuk localhost (http). Ganti True jika sudah https (production)
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True, 
        max_age=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False 
    )
    
    return {
        "message": "Login berhasil", 
        "role": user.role,
        "identifier": user.identifier,
        "nama_lengkap": user.nama_lengkap
    }

@app.post("/logout")
def logout(response: Response):
    """
    Logout dengan cara menghapus cookie access_token.
    """
    response.delete_cookie(key="access_token")
    return {"message": "Logout berhasil"}

# Dependency untuk mendapatkan user dari COOKIE
def get_current_user(request: Request, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    # Ambil token dari Cookie
    token_cookie = request.cookies.get("access_token")
    
    if not token_cookie:
        raise credentials_exception

    # Token biasanya formatnya "Bearer eyJhbG..." kita perlu split
    try:
        scheme, token = token_cookie.split()
        if scheme.lower() != "bearer":
            raise credentials_exception
    except ValueError:
        # Jika format tidak sesuai (misal tidak ada "Bearer ")
        raise credentials_exception

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

@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# ... (Sisa kode ke bawah sama persis seperti sebelumnya) ...
# ... (Route predict, tickets, create_ticket, dll tetap sama) ...
# Cukup pastikan route yang butuh login menggunakan Depends(get_current_user)

@app.post("/predict", response_model=schemas.PredictResponse)
def predict(req: schemas.PredictRequest):
    if not req.text or req.text.strip() == "":
        raise HTTPException(status_code=400, detail="Text is empty")
    category, scores = model_wrapper.predict(req.text)
    return {"category": category, "scores": scores}

@app.post("/tickets", response_model=schemas.TicketOut)
def create_ticket(
    ticket: schemas.TicketCreate, 
    db: Session = Depends(get_db),
    # Uncomment jika ingin protect:
    # current_user: models.User = Depends(get_current_user) 
):
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
    db: Session = Depends(get_db)
):
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