# -*- coding: utf-8 -*-
"""
Created on Sat Oct  3 15:48:55 2026

@author: Bilgisayar
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from google import genai
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

app = FastAPI(
    title="Kurumsal Talep Yönetim Sistemi API",
    version="1.0.0",
    description="Yapay Zeka Destekli Kamu Kurumu Talep ve Yardım Masası Otomasyonu"
)

# Render üzerindeki PostgreSQL bulut veritabanı bağlantı adresi
DATABASE_URL = os.environ.get("DATABASE_URL")

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
    CreatedAt = Column(DateTime, default=datetime.utcnow)

# Tablo yoksa otomatik oluşturur
Base.metadata.create_all(bind=engine)

# İstek gövdesi için Pydantic modeli
class ChatRequest(BaseModel):
    user_name: str
    department: str
    message: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "Talep Yönetim ve AI Destek Masası",
        "docs_url": "/docs"
    }

# Fonksiyon asenkron yapısıyla korundu
@app.post("/api/chatbot/send")
async def send_message(request: ChatRequest):
    try:
        # Render Environment Variables veya yerel ortam üzerinden anahtarı alıyoruz
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY tanımlanmamış!")
            
        client = genai.Client(api_key=api_key)
        
        # Kurumsal talep asistanı için yapay zeka yönlendirmesi
        prompt = (
            f"Sen bir kamu kurumunun yapay zeka destekli talep ve yardım masası asistanısın. "
            f"Vatandaş veya personel olan kullanıcının adı: {request.user_name}. "
            f"İlgili Departman: {request.department}. "
            f"Gelen Talep / Mesaj: {request.message}. "
            f"Lütfen talebi analiz et, çözüm önerisi sun ve kurumsal bir dille yardımcı ol."
        )
        
        # Güncel model entegrasyonu
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )
        
        ai_reply = response.text

        # PostgreSQL Veritabanına Kayıt İşlemi
        db = SessionLocal()
        yeni_talep = TalepModel(
            UserName=request.user_name,
            Department=request.department,
            Message=request.message,
            AiResponse=ai_reply
        )
        db.add(yeni_talep)
        db.commit()
        db.refresh(yeni_talep)
        db.close()
        
        return {
            "success": True,
            "database_status": "PostgreSQL'e Başarıyla Kaydedildi",
            "user": request.user_name,
            "department": request.department,
            "ai_response": ai_reply
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))