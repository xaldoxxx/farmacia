# app2colab.py (versión corregida y completa)

import os
import uuid
from datetime import datetime, timedelta
from flask import Flask, session, redirect, url_for, request, render_template, g, flash
from config import Config
from database import get_db, init_db

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
            flash("Debes iniciar sesión para acceder al panel", 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# --- Rutas Cliente & Carrito ---

@app.route('/')
def home():
    db = get_db()
    cat_id = request.args.get('cat')
    q = request.args.get('q', '').strip()
    today = datetime.now().strftime('%Y-%m-%d')

    # 1. Buscamos productos según filtros
    sql = 'SELECT p.*, c.nombre as cat_nombre FROM productos p JOIN categorias c ON p.categoria_id = c.id WHERE p.publicar_hasta >= ?'
    params = [today]
    if cat_id:
        sql += ' AND p.categoria_id = ?'; params.append(cat_id)
    if q:
        sql += ' AND p.nombre LIKE ?'; params.append(f'%{q}%')
    
    productos = db.execute(sql, params).fetchall()
    categorias = db.execute('SELECT id, nombre FROM categorias ORDER BY nombre').fetchall()

    # 2. Lógica del Carrito (con control estricto de stock)
    items_carrito = []
    total_compra = 0
    mensaje_whatsapp = "🌟 *PEDIDO FARMACIA 2026* 🌟%0A%0A"
    
    if 'cart' in session:
        for p_id, cant in list(session['cart'].items()):
            p = db.execute('SELECT * FROM productos WHERE id = ?', (p_id,)).fetchone()
            if p:
                # Ajuste de stock: nunca superar el disponible
                cant_max = min(cant, p['cantidad'])
                if cant > cant_max:
                    flash(f"{p['nombre']}: Cantidad ajustada a stock disponible ({cant_max})", 'warning')
                    session['cart'][p_id] = cant_max
                    session.modified = True
                    cant = cant_max  # actualizamos para el cálculo

                subtotal = cant * p['precio']
                total_compra += subtotal
                items_carrito.append({
                    'id': p_id, 
                    'nombre': p['nombre'], 
                    'cantidad': cant, 
                    'precio': p['precio'], 
                    'subtotal': subtotal
                })
                mensaje_whatsapp += f"✅ *{cant}x* {p['nombre']} - ${subtotal:.2f}%0A"
    
    mensaje_whatsapp += f"%0A💰 *TOTAL: ${total_compra:.2f}*"

    return render_template('index.html', 
                           productos=productos, 
                           categorias=categorias, 
                           items_carrito=items_carrito,
                           total_compra=total_compra,
                           whatsapp_link=f"https://wa.me/{Config.NUMERO_WHATSAPP}?text={mensaje_whatsapp}",
                           query=q,
                           show_cart=request.args.get('show_cart'))

@app.route('/carrito/agregar/<id>')
def agregar_al_carrito(id):
    db = get_db()
    producto = db.execute('SELECT * FROM productos WHERE id = ?', (id,)).fetchone()
    if not producto:
        flash("Producto no encontrado", 'danger')
        return redirect(url_for('home'))

    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    cantidad_actual = cart.get(id, 0)
    
    # Validación estricta de stock
    if cantidad_actual + 1 > producto['cantidad']:
        flash(f"No hay suficiente stock para {producto['nombre']}", 'warning')
    else:
        cart[id] = cantidad_actual + 1
        session.modified = True
        flash(f"{producto['nombre']} agregado al carrito", 'success')

    return redirect(url_for('home', show_cart=1))

@app.route('/carrito/restar/<id>')
def restar_del_carrito(id):
    if 'cart' in session and id in session['cart']:
        session['cart'][id] -= 1
        if session['cart'][id] <= 0:
            session['cart'].pop(id)
        session.modified = True
        flash("Producto reducido del carrito", 'info')
    return redirect(url_for('home', show_cart=1))

@app.route('/carrito/limpiar')
def limpiar_carrito():
    session.pop('cart', None)
    flash("Carrito vaciado", 'info')
    return redirect(url_for('home'))

# --- Rutas Admin ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user') == Config.ADMIN_USER and request.form.get('pass') == Config.ADMIN_PASS:
            session['admin_logged_in'] = True
            flash("Sesión iniciada correctamente", 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Usuario o contraseña incorrectos", 'danger')
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

    try:
        db.execute('''INSERT INTO productos (id, nombre, imagen, detalle, precio, cantidad, publicar_hasta, categoria_id)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                   (str(uuid.uuid4()), request.form['nombre'], filename, "", 
                    float(request.form['precio']), int(request.form['cantidad']), 
                    request.form['publicar_hasta'], int(request.form['categoria_id'])))
        db.commit()
        flash("Producto agregado correctamente", 'success')
    except Exception as e:
        flash(f"Error al agregar producto: {str(e)}", 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/editar_completo', methods=['POST'])
@login_required
def editar_completo():
    db = get_db()
    try:
        db.execute('''UPDATE productos SET nombre=?, precio=?, cantidad=?, publicar_hasta=?, detalle=? WHERE id=?''',
                   (request.form['nombre'], float(request.form['precio']), int(request.form['cantidad']),
                    request.form['publicar_hasta'], request.form['detalle'], request.form['id']))
        db.commit()
        flash("Producto actualizado correctamente", 'success')
    except Exception as e:
        flash(f"Error al editar producto: {str(e)}", 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/eliminar/<id>')
@login_required
def eliminar(id):
    db = get_db()
    try:
        db.execute('DELETE FROM productos WHERE id=?', (id,))
        db.commit()
        flash("Producto eliminado correctamente", 'success')
    except Exception as e:
        flash(f"Error al eliminar producto: {str(e)}", 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash("Sesión cerrada correctamente", 'info')
    return redirect(url_for('login'))

# --- Bloque de ejecución para Google Colab ---
if __name__ == '__main__':
    with app.app_context():
        init_db()
        
    from pyngrok import ngrok
    # Tu token está configurado correctamente
    ngrok.set_auth_token("39HgBBF8I4YkpN8PxvDKixjfZ8S_toMWhiEALqwwcNC7cU1S")
    
    public_url = ngrok.connect(5000).public_url
    print(f"\n * FARMACIA ONLINE LISTA")
    print(f" * URL PÚBLICA: {public_url}")
    print(f" * PANEL ADMIN: {public_url}/login\n")
    
    app.run(port=5000)
