# -*- coding: utf-8 -*-
"""
Created on Sat Oct  3 15:48:55 2026

@author: Bilgisayar
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from google import genai

app = FastAPI(
    title="Kurumsal Talep Yönetim Sistemi API",
    version="1.0.0",
    description="Yapay Zeka Destekli Kamu Kurumu Talep ve Yardım Masası Otomasyonu"
)

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

# Fonksiyon asenkron hale getirildi
@app.post("/api/chatbot/send")
async def send_message(request: ChatRequest):
    try:
        # Render Environment Variables üzerinden anahtarı alıyoruz
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
        
        # GÜNCELLEME: Kullanımdan kaldırılan gemini-2.0-flash yerine güncel gemini-3.5-flash entegre edildi
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )
        
        return {
            "success": True,
            "user": request.user_name,
            "department": request.department,
            "ai_response": response.text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
