import sqlite3
from flask import g
from config import Config

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(Config.DB_FILE)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    db = sqlite3.connect(Config.DB_FILE)
    cursor = db.cursor()
    # Tabla Categorías
    cursor.execute('''CREATE TABLE IF NOT EXISTS categorias 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE)''')
    # Tabla Productos
    cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
                        id TEXT PRIMARY KEY, nombre TEXT NOT NULL, imagen TEXT,
                        detalle TEXT, precio REAL NOT NULL, cantidad INTEGER NOT NULL DEFAULT 0,
                        publicar_hasta TEXT NOT NULL, categoria_id INTEGER NOT NULL,
                        FOREIGN KEY (categoria_id) REFERENCES categorias(id))''')
    
    # Datos semilla
    cursor.execute("SELECT COUNT(*) FROM categorias")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO categorias (nombre) VALUES (?)",
                          [('Medicamentos',), ('Estética',), ('Bebés',), ('Otros',)])
    db.commit()
    db.close()
    
