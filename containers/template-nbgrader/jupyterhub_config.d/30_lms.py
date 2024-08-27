# configure LMS for JupyterHub

c = get_config()  # noqa

# configuration data provided by your LMS
base_url = 'URL_OF_LMS'
c.LTI13Authenticator.client_id = ['CLIENT_ID']
c.LTI13Authenticator.issuer = base_url
c.LTI13Authenticator.authorize_url = f'{base_url}/AUTH_LOGIN_PATH'
c.LTI13Authenticator.jwks_endpoint = f'{base_url}/KEY_SET_PATH'
c.LTI13Authenticator.access_token_url = f'{base_url}/ACCESS_TOKEN_PATH'
