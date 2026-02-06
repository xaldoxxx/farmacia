import sqlite3
import uuid
import os
from functools import wraps
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "demo_farmacia_2026_premium_super_secreto_2025"

# ── Configuración ───────────────────────────────────────────────────────────────
ADMIN_USER = "admin"
ADMIN_PASS = "farmacia2026"
NUMERO_WHATSAPP = "5491122334455"  # ← cámbialo por tu número real sin espacios ni guiones

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
DB_DIR = os.path.join(BASE_DIR, 'data')
DB_FILE = os.path.join(DB_DIR, 'farmacia.db')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Inicialización de base de datos ────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
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

    cursor.execute("SELECT COUNT(*) FROM categorias")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO categorias (nombre) VALUES (?)",
            [('Medicamentos',), ('Estética',), ('Bebés',), ('Otros',)]
        )

    conn.commit()
    conn.close()

init_db()

# ── Plantilla INDEX (principal) ────────────────────────────────────────────────
INDEX_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmacia 2026 - Tu Bienestar</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        :root {
            --primary: #00b894;
            --primary-dark: #009578;
            --secondary: #00cec9;
            --light: #f8f9fa;
            --dark: #2d3436;
            --gray: #636e72;
        }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #f0f4f8 0%, #e0e7ff 100%);
            color: var(--dark);
            min-height: 100vh;
        }
        .navbar {
            background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        .navbar-brand { font-weight: 700; letter-spacing: -0.5px; }
        .hero {
            background: rgba(255,255,255,0.85);
            backdrop-filter: blur(12px);
            border-radius: 1.8rem;
            border: 1px solid rgba(255,255,255,0.4);
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            padding: 3rem 1.5rem;
            margin: 2rem 0;
            text-align: center;
        }
        .hero h1 {
            font-weight: 700;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .cat-link {
            padding: 0.65rem 1.5rem;
            border-radius: 50px;
            background: white;
            border: 1px solid #e0e0e0;
            color: var(--gray);
            transition: all 0.3s ease;
            font-weight: 500;
            white-space: nowrap;
        }
        .cat-link:hover, .cat-link.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,184,148,0.25);
        }
        .product-card {
            border: none;
            border-radius: 1.5rem;
            overflow: hidden;
            background: white;
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
            box-shadow: 0 6px 25px rgba(0,0,0,0.08);
            position: relative;
        }
        .product-card:hover {
            transform: translateY(-12px);
            box-shadow: 0 20px 50px rgba(0,184,148,0.22);
        }
        .img-container {
            height: 220px;
            overflow: hidden;
            background: #f8f9fa;
            position: relative;
        }
        .img-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.6s ease;
        }
        .product-card:hover img { transform: scale(1.12); }
        .price {
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--primary);
            background: rgba(0,184,148,0.08);
            padding: 0.35rem 0.8rem;
            border-radius: 12px;
        }
        .stock-low {
            position: absolute;
            top: 12px;
            right: 12px;
            background: #e74c3c;
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.35rem 0.75rem;
            border-radius: 50px;
            box-shadow: 0 4px 12px rgba(231,76,60,0.4);
        }
        #btn-cart {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 1000;
            background: var(--dark);
            color: white;
            border: none;
            border-radius: 999px;
            padding: 16px 32px;
            font-weight: 600;
            box-shadow: 0 12px 30px rgba(0,0,0,0.25);
            transition: all 0.3s ease;
        }
        #btn-cart:hover {
            transform: scale(1.08);
            background: #1a1f24;
        }
        .cart-badge {
            background: var(--primary);
            color: white;
            border-radius: 50%;
            padding: 4px 10px;
            font-size: 0.9rem;
            margin-left: 8px;
        }
    </style>
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark shadow-sm py-3">
    <div class="container">
        <a class="navbar-brand fs-3" href="/">💊 Farmacia 2026</a>
        <form class="d-flex ms-auto w-50" method="GET">
            <input class="form-control rounded-pill px-4 shadow-sm" type="search" name="q" placeholder="¿Qué necesitas hoy?" value="{{ query or '' }}">
        </form>
    </div>
</nav>

