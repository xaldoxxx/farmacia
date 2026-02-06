import sqlite3
from datetime import datetime, timedelta
from config import Config

def get_db():
    db = sqlite3.connect(Config.DB_FILE)
    db.row_factory = sqlite3.Row  # para acceder como diccionario
    return db

def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            imagen TEXT,
            detalle TEXT,
            precio REAL NOT NULL,
            cantidad INTEGER NOT NULL DEFAULT 0,
            publicar_hasta TEXT NOT NULL,
            categoria_id INTEGER NOT NULL,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    ''')
    if db.execute("SELECT COUNT(*) FROM categorias").fetchone()[0] == 0:
        db.executemany("INSERT INTO categorias (nombre) VALUES (?)",
                       [('Medicamentos',), ('Estética',), ('Bebés',), ('Otros',)])
    db.commit()
    db.close()
