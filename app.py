# app.py
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
import logging
from config import Config
from models import init_db, load_user, get_db_connection, get_twitter_tokens
from routes import register_routes
import time
import threading
from datetime import datetime
from twitter import post_to_twitter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = Config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def user_loader(user_id):
    return load_user(user_id, Config.DB_CONFIG)

# Registrar rutas
register_routes(app, Config.DB_CONFIG, Config.ALLOWED_EXTENSIONS, Config.UPLOAD_FOLDER)

# Variable global para controlar el hilo
scheduler_running = False

def check_scheduled_posts():
    global scheduler_running
    if scheduler_running:
        logger.warning("Scheduler ya está corriendo, omitiendo nueva instancia")
        return
    scheduler_running = True
    try:
        while True:
            start_time = time.time()
            try:
                conn = get_db_connection(Config.DB_CONFIG)
                c = conn.cursor()
                now = datetime.now().strftime('%Y-%m-%d %H:%M')  # Formato: "YYYY-MM-DD HH:MM"
                logger.debug(f"Verificando publicaciones programadas a las {now}")
                c.execute("SELECT id, user_id, date, time, social_network, text, image_path FROM posts WHERE date || ' ' || COALESCE(time, '') <= %s AND social_network = %s", (now, 'Twitter/X'))
                posts = c.fetchall()
                if posts:
                    logger.debug(f"Encontradas {len(posts)} publicaciones para procesar")
                for post in posts:
                    post_id, user_id, date, post_time, social_network, text, image_path = post
                    tokens = get_twitter_tokens(user_id, Config.DB_CONFIG)
                    if tokens:
                        access_token, access_token_secret = tokens
                        logger.info(f"Publicando para user_id {user_id}: {text}")
                        if post_to_twitter(text, image_path, access_token, access_token_secret):
                            c.execute('DELETE FROM posts WHERE id = %s', (post_id,))
                            logger.info(f"Publicación {post_id} eliminada tras ser publicada en Twitter")
                        else:
                            logger.error(f"Fallo al publicar post {post_id}")
                    else:
                        logger.warning(f"No se encontraron tokens para user_id {user_id}")
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error al verificar publicaciones programadas: {e}")
            # Ajustar el tiempo de espera para que sea exactamente 60 segundos
            elapsed_time = time.time() - start_time
            sleep_time = max(60 - elapsed_time, 0)
            logger.debug(f"Esperando {sleep_time:.2f} segundos hasta la próxima verificación")
            time.sleep(sleep_time)
    finally:
        scheduler_running = False

def run_scheduler():
    if not scheduler_running:
        scheduler_thread = threading.Thread(target=check_scheduled_posts, daemon=True)
        scheduler_thread.start()
    else:
        logger.warning("Intentando iniciar scheduler, pero ya está activo")

if __name__ == '__main__':
    init_db(Config.DB_CONFIG)
    run_scheduler()
    app.run(debug=True, port=5000)