<div class="container">
    <div class="hero">
        <h1 class="mb-3">Siempre cerca, siempre listos.</h1>
        <p class="lead text-muted mb-0">Medicamentos esenciales y estética premium con atención personalizada — pedidos rápidos por WhatsApp</p>
    </div>

    <div class="d-flex flex-wrap gap-3 justify-content-center mb-5 pb-3 overflow-auto">
        <a href="/" class="cat-link shadow-sm {% if not request.args.get('cat') %}active{% endif %}">Todos</a>
        {% for cat in categorias %}
            <a href="/?cat={{ cat[0] }}" class="cat-link shadow-sm {% if request.args.get('cat') == cat[0]|string %}active{% endif %}">{{ cat[1] }}</a>
        {% endfor %}
    </div>

    {% if productos %}
    <div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-4 mb-5">
        {% for p in productos %}
        <div class="col">
            <div class="card product-card h-100 position-relative">
                {% if p[5] <= 5 and p[5] > 0 %}
                    <span class="stock-low">¡Quedan pocas!</span>
                {% endif %}
                <div class="img-container">
                    {% if p[2] %}
                        <img src="/static/uploads/{{ p[2] }}" alt="{{ p[1] }}">
                    {% else %}
                        <div class="d-flex align-items-center justify-content-center h-100 text-muted bg-light">Sin foto</div>
                    {% endif %}
                </div>
                <div class="card-body text-center pt-4 pb-4">
                    <h5 class="card-title fw-600 mb-3">{{ p[1] }}</h5>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="price">${{ "%.2f"|format(p[4]) }}</span>
                        <button onclick="addToCart('{{ p[1]|e }}', {{ p[4] }})" class="btn btn-primary rounded-pill px-4 py-2 fw-500">
                            + Añadir
                        </button>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="text-center py-5 my-5 text-muted">
        <h3 class="mb-3">No hay productos en este momento</h3>
        <p class="lead">Prueba con otra categoría o busca algo específico</p>
    </div>
    {% endif %}
</div>

<button id="btn-cart" onclick="sendWhatsApp()">
    🛒 Ver Pedido <span class="cart-badge" id="cart-count">0</span>
</button>

