# facebook.py
import requests
import logging

logger = logging.getLogger(__name__)

def get_facebook_auth_url(client_id, redirect_uri):
    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=public_profile"
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
    logger.debug(f"Intercambiando código por token de Facebook: {data}")
    response = requests.post(url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        logger.info(f"Token de Facebook obtenido: {token_data}")
        return token_data.get('access_token')
    logger.error(f"Error al obtener token de Facebook: {response.status_code} - {response.text}")
    return None

def post_to_facebook(caption, image_path, access_token, page_id=None):
    """
    Publica en Facebook (página o perfil, dependiendo de page_id).
    Requiere una URL pública para image_path.
    """
    try:
        url = f"https://graph.facebook.com/v19.0/{page_id or 'me'}/photos" if image_path else f"https://graph.facebook.com/v19.0/{page_id or 'me'}/feed"
        params = {
            'access_token': access_token,
            'message': caption
        }
        if image_path:
            params['url'] = image_path  # URL pública de la imagen

        logger.debug(f"Publicando en Facebook: {params}")
        response = requests.post(url, data=params)
        if response.status_code == 200 or response.status_code == 201:
            logger.info("Publicación en Facebook exitosa")
            return True
        logger.error(f"Error al publicar en Facebook: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        logger.error(f"Error al publicar en Facebook: {str(e)}")
        return False