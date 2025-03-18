# app.py
from flask import Flask, redirect, request
from flask_cors import CORS
from flask_login import LoginManager, current_user
import logging
import os
from config import Config
from models import init_db, load_user, get_db_connection, get_twitter_tokens, get_instagram_tokens, get_facebook_tokens
from routes import register_routes
import time
import threading
from datetime import datetime
from twitter import post_to_twitter
from instagram import post_to_instagram
from facebook import post_to_facebook

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
            with get_db_connection(Config.DB_CONFIG) as conn:
                c = conn.cursor()
                now = datetime.now().strftime('%Y-%m-%d %H:%M')
                logger.debug(f"Verificando publicaciones programadas a las {now}")
                c.execute("SELECT id, user_id, date, time, social_network, text, image_path FROM posts WHERE date || ' ' || COALESCE(time, '') <= %s", (now,))
                posts = c.fetchall()
                for post in posts:
                    post_id, user_id, date, post_time, social_network, text, image_path = post
                    if social_network == 'Twitter/X':
                        tokens = get_twitter_tokens(user_id, Config.DB_CONFIG)
                        if tokens:
                            access_token, access_token_secret = tokens
                            if post_to_twitter(text, image_path, access_token, access_token_secret):
                                c.execute('DELETE FROM posts WHERE id = %s', (post_id,))
                                logger.info(f"Publicación {post_id} eliminada tras ser publicada en Twitter")
                    elif social_network == 'Instagram':
                        token = get_instagram_tokens(user_id, Config.DB_CONFIG)
                        if token:
                            if post_to_instagram(text, image_path, token):
                                c.execute('DELETE FROM posts WHERE id = %s', (post_id,))
                                logger.info(f"Publicación {post_id} eliminada tras ser publicada en Instagram")
                    elif social_network == 'Facebook':
                        token = get_facebook_tokens(user_id, Config.DB_CONFIG)
                        if token:
                            if post_to_facebook(text, image_path, token):
                                c.execute('DELETE FROM posts WHERE id = %s', (post_id,))
                                logger.info(f"Publicación {post_id} eliminada tras ser publicada en Facebook")
                conn.commit()
            elapsed_time = time.time() - start_time
            sleep_time = max(60 - elapsed_time, 0)
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
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)