<script>
let cart = [];
function addToCart(name, price) {
    cart.push({name, price});
    document.getElementById('cart-count').innerText = cart.length;
    Swal.fire({
        toast: true,
        position: 'top-end',
        icon: 'success',
        title: name + ' añadido al carrito',
        showConfirmButton: false,
        timer: 1600,
        background: '#fff',
        color: '#2d3436'
    });
}
function sendWhatsApp() {
    if (cart.length === 0) {
        return Swal.fire('Carrito vacío', 'Agrega productos para continuar', 'info');
    }
    let msg = "🌟 *PEDIDO FARMACIA 2026* 🌟\\n\\n";
    let total = 0;
    cart.forEach(i => {
        msg += `✅ ${i.name} — $${i.price}\\n`;
        total += i.price;
    });
    msg += `\\n💰 *TOTAL: $${total.toFixed(2)}*\\n\\nGracias por confirmar disponibilidad y envío 🙏`;
    window.open(`https://wa.me/{{ whatsapp }}?text=${encodeURIComponent(msg)}`, '_blank');
}
</script>
</body>
</html>
"""
# ── Plantillas ADMIN y LOGIN (sin cambios importantes) ──────────────────────────

ADMIN_HTML = """
<!DOCTYPE html><html lang="es"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel de Supervivencia - Farmacia 2026</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <style>
        body { background-color: #f0f2f5; font-size: 0.85rem; }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        .alert-card { border-left: 6px solid; margin-bottom: 8px; transition: 0.2s; }
        .alert-card:hover { transform: translateX(5px); }
        .critical { border-left-color: #dc3545; background: #fff5f5; }
        .warning { border-left-color: #ffc107; background: #fffbeb; }
        .info-miss { border-left-color: #0dcaf0; background: #f0faff; }
        .badge-count { font-size: 1.4rem; font-weight: bold; }
        .sticky-form { position: sticky; top: 15px; }
    </style>
</head><body>

<nav class="navbar navbar-dark bg-dark mb-4"><div class="container">
    <span class="navbar-brand">💊 DASHBOARD FARMACIA</span>
    <a href="/logout" class="btn btn-sm btn-outline-danger">Cerrar Sesión</a>
</div></nav>

<div class="container-fluid px-3">
    <div class="row g-2 mb-4 text-center">
        <div class="col-6 col-md-3"><div class="card p-2 border-bottom border-danger border-4"><div class="text-danger small fw-bold">STOCK</div><div class="badge-count">{{ alertas.stock|length }}</div></div></div>
        <div class="col-6 col-md-3"><div class="card p-2 border-bottom border-warning border-4"><div class="text-warning small fw-bold">VENCE</div><div class="badge-count">{{ alertas.vence|length }}</div></div></div>
        <div class="col-6 col-md-3"><div class="card p-2 border-bottom border-info border-4"><div class="text-info small fw-bold">FOTOS</div><div class="badge-count">{{ alertas.sin_foto|length }}</div></div></div>
        <div class="col-6 col-md-3"><div class="card p-2 border-bottom border-success border-4"><div class="text-success small fw-bold">TOTAL</div><div class="badge-count">{{ productos|length }}</div></div></div>
    </div>

    <div class="row">
        <div class="col-lg-8">
            <h6 class="fw-bold mb-3"><i class="bi bi-lightning-fill text-warning"></i> ACCIONES RÁPIDAS</h6>

            {% for p in alertas.stock %}
            <div class="card alert-card critical p-3">
                <div class="d-flex justify-content-between align-items-center">
                    <div><b class="d-block">{{ p[1] }}</b><span class="badge bg-danger">Quedan: {{p[5]}}</span></div>
                    <form action="/admin/update_stock" method="POST" class="d-flex gap-1">
                        <input type="hidden" name="id" value="{{ p[0] }}">
                        <input type="number" name="qty" class="form-control form-control-sm w-50" placeholder="+" required>
                        <button class="btn btn-sm btn-danger">Cargar</button>
                    </form>
                </div>
            </div>
            {% endfor %}

            {% for p in alertas.vence %}
            <div class="card alert-card warning p-3">
                <div class="d-flex justify-content-between align-items-center">
                    <div><b>{{ p[1] }}</b><br><small class="text-muted">Expira: {{ p[6] }}</small></div>
                    <form action="/admin/renew" method="POST">
                        <input type="hidden" name="id" value="{{ p[0] }}">
                        <button class="btn btn-sm btn-warning text-dark fw-bold">+30 Días</button>
                    </form>
                </div>
            </div>
            {% endfor %}

            <div class="card mt-4 p-3 bg-white">
                <h6 class="fw-bold mb-3">INVENTARIO COMPLETO (Click para editar detalle/precio)</h6>
                <div class="table-responsive">
                    <table class="table table-hover align-middle">
                        <thead class="table-light"><tr><th>Foto</th><th>Producto</th><th>Precio</th><th>Stock</th><th>Acción</th></tr></thead>
                        <tbody>
                            {% for p in productos %}
                            <tr>
                                <td><img src="/static/uploads/{{p[2]}}" width="35" class="rounded border shadow-sm"></td>
                                <td>
                                    <a href="#" class="fw-bold text-decoration-none" data-bs-toggle="modal" data-bs-target="#editModal{{p[0]}}">
                                        {{p[1]}} <i class="bi bi-pencil-square ms-1 small"></i>
                                    </a>
                                </td>
                                <td>${{p[4]}}</td>
                                <td><span class="badge {% if p[5] <= 5 %}bg-danger{% else %}bg-secondary{% endif %}">{{p[5]}}</span></td>
                                <td><a href="/admin/eliminar/{{p[0]}}" class="btn btn-sm btn-outline-danger border-0"><i class="bi bi-trash"></i></a></td>
                            </tr>

                            <div class="modal fade" id="editModal{{p[0]}}" tabindex="-1">
                                <div class="modal-dialog">
                                    <div class="modal-content">
                                        <form action="/admin/editar_completo" method="POST">
                                            <div class="modal-header"><h6 class="modal-title">Editar: {{p[1]}}</h6><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
                                            <div class="modal-body">
                                                <input type="hidden" name="id" value="{{p[0]}}">
                                                <div class="mb-2"><label class="small fw-bold">Nombre</label><input type="text" name="nombre" class="form-control" value="{{p[1]}}" required></div>
                                                <div class="row mb-2"><div class="col"><label class="small fw-bold">Precio</label><input type="number" step="0.01" name="precio" class="form-control" value="{{p[4]}}" required></div>
                                                <div class="col"><label class="small fw-bold">Stock</label><input type="number" name="cantidad" class="form-control" value="{{p[5]}}" required></div></div>
                                                <div class="mb-2"><label class="small fw-bold">Vencimiento Pub.</label><input type="date" name="publicar_hasta" class="form-control" value="{{p[6]}}" required></div>
                                                <div class="mb-2"><label class="small fw-bold">Detalles / Descripción</label><textarea name="detalle" class="form-control" rows="3">{{p[3]}}</textarea></div>
                                            </div>
                                            <div class="modal-footer"><button type="submit" class="btn btn-primary w-100">Guardar Cambios</button></div>
                                        </form>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="col-lg-4">
            <div class="card p-4 sticky-form shadow-sm">
                <h6 class="fw-bold mb-3 text-primary"><i class="bi bi-plus-circle"></i> NUEVO PRODUCTO</h6>
                <form action="/admin/agregar" method="POST" enctype="multipart/form-data">
                    <input type="text" name="nombre" class="form-control form-control-sm mb-2" placeholder="Nombre..." required>
                    <div class="row g-2 mb-2">
                        <div class="col-6"><input type="number" name="precio" step="0.01" class="form-control form-control-sm" placeholder="Precio $" required></div>
                        <div class="col-6"><input type="number" name="cantidad" class="form-control form-control-sm" placeholder="Stock" required></div>
                    </div>
                    <input type="date" name="publicar_hasta" class="form-control form-control-sm mb-2" required>
                    <select name="categoria_id" class="form-select form-select-sm mb-2">
                        {% for c in categorias %}<option value="{{c[0]}}">{{c[1]}}</option>{% endfor %}
                    </select>
                    <input type="file" name="imagen_file" class="form-control form-control-sm mb-3">
                    <button class="btn btn-primary w-100 fw-bold shadow-sm">SUBIR PRODUCTO</button>
                </form>
            </div>
        </div>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body></html>
"""



LOGIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <title>Login Admin</title>
</head>
<body class="bg-dark d-flex align-items-center min-vh-100">
<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-4">
            <div class="card shadow-lg border-0">
                <div class="card-body p-4 text-center">
                    <h4 class="mb-4">Panel Administrador</h4>
                    <form method="POST">
                        <input type="text" name="user" class="form-control mb-3" placeholder="admin" required autofocus>
                        <input type="password" name="pass" class="form-control mb-4" placeholder="farmacia2026" required>
                        <button class="btn btn-primary w-100">Ingresar</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>"""

# ── Decorador login ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Rutas ──────────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    init_db()  # idempotente, no hace daño llamarlo

    cat_id = request.args.get('cat')
    q = request.args.get('q', '').strip()
    today = datetime.now().strftime('%Y-%m-%d')

    conn = sqlite3.connect(DB_FILE)
    sql = '''
        SELECT p.*, c.nombre
        FROM productos p
        JOIN categorias c ON p.categoria_id = c.id
        WHERE p.publicar_hasta >= ?
    '''
    params = [today]

    if cat_id:
        sql += ' AND p.categoria_id = ?'
        params.append(cat_id)
    if q:
        sql += ' AND p.nombre LIKE ?'
        params.append(f'%{q}%')

    productos = conn.execute(sql, params).fetchall()
    categorias = conn.execute('SELECT id, nombre FROM categorias ORDER BY nombre').fetchall()
    conn.close()

    return render_template_string(INDEX_HTML,
                                 productos=productos,
                                 categorias=categorias,
                                 whatsapp=NUMERO_WHATSAPP,
                                 query=q)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user') == ADMIN_USER and request.form.get('pass') == ADMIN_PASS:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
    return render_template_string(LOGIN_HTML)


@app.route('/admin')
@login_required
def admin_dashboard():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Productos completos
    productos = cursor.execute('''
        SELECT p.*, c.nombre
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        ORDER BY p.nombre
    ''').fetchall()

    categorias = cursor.execute('SELECT id, nombre FROM categorias ORDER BY nombre').fetchall()

    # Alertas
    today = datetime.now().strftime('%Y-%m-%d')
    in_30_days = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    # Stock bajo (≤ 5)
    stock_bajo = cursor.execute('''
        SELECT * FROM productos
        WHERE cantidad <= 5 AND cantidad > 0
        ORDER BY cantidad ASC
    ''').fetchall()

    # Por vencer (30 días o menos)
    por_vencer = cursor.execute('''
        SELECT * FROM productos
        WHERE publicar_hasta <= ? AND publicar_hasta >= ?
        ORDER BY publicar_hasta ASC
    ''', (in_30_days, today)).fetchall()

    # Sin foto
    sin_foto = cursor.execute('''
        SELECT * FROM productos
        WHERE imagen IS NULL OR imagen = ''
    ''').fetchall()

    conn.close()

    alertas = {
        'stock': stock_bajo,
        'vence': por_vencer,
        'sin_foto': sin_foto
    }

    return render_template_string(ADMIN_HTML,
                                 productos=productos,
                                 categorias=categorias,
                                 alertas=alertas)





@app.route('/admin/agregar', methods=['POST'])
@login_required
def agregar_producto():
    nombre = request.form.get('nombre', '').strip()
    if not nombre:
        return redirect(url_for('admin_dashboard'))

    try:
        precio    = float(request.form.get('precio', 0))
        cantidad  = int(request.form['cantidad'])
        publicar_hasta = request.form['publicar_hasta']
        cat_id    = int(request.form['categoria_id'])
    except (ValueError, KeyError):
        # Podrías agregar flash message aquí si quieres
        return redirect(url_for('admin_dashboard'))

    imagen = None
    file = request.files.get('imagen_file')
    if file and file.filename and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex[:12]}.{ext}"
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        imagen = filename

    conn = sqlite3.connect(DB_FILE)
    conn.execute('''
        INSERT INTO productos (id, nombre, imagen, detalle, precio, cantidad, publicar_hasta, categoria_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (str(uuid.uuid4()), nombre, imagen, "", precio, cantidad, publicar_hasta, cat_id))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/eliminar/<prod_id>')
@login_required
def eliminar_producto(prod_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute('DELETE FROM productos WHERE id = ?', (prod_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))




from datetime import timedelta   # ← agrégalo arriba si no está

@app.route('/admin/update_stock', methods=['POST'])
@login_required
def update_stock():
    prod_id = request.form.get('id')
    try:
        qty_add = int(request.form.get('qty', 0))
        if qty_add <= 0:
            return redirect(url_for('admin_dashboard'))

        conn = sqlite3.connect(DB_FILE)
        conn.execute('''
            UPDATE productos
            SET cantidad = cantidad + ?
            WHERE id = ?
        ''', (qty_add, prod_id))
        conn.commit()
        conn.close()
    except:
        pass

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/renew', methods=['POST'])
@login_required
def renew():
    prod_id = request.form.get('id')
    try:
        conn = sqlite3.connect(DB_FILE)
        # Sumar 30 días a la fecha actual (o a la existente, según prefieras)
        conn.execute('''
            UPDATE productos
            SET publicar_hasta = date(publicar_hasta, '+30 days')
            WHERE id = ?
        ''', (prod_id,))
        conn.commit()
        conn.close()
    except:
        pass

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/editar_completo', methods=['POST'])
@login_required
def editar_completo():
    prod_id = request.form.get('id')
    if not prod_id:
        return redirect(url_for('admin_dashboard'))

    try:
        nombre = request.form['nombre'].strip()
        precio = float(request.form['precio'])
        cantidad = int(request.form['cantidad'])
        publicar_hasta = request.form['publicar_hasta']
        detalle = request.form.get('detalle', '')

        conn = sqlite3.connect(DB_FILE)
        conn.execute('''
            UPDATE productos
            SET nombre = ?, precio = ?, cantidad = ?, publicar_hasta = ?, detalle = ?
            WHERE id = ?
        ''', (nombre, precio, cantidad, publicar_hasta, detalle, prod_id))
        conn.commit()
        conn.close()
    except:
        pass  # en producción pondrías flash de error

    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
