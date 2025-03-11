# routes.py
from flask import request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user, current_user
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from models import get_db_connection, User, get_twitter_tokens, save_twitter_tokens
from utils import allowed_file
from twitter import post_to_twitter
import tweepy
from config import Config
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

def register_routes(app, db_config, allowed_extensions, upload_folder):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            conn = get_db_connection(db_config)
            c = conn.cursor()
            c.execute('SELECT id, password FROM users WHERE username = %s', (username,))
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
            conn = get_db_connection(db_config)
            c = conn.cursor()
            try:
                c.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_password))
                conn.commit()
                flash('Usuario registrado, ahora inicia sesión')
                return redirect(url_for('login'))
            except psycopg2.IntegrityError:
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
        twitter_linked = get_twitter_tokens(current_user.id, db_config) is not None
        return render_template('index.html', twitter_linked=twitter_linked)

    @app.route('/link_twitter')
    @login_required
    def link_twitter():
        # Obtener la URL de callback dinámicamente
        scheme = request.scheme
        host = request.host
        callback_url = f"{scheme}://{host}/twitter_callback"
        
        # Configurar OAuthHandler de Tweepy con la URL de callback dinámica
        auth = tweepy.OAuthHandler(Config.TWITTER_API_KEY, Config.TWITTER_API_SECRET, callback=callback_url)
        
        try:
            # Obtener la URL de autorización y redirigir al usuario para autorizar la aplicación
            redirect_url = auth.get_authorization_url()
            
            # Guardar el token de solicitud para usarlo más tarde
            session['request_token'] = auth.request_token
            
            return redirect(redirect_url)
        except tweepy.TweepError as e:
            # Manejo de errores en caso de que la autenticación falle
            logger.error(f"Error al obtener URL de autorización: {e}")
            flash('Error al vincular Twitter')
            return redirect(url_for('index'))

    @app.route('/twitter_callback')
    @login_required
    def twitter_callback():
        verifier = request.args.get('oauth_verifier')
        if not verifier or 'request_token' not in session:
            flash('Error en la vinculación de Twitter')
            return redirect(url_for('index'))

        auth = tweepy.OAuthHandler(Config.TWITTER_API_KEY, Config.TWITTER_API_SECRET)
        auth.request_token = session.pop('request_token')
        try:
            access_token, access_token_secret = auth.get_access_token(verifier)
            save_twitter_tokens(current_user.id, access_token, access_token_secret, db_config)
            flash('Cuenta de Twitter vinculada exitosamente')
        except tweepy.TweepError as e:
            logger.error(f"Error al obtener tokens de acceso: {e}")
            flash('Error al vincular Twitter')
        return redirect(url_for('index'))

    @app.route('/posts', methods=['GET'])
    @login_required
    def get_posts():
        try:
            conn = get_db_connection(db_config)
            c = conn.cursor()
            c.execute('SELECT id, date, time, social_network, text, image_path FROM posts WHERE user_id = %s', (current_user.id,))
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
                if file and allowed_file(file.filename, allowed_extensions):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_folder, f"{current_user.id}_{filename}")
                    file.save(file_path)
                    image_path = f"/{file_path}"

            conn = get_db_connection(db_config)
            c = conn.cursor()
            c.execute('INSERT INTO posts (user_id, date, time, social_network, text, image_path) VALUES (%s, %s, %s, %s, %s, %s)',
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
                if file and allowed_file(file.filename, allowed_extensions):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_folder, f"{current_user.id}_{filename}")
                    file.save(file_path)
                    image_path = f"/{file_path}"

            conn = get_db_connection(db_config)
            c = conn.cursor()
            c.execute('UPDATE posts SET date = %s, time = %s, social_network = %s, text = %s, image_path = %s WHERE id = %s AND user_id = %s',
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
            conn = get_db_connection(db_config)
            c = conn.cursor()
            c.execute('SELECT image_path FROM posts WHERE id = %s AND user_id = %s', (post_id, current_user.id))
            post = c.fetchone()
            if post and post[0]:
                try:
                    os.remove(post[0][1:])
                except:
                    pass
            c.execute('DELETE FROM posts WHERE id = %s AND user_id = %s', (post_id, current_user.id))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Publicación eliminada'}), 200
        except Exception as e:
            logger.error(f"Error en delete_post: {e}")
            return jsonify({'error': 'Error al eliminar publicación'}), 500