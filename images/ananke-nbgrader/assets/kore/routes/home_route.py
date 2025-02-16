import json
import logging

from flask import make_response
from flask import redirect as flask_redirect
from flask import render_template, Blueprint, current_app
from flask import request as flask_request
from flask import session as flask_session
from jupyterhub.services.auth import HubOAuth

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
    data = {}

    config_loader = current_app.config['CONFIG_LOADER']
    if config_loader.preflight_error:
        data['preflight_error'] = config_loader.preflight_error

    user_name = user.get('name')
    data['user'] = user_name

    try:
        with open(f'runtime/lti_{user_name}.json', 'r') as file:
            lti_state = json.load(file)
        data['url'] = f"{lti_state['https://purl.imsglobal.org/spec/lti/claim/target_link_uri']}/services/kore"
    except (FileNotFoundError, PermissionError, ValueError, OSError):
        logging.error(f'LTI state file for user {user_name} not found!')

        if 'preflight_error' in data:
            data['preflight_error'] += f'\nError while reading lti state file.'
        else:
            data['preflight_error'] = 'Error while reading lti state file.'

    logging.info(f'User {user_name} is accessing home page of kore service.')

    return render_template('home.html.jinja', data=data)
