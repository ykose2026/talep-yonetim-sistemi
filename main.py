# -*- coding: utf-8 -*-
"""
Created on Sat Oct  3 15:48:55 2026

@author: Bilgisayar
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import os
from google import genai
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime, timezone

app = FastAPI(
    title="Kurumsal Talep Yönetim Sistemi API",
    version="1.0.0",
    description="Yapay Zeka Destekli Kamu Kurumu Talep ve Yardım Masası Otomasyonu"
)

# Render üzerindeki PostgreSQL bağlantı adresini alıyoruz
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # SQLAlchemy uyumluluğu için postgres:// ifadesini postgresql:// yapıyoruz
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    # Lokal testlerinizde veya hata durumunda çökmemesi için fallback (SQLite)
    DATABASE_URL = "sqlite:///./local_test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Veritabanı Modeli (Talepler Tablosu)
class TalepModel(Base):
    __tablename__ = "Talepler"
    Id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    UserName = Column(String(100), nullable=False)
    Department = Column(String(100), nullable=False)
    Message = Column(Text, nullable=False)
    AiResponse = Column(Text, nullable=False)
    # Python 3.12+ standartlarına göre güncellenmiş utc zaman damgası
    CreatedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Tablo yoksa otomatik oluşturulur
Base.metadata.create_all(bind=engine)

# İstek gövdesi için Pydantic modeli
class ChatRequest(BaseModel):
    user_name: str
    department: str
    message: str

# FastAPI için Güvenli Veritabanı Oturum Bağımlılığı (Dependency Injection)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "Talep Yönetim ve AI Destek Masası",
        "docs_url": "/docs"
    }

@app.post("/api/chatbot/send")
async def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY tanımlanmamış!")
            
        client = genai.Client(api_key=api_key)
        
        prompt = (
            f"Sen bir kamu kurumunun yapay zeka destekli talep ve yardım masası asistanısın. "
            f"Vatandaş veya personel olan kullanıcının adı: {request.user_name}. "
            f"İlgili Departman: {request.department}. "
            f"Gelen Talep / Mesaj: {request.message}. "
            f"Lütfen talebi analiz et, çözüm önerisi sun ve kurumsal bir dille yardımcı ol."
        )
        
        # Güncel ve kararlı Gemini modeli kullanılıyor
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )
        
        ai_reply = response.text

        # PostgreSQL Veritabanına Güvenli Kayıt İşlemi
        yeni_talep = TalepModel(
            UserName=request.user_name,
            Department=request.department,
            Message=request.message,
            AiResponse=ai_reply
        )
        db.add(yeni_talep)
        db.commit()
        db.refresh(yeni_talep)
        
        return {
            "success": True,
            "database_status": "PostgreSQL'e Başarıyla Kaydedildi",
            "talep_id": yeni_talep.Id,
            "user": request.user_name,
            "department": request.department,
            "ai_response": ai_reply
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
