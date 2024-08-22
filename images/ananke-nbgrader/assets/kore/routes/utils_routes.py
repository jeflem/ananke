import json

from flask import Blueprint, current_app, Response
from flask import jsonify as flask_jsonify
from flask import make_response
from flask import redirect as flask_redirect
from flask import request as flask_request
from flask import session as flask_session
from jupyterhub.services.auth import HubOAuth

from exceptions import ConfigFileError
from misc.utils import load_config

utils_bp = Blueprint('utils', __name__)


@utils_bp.route('/config', methods=['GET'])
def config():
    # Retrieve full course list (active and backed up ones).
    if flask_request.method == 'GET':
        try:
            config_data = load_config(path='/opt/kore/config/config.json')
            return Response(response=json.dumps(config_data), status=200)
        except ConfigFileError:
            return Response(response=json.dumps({'message': 'ConfigFileError'}), status=500)


@utils_bp.route('/oauth_callback')
def oauth_callback():
    prefix = current_app.config['PREFIX']
    kore_token = current_app.config['KORE_TOKEN']
    auth = HubOAuth(api_token=kore_token, cache_max_age=60)

    code = flask_request.args.get('code', None)
    if code is None:
        return 403

    # Validate the state field.
    arg_state = flask_request.args.get('state', None)
    cookie_state = flask_request.cookies.get(auth.state_cookie_name)
    if arg_state is None or arg_state != cookie_state:
        # State doesn't match.
        return 403

    token = auth.token_for_code(code)
    flask_session['token'] = token
    next_url = auth.get_next_url(cookie_state) or prefix
    response = make_response(flask_redirect(next_url))
    return response


@utils_bp.route('/jwks', methods=['GET'])
def get_jwks():
    # Read the public key of Kore.
    with open(file='keys/lti_key.json') as public_key:
        jwk = json.load(public_key)

    # Make JWKS containing the read JWK only.
    jwks = {'keys': [jwk]}

    return flask_jsonify(jwks)
