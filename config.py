import os

class Config:
    SECRET_KEY = 'tu_clave_secreta_aqui'  # Cambia esto por algo seguro
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Configuración de PostgreSQL
    DB_CONFIG = {
        'dbname': 'auxiliar_redes',  # Cambia esto
        'user': 'postgres',           # Cambia esto
        'password': 'postgres',    # Cambia esto
        'host': 'localhost',
        'port': '5432'
    }

    # Configuración de Twitter API
    TWITTER_API_KEY = 'JuqEmy9g0o8pyZpzIjiedFVVh'         # Reemplaza con tu API Key real
    TWITTER_API_SECRET = '6CxZ6kpMTm32pRWH9ZRAw83tfWAmsOjNCy5amnNGEaVYynV0mL'   # Reemplaza con tu API Secret real
#    TWITTER_ACCESS_TOKEN = 'tu_access_token_aqui'  # Opcional, reemplaza si lo tienes
#    TWITTER_ACCESS_TOKEN_SECRET = 'tu_access_token_secret_aqui'  # Opcional

    # Configuracion Instagram
    INSTAGRAM_CLIENT_ID = os.environ.get('660391139881627')
    INSTAGRAM_CLIENT_SECRET = os.environ.get('42d54108a93f445d6ff8cf137d90515b')
    INSTAGRAM_REDIRECT_URI = 'https://socialbotic.geco.com.ar/instagram_callback'

    FACEBOOK_APP_ID = '530713843385760'  # Reemplaza con el App ID de Facebook
    FACEBOOK_APP_SECRET = '15ea97e60d2b312b1db892a6d952c7b9'  # Reemplaza con el App Secret de Facebook
    FACEBOOK_REDIRECT_URI = 'https://socialbotic.geco.com.ar/facebook_callback'

# Crear carpeta de uploads si no existe
if not os.path.exists(Config.UPLOAD_FOLDER):
    os.makedirs(Config.UPLOAD_FOLDER)