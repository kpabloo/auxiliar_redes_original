# instagram.py
import requests
import logging

logger = logging.getLogger(__name__)

def get_instagram_auth_url(client_id, redirect_uri):
    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=instagram_basic,instagram_content_publish"
        f"&response_type=code"
    )
    return auth_url

def exchange_code_for_token(code, client_id, client_secret, redirect_uri):
    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code': code
    }
    logger.debug(f"Intercambiando código por token: {data}")
    response = requests.post(url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        logger.info(f"Token obtenido: {token_data}")
        return token_data.get('access_token')
    logger.error(f"Error al obtener token: {response.status_code} - {response.text}")
    return None

def post_to_instagram(caption, image_path, access_token):
    """
    Publica en Instagram usando la Graph API.
    Nota: Requiere que image_path sea una URL pública accesible.
    """
    try:
        # Paso 1: Crear un contenedor de medios
        url = "https://graph.instagram.com/v19.0/me/media"
        params = {
            'access_token': access_token,
            'caption': caption,
            'image_url': image_path  # Esto debe ser una URL pública, no un path local
        }
        logger.debug(f"Creando contenedor de medios: {params}")
        response = requests.post(url, params=params)
        if response.status_code != 200:
            logger.error(f"Error al crear contenedor: {response.status_code} - {response.text}")
            return False

        media_data = response.json()
        media_id = media_data.get('id')
        if not media_id:
            logger.error(f"No se obtuvo media_id: {media_data}")
            return False

        # Paso 2: Publicar el contenedor
        publish_url = f"https://graph.instagram.com/{media_id}/publish"
        publish_params = {
            'access_token': access_token
        }
        logger.debug(f"Publicando contenedor con media_id: {media_id}")
        publish_response = requests.post(publish_url, params=publish_params)
        if publish_response.status_code == 200:
            logger.info("Publicación en Instagram exitosa")
            return True
        logger.error(f"Error al publicar: {publish_response.status_code} - {publish_response.text}")
        return False
    except Exception as e:
        logger.error(f"Error al publicar en Instagram: {str(e)}")
        return False