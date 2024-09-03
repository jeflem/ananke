import logging
import os
import secrets
from tempfile import mkdtemp

from flask import Flask
from flask_session import Session

from models.config_loaders import FlaskConfigLoader
from routes.assignments_route import assignments_bp
from routes.courses_route import courses_bp
from routes.grades_route import grades_bp
from routes.home_route import home, home_bp, authenticated
from routes.problems_route import problems_bp
from routes.utils_routes import utils_bp

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)1.1s %(asctime)s.%(msecs)03d %(module)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=secrets.token_bytes(32),
    SESSION_COOKIE_NAME='kore-sessionid',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,  # should be True in case of HTTPS usage (production)
    SESSION_COOKIE_SAMESITE=None,  # should be 'None' in case of HTTPS usage (production)
    SESSION_TYPE='filesystem',
    SESSION_FILE_DIR=mkdtemp(),
    DEBUG_TB_INTERCEPT_REDIRECTS=False
)
Session(app)  # store session data on server (not on client)

# Initialize the ConfigLoader class and load both (general and LTI) configuration files.
config_loader = FlaskConfigLoader(
    kore_config_file_path='/opt/kore/config/config.json',
    lti_config_file_path='/opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_config.d/30_lms.py',
    app=app
)
config_loader.load_config()

# Store global parameters and the ConfigLoader in the app context.
prefix = os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '/')
logging.info(f'JupyterHub service prefix for Kore: {prefix}')
config_loader.store_parameter(key='PREFIX', value=prefix)
config_loader.store_parameter(key='KORE_TOKEN', value=os.environ['JUPYTERHUB_API_TOKEN'])
config_loader.store_in_app_context()

# Register blueprints with the app.
home_bp.before_request(authenticated(home, app.config['KORE_TOKEN']))
app.register_blueprint(home_bp, url_prefix=prefix)
app.register_blueprint(grades_bp, url_prefix=prefix)
app.register_blueprint(courses_bp, url_prefix=prefix)
app.register_blueprint(assignments_bp, url_prefix=prefix)
app.register_blueprint(problems_bp, url_prefix=prefix)
app.register_blueprint(utils_bp, url_prefix=prefix)


if __name__ == '__main__':
    app.run()
