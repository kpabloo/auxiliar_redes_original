# twitter.py
import tweepy
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_twitter_client(access_token=None, access_token_secret=None):
    # Usamos tweepy.Client para la API v2
    client = tweepy.Client(
        consumer_key=Config.TWITTER_API_KEY,
        consumer_secret=Config.TWITTER_API_SECRET,
        access_token=access_token,
        access_token_secret=access_token_secret
    )
    return client

def post_to_twitter(text, image_path=None, access_token=None, access_token_secret=None):
    try:
        client = get_twitter_client(access_token, access_token_secret)
        if image_path:
            # Subir la imagen primero
            api_v1 = tweepy.API(tweepy.OAuth1UserHandler(
                Config.TWITTER_API_KEY,
                Config.TWITTER_API_SECRET,
                access_token,
                access_token_secret
            ))
            media = api_v1.media_upload(filename=image_path[1:])
            response = client.create_tweet(text=text, media_ids=[media.media_id])
        else:
            response = client.create_tweet(text=text)
        logger.info(f"Publicado en Twitter: {text}")
        return True
    except Exception as e:
        logger.error(f"Error al publicar en Twitter: {e}")
        return False