import os

class Config:
    # Usa variables de entorno si existen, si no, usa el default (pero oculto)
    SECRET_KEY = os.environ.get("SECRET_KEY", "una-clave-muy-larga-y-compleja-2026")
    ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
    ADMIN_PASS = os.environ.get("ADMIN_PASS", "farmacia2026")
    NUMERO_WHATSAPP = os.environ.get("WHATSAPP", "5491122334455")
    
    # El token de Ngrok debería estar fuera del código
    NGROK_TOKEN = os.environ.get("NGROK_TOKEN", "TU_TOKEN_AQUÍ")

    
    # Compatible con Colab y script normal
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        BASE_DIR = os.getcwd()  # Colab / notebook
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    DB_DIR = os.path.join(BASE_DIR, 'data')
    DB_FILE = os.path.join(DB_DIR, 'farmacia.db')
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
