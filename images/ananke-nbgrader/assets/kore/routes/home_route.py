import logging

from flask import make_response
from flask import redirect as flask_redirect
from flask import render_template, Blueprint, current_app
from flask import request as flask_request
from flask import session as flask_session
from jupyterhub.services.auth import HubOAuth

from models.lti_file_reader import LTIFileReader

home_bp = Blueprint('home', __name__)


def authenticated(route_function, kore_token):
    """
    Decorator function for authenticating with the Hub via OAuth.
    """

    auth = HubOAuth(api_token=kore_token, cache_max_age=60)

    def wrapper(*args, **kwargs):
        token = flask_session.get('token')

        if token:
            user = auth.user_for_token(token)
        else:
            user = None
        if user:
            return route_function(user, *args, **kwargs)
        else:
            # Redirect to login-url on failed auth.
            state = auth.generate_state(next_url=flask_request.path)
            response = make_response(flask_redirect(auth.login_url + f'&state={state}'))
            response.set_cookie(auth.state_cookie_name, state)
            return response

    return wrapper


@home_bp.route('', methods=['GET'])
def home(user):
    # Defining object containing relevant information for the HTML template.
    tmpl_data = {}

    config_loader = current_app.config['CONFIG_LOADER']
    if config_loader.preflight_error:
        tmpl_data['preflight_error'] = config_loader.preflight_error

    user_name = user.get('name')
    tmpl_data['user'] = user_name

    logging.info(f'User {user_name} is accessing home page of kore service.')

    lti_file_reader: LTIFileReader = LTIFileReader(user_name=user_name, file_path=f'runtime/lti_{user_name}.json')
    lti_file_reader.read_file()

    if not lti_file_reader.read_success:
        if 'preflight_error' in tmpl_data:
            tmpl_data['preflight_error'] += f'\n{lti_file_reader.preflight_error}'
        else:
            tmpl_data['preflight_error'] = lti_file_reader.preflight_error

    return render_template('home.html.jinja', data=tmpl_data)
