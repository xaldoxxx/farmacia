# farmacia
back farmacia CRUD catalogo pedidos por whatsapp
<header>
        <h1>💊 Farmacia 2026 - Sistema de Catálogo y Pedidos</h1>
        <p>Un sistema web ligero y moderno diseñado para farmacias, que permite gestionar un catálogo de productos y recibir pedidos directamente por <strong>WhatsApp</strong>. Incluye un panel de administración con alertas inteligentes de stock y vencimiento.</p>
    </header>

    <hr>

    <section>
        <h2>🚀 Características Principales</h2>
        <ul>
            <li><strong>Catálogo Interactivo:</strong> Búsqueda por nombre y filtrado por categorías.</li>
            <li><strong>Carrito de WhatsApp:</strong> Los clientes añaden productos y envían el pedido detallado con un solo clic.</li>
            <li><strong>Panel Admin (Dashboard):</strong>
                <ul>
                    <li><em>Alertas de Stock:</em> Aviso visual si quedan 5 unidades o menos.</li>
                    <li><em>Control de Vencimiento:</em> Alerta de productos próximos a expirar (30 días).</li>
                    <li><em>Gestión de Imágenes:</em> Carga dinámica de fotos para cada producto.</li>
                    <li><em>Edición Rápida:</em> Renovación de fechas y carga de stock en un paso.</li>
                </ul>
            </li>
        </ul>
    </section>

    <section>
        <h2>🛠️ Tecnologías Usadas</h2>
        <ul>
            <li><strong>Backend:</strong> Python 3 + Flask</li>
            <li><strong>Base de Datos:</strong> SQLite3 (incluida, sin configuración externa)</li>
            <li><strong>Frontend:</strong> Bootstrap 5.3 + SweetAlert2</li>
        </ul>
    </section>

    <section>
        <h2>📋 Requisitos Previos</h2>
        <p>Asegúrate de tener instalado Python en tu sistema. Luego, instala las dependencias necesarias:</p>
        <pre><code>pip install flask werkzeug</code></pre>
    </section>

    <section>
        <h2>⚙️ Configuración Rápida</h2>
        <p>Abre el archivo principal y localiza la sección de configuración para personalizar tu entorno:</p>
        <ul>
            <li><strong>Número de WhatsApp:</strong> Cambia <code>NUMERO_WHATSAPP</code> por el tuyo (formato internacional, ej: 54911...).</li>
            <li><strong>Credenciales:</strong> Modifica <code>ADMIN_USER</code> y <code>ADMIN_PASS</code> para el acceso al panel.</li>
        </ul>
    </section>

    <section>
        <h2>🏃 Instrucciones de Ejecución</h2>
        <ol>
            <li>Clona o descarga este repositorio.</li>
            <li>Ejecuta la aplicación:
                <br><code>python app.py</code>
            </li>
            <li>Accede desde tu navegador:
                <ul>
                    <li><strong>Cliente:</strong> http://localhost:8000</li>
                    <li><strong>Admin:</strong> http://localhost:8000/admin</li>
                </ul>
            </li>
        </ol>
    </section>

    <section>
        <h2>📁 Estructura del Proyecto</h2>
        <ul>
            <li><code>/data</code>: Almacena la base de datos farmacia.db.</li>
            <li><code>/static/uploads</code>: Carpeta donde se guardan las imágenes de productos.</li>
            <li><code>app.py</code>: Lógica del servidor, rutas y plantillas HTML integradas.</li>
        </ul>
    </section>
