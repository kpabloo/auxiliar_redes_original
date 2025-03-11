import os

class Config:
    SECRET_KEY = 'tu_clave_secreta_aqui'  # Cambia esto por algo seguro
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Configuración de PostgreSQL
    DB_CONFIG = {
        'dbname': 'auxiliar_redes',  # Cambia esto
        'user': 'auxiliar_redes_user',           # Cambia esto
        'password': 'cqpFUAhs4x0EBFAGvPfBE5p6D58tfa9E',    # Cambia esto
        'host': 'dpg-cv8af80gph6c73brdl60-a.oregon-postgres.render.com',
        'port': '5432'
    }

    # Configuración de Twitter API
    TWITTER_API_KEY = 'JuqEmy9g0o8pyZpzIjiedFVVh'         # Reemplaza con tu API Key real
    TWITTER_API_SECRET = '6CxZ6kpMTm32pRWH9ZRAw83tfWAmsOjNCy5amnNGEaVYynV0mL'   # Reemplaza con tu API Secret real
#    TWITTER_ACCESS_TOKEN = 'tu_access_token_aqui'  # Opcional, reemplaza si lo tienes
#    TWITTER_ACCESS_TOKEN_SECRET = 'tu_access_token_secret_aqui'  # Opcional

# Crear carpeta de uploads si no existe
if not os.path.exists(Config.UPLOAD_FOLDER):
    os.makedirs(Config.UPLOAD_FOLDER)