import os

class Config:
    SECRET_KEY = "demo_farmacia_2026_premium_super_secreto_2025"
    ADMIN_USER = "admin"
    ADMIN_PASS = "farmacia2026"
    NUMERO_WHATSAPP = "5491122334455"
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    DB_DIR = os.path.join(BASE_DIR, 'data')
    DB_FILE = os.path.join(DB_DIR, 'farmacia.db')
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
