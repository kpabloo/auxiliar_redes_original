# models.py
import psycopg2
from flask_login import UserMixin
import logging

logger = logging.getLogger(__name__)

class User(UserMixin):
    def __init__(self, id):
        self.id = id

def get_db_connection(db_config):
    return psycopg2.connect(**db_config)

def init_db(db_config):
    try:
        with get_db_connection(db_config) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                date TEXT NOT NULL,
                time TEXT,
                social_network TEXT NOT NULL,
                text TEXT NOT NULL,
                image_path TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS twitter_tokens (
                user_id INTEGER PRIMARY KEY,
                access_token TEXT NOT NULL,
                access_token_secret TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')
            # Nueva tabla para tokens de Instagram
            c.execute('''CREATE TABLE IF NOT EXISTS instagram_tokens (
                user_id INTEGER PRIMARY KEY,
                access_token TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')
            conn.commit()
            logger.info("Base de datos inicializada/actualizada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")

def load_user(user_id, db_config):
    try:
        with get_db_connection(db_config) as conn:
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE id = %s', (user_id,))
            user = c.fetchone()
            return User(user[0]) if user else None
    except Exception as e:
        logger.error(f"Error al cargar usuario: {e}")
        return None

def get_twitter_tokens(user_id, db_config):
    try:
        with get_db_connection(db_config) as conn:
            c = conn.cursor()
            c.execute('SELECT access_token, access_token_secret FROM twitter_tokens WHERE user_id = %s', (user_id,))
            tokens = c.fetchone()
            return tokens if tokens else None
    except Exception as e:
        logger.error(f"Error al obtener tokens de Twitter: {e}")
        return None

def save_twitter_tokens(user_id, access_token, access_token_secret, db_config):
    try:
        with get_db_connection(db_config) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO twitter_tokens (user_id, access_token, access_token_secret) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET access_token = %s, access_token_secret = %s',
                      (user_id, access_token, access_token_secret, access_token, access_token_secret))
            conn.commit()
            logger.info(f"Tokens de Twitter guardados para user_id {user_id}")
    except Exception as e:
        logger.error(f"Error al guardar tokens de Twitter: {e}")

# Nuevas funciones para Instagram
def get_instagram_tokens(user_id, db_config):
    try:
        with get_db_connection(db_config) as conn:
            c = conn.cursor()
            c.execute('SELECT access_token FROM instagram_tokens WHERE user_id = %s', (user_id,))
            token = c.fetchone()
            return token[0] if token else None
    except Exception as e:
        logger.error(f"Error al obtener tokens de Instagram: {e}")
        return None

def save_instagram_tokens(user_id, access_token, db_config):
    try:
        with get_db_connection(db_config) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO instagram_tokens (user_id, access_token) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET access_token = %s',
                      (user_id, access_token, access_token))
            conn.commit()
            logger.info(f"Token de Instagram guardado para user_id {user_id}")
    except Exception as e:
        logger.error(f"Error al guardar tokens de Instagram: {e}")