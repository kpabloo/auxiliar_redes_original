from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import logging
import os
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'tu_clave_secreta_aqui'  # Cambia esto por algo seguro
CORS(app)

# Configura la carpeta de subidas
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        return User(user[0]) if user else None
    except Exception as e:
        logger.error(f"Error al cargar usuario: {e}")
        return None

def init_db():
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT NOT NULL,
            time TEXT,
            social_network TEXT NOT NULL,
            text TEXT NOT NULL,
            image_path TEXT,  -- Nueva columna para la ruta de la imagen
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')
        try:
            c.execute('ALTER TABLE posts ADD COLUMN user_id INTEGER')
            logger.info("Columna user_id añadida a la tabla posts")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute('ALTER TABLE posts ADD COLUMN time TEXT')
            logger.info("Columna time añadida a la tabla posts")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute('ALTER TABLE posts ADD COLUMN image_path TEXT')
            logger.info("Columna image_path añadida a la tabla posts")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        logger.info("Base de datos inicializada/actualizada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
    finally:
        conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
            login_user(User(user[0]))
            logger.info(f"Usuario {username} inició sesión")
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            flash('Usuario registrado, ahora inicia sesión')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('El usuario ya existe')
        conn.close()
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logger.info(f"Usuario {current_user.id} cerró sesión")
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/posts', methods=['GET'])
@login_required
def get_posts():
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT id, date, time, social_network, text, image_path FROM posts WHERE user_id = ?', (current_user.id,))
        posts = [{'id': row[0], 'date': row[1], 'time': row[2], 'social_network': row[3], 'text': row[4], 'image_path': row[5]} for row in c.fetchall()]
        conn.close()
        logger.debug(f"Publicaciones obtenidas para user_id {current_user.id}: {len(posts)}")
        return jsonify(posts)
    except Exception as e:
        logger.error(f"Error en get_posts: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/posts', methods=['POST'])
@login_required
def add_post():
    try:
        date = request.form['date']
        time = request.form.get('time', '')
        social_network = request.form['social_network']
        text = request.form['text']
        image_path = None

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{current_user.id}_{filename}")
                file.save(file_path)
                image_path = f"/{file_path}"

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO posts (user_id, date, time, social_network, text, image_path) VALUES (?, ?, ?, ?, ?, ?)',
                  (current_user.id, date, time, social_network, text, image_path))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Publicación guardada'}), 201
    except Exception as e:
        logger.error(f"Error en add_post: {e}")
        return jsonify({'error': 'Error al guardar publicación'}), 500

@app.route('/posts/<int:post_id>', methods=['PUT'])
@login_required
def update_post(post_id):
    try:
        date = request.form['date']
        time = request.form.get('time', '')
        social_network = request.form['social_network']
        text = request.form['text']
        image_path = request.form.get('existing_image_path', '')

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{current_user.id}_{filename}")
                file.save(file_path)
                image_path = f"/{file_path}"

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('UPDATE posts SET date = ?, time = ?, social_network = ?, text = ?, image_path = ? WHERE id = ? AND user_id = ?',
                  (date, time, social_network, text, image_path, post_id, current_user.id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Publicación actualizada'}), 200
    except Exception as e:
        logger.error(f"Error en update_post: {e}")
        return jsonify({'error': 'Error al actualizar publicación'}), 500

@app.route('/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT image_path FROM posts WHERE id = ? AND user_id = ?', (post_id, current_user.id))
        post = c.fetchone()
        if post and post[0]:
            try:
                os.remove(post[0][1:])  # Elimina el archivo del sistema
            except:
                pass
        c.execute('DELETE FROM posts WHERE id = ? AND user_id = ?', (post_id, current_user.id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Publicación eliminada'}), 200
    except Exception as e:
        logger.error(f"Error en delete_post: {e}")
        return jsonify({'error': 'Error al eliminar publicación'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)