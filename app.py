from flask import session, render_template, redirect, url_for, request
import os
from flask import Flask, session, redirect, url_for, request, render_template, g
from config import Config
from database import get_db, init_db
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.config.from_object(Config)

# Asegurar carpetas
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.DB_DIR, exist_ok=True)

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Decorador ---
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# --- Rutas Cliente ---
@app.route('/')
def home():
    db = get_db()
    cat_id = request.args.get('cat')
    q = request.args.get('q', '').strip()
    today = datetime.now().strftime('%Y-%m-%d')

    sql = 'SELECT p.*, c.nombre as cat_nombre FROM productos p JOIN categorias c ON p.categoria_id = c.id WHERE p.publicar_hasta >= ?'
    params = [today]

    if cat_id:
        sql += ' AND p.categoria_id = ?'; params.append(cat_id)
    if q:
        sql += ' AND p.nombre LIKE ?'; params.append(f'%{q}%')

    productos = db.execute(sql, params).fetchall()
    categorias = db.execute('SELECT id, nombre FROM categorias ORDER BY nombre').fetchall()
    
    return render_template('index.html', productos=productos, categorias=categorias, 
                           whatsapp=Config.NUMERO_WHATSAPP, query=q)

# --- Rutas del Carrito (Lógica en Python) ---

@app.route('/carrito/agregar/<id>')
def agregar_al_carrito(id):
    db = get_db()
    producto = db.execute('SELECT * FROM productos WHERE id = ?', (id,)).fetchone()
    
    if not producto:
        return redirect(url_for('home'))

    # Inicializar carrito en sesión si no existe
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    
    # Lógica de Stock (Falla 2)
    cantidad_actual = cart.get(id, 0)
    if cantidad_actual < producto['cantidad']:
        cart[id] = cantidad_actual + 1
        session.modified = True
    # Si no hay stock, simplemente no suma y redirige
    
    return redirect(url_for('home'))

@app.route('/carrito/restar/<id>')
def restar_del_carrito(id):
    if 'cart' in session and id in session['cart']:
        session['cart'][id] -= 1
        if session['cart'][id] <= 0:
            session['cart'].pop(id)
        session.modified = True
    return redirect(url_for('home'))

@app.route('/carrito/limpiar')
def limpiar_carrito():
    session.pop('cart', None)
    return redirect(url_for('home'))

# --- Ruta Home Actualizada ---
@app.route('/')
def home():
    db = get_db()
    cat_id = request.args.get('cat')
    q = request.args.get('q', '').strip()
    today = datetime.now().strftime('%Y-%m-%d')

    # Buscamos productos
    sql = 'SELECT p.*, c.nombre as cat_nombre FROM productos p JOIN categorias c ON p.categoria_id = c.id WHERE p.publicar_hasta >= ?'
    params = [today]
    if cat_id:
        sql += ' AND p.categoria_id = ?'; params.append(cat_id)
    if q:
        sql += ' AND p.nombre LIKE ?'; params.append(f'%{q}%')
    
    productos = db.execute(sql, params).fetchall()
    categorias = db.execute('SELECT id, nombre FROM categorias ORDER BY nombre').fetchall()

    # --- Lógica para mostrar el Carrito en el Modal ---
    items_carrito = []
    total_compra = 0
    mensaje_whatsapp = "🌟 *PEDIDO FARMACIA 2026* 🌟%0A%0A"
    
    if 'cart' in session:
        for p_id, cant in session['cart'].items():
            p = db.execute('SELECT * FROM productos WHERE id = ?', (p_id,)).fetchone()
            if p:
                subtotal = cant * p['precio']
                total_compra += subtotal
                items_carrito.append({'id': p_id, 'nombre': p['nombre'], 'cantidad': cant, 'precio': p['precio'], 'subtotal': subtotal})
                mensaje_whatsapp += f"✅ *{cant}x* {p['nombre']} - ${subtotal:.2f}%0A"
    
    mensaje_whatsapp += f"%0A💰 *TOTAL: ${total_compra:.2f}*"

    return render_template('index.html', 
                           productos=productos, 
                           categorias=categorias, 
                           items_carrito=items_carrito,
                           total_compra=total_compra,
                           whatsapp_link=f"https://wa.me/{Config.NUMERO_WHATSAPP}?text={mensaje_whatsapp}",
                           query=q)




# --- Rutas Admin (Lógica completa extraída de tu app.py original) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user') == Config.ADMIN_USER and request.form.get('pass') == Config.ADMIN_PASS:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    db = get_db()
    productos = db.execute('SELECT p.*, c.nombre as cat_nombre FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id ORDER BY p.nombre').fetchall()
    categorias = db.execute('SELECT id, nombre FROM categorias ORDER BY nombre').fetchall()
    
    today = datetime.now()
    in_30_days = (today + timedelta(days=30)).strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')

    alertas = {
        'stock': [p for p in productos if 0 < p['cantidad'] <= 5],
        'vence': [p for p in productos if today_str <= p['publicar_hasta'] <= in_30_days],
        'sin_foto': [p for p in productos if not p['imagen']]
    }
    return render_template('admin.html', productos=productos, categorias=categorias, alertas=alertas)

@app.route('/admin/agregar', methods=['POST'])
@login_required
def agregar_producto():
    db = get_db()
    file = request.files.get('imagen_file')
    filename = ""
    if file and file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex[:12]}.{ext}"
        file.save(os.path.join(Config.UPLOAD_FOLDER, filename))

    db.execute('''INSERT INTO productos (id, nombre, imagen, detalle, precio, cantidad, publicar_hasta, categoria_id)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
               (str(uuid.uuid4()), request.form['nombre'], filename, "", 
                float(request.form['precio']), int(request.form['cantidad']), 
                request.form['publicar_hasta'], int(request.form['categoria_id'])))
    db.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/editar_completo', methods=['POST'])
@login_required
def editar_completo():
    db = get_db()
    db.execute('''UPDATE productos SET nombre=?, precio=?, cantidad=?, publicar_hasta=?, detalle=? WHERE id=?''',
               (request.form['nombre'], float(request.form['precio']), int(request.form['cantidad']),
                request.form['publicar_hasta'], request.form['detalle'], request.form['id']))
    db.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/eliminar/<id>')
@login_required
def eliminar(id):
    db = get_db()
    db.execute('DELETE FROM productos WHERE id=?', (id,))
    db.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8000)
