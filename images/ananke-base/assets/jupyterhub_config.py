# Configuration file for jupyterhub.

import fcntl
import json
import logging
import subprocess
from glob import glob

from ltiauthenticator.lti13.auth import LTI13Authenticator
from ltiauthenticator.lti13.handlers import LTI13CallbackHandler

c = get_config()  # noqa

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)1.1s %(asctime)s.%(msecs)03d %(module)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

#-------------------------------------------------------------------------------
# general config
#-------------------------------------------------------------------------------

c.JupyterHub.bind_url = 'http://:8000'

# c.JupyterHub.logo_file = ''

c.JupyterHub.cookie_secret_file = '/opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_cookie_secret'
c.JupyterHub.db_url = 'sqlite:///opt/conda/envs/jhub/etc/jupyterhub/jupyterhub.sqlite'
c.ConfigurableHTTPProxy.pid_file = '/opt/conda/envs/jhub/etc/jupyterhub/jupyterhub-proxy.pid'

c.Authenticator.admin_users = set()

c.JupyterHub.authenticator_class = 'ltiauthenticator.lti13.auth.LTI13Authenticator'

# start with JupyterLab
c.Spawner.default_url = '/lab'

#-------------------------------------------------------------------------------
# post_auth_hook
#-------------------------------------------------------------------------------

c.post_auth_hook_callbacks = []

async def post_auth_callback(authenticator: LTI13Authenticator, handler: LTI13CallbackHandler, authentication: dict) -> dict:
    """
    Optional hook to run necessary bootstrapping tasks.
    If any of these tasks returns `True` the JupyterHub will be restarted.

    Parameters
    ----------
    authenticator : LTI13Authenticator
        The JupyterHub LTI 1.3 Authenticator.
    handler : LTI13CallbackHandler
        Handles JupyterHub authentication requests responses according to the LTI 1.3 standard.
    authentication : dict
        The authentication dict for the user.

    Returns
    -------
    dict
        The (altered) authentication dict for the user.

    Notes
    -----
        The username on Debian has to start with a letter, which is why the letter u is prefixed.
    """
    
    logging.debug('Running post authentication hooks')
    
    needs_restart  = False
    authentication['name'] = 'u' + authentication['name']    # usernames have to start with a-z on Debian
    for callback in c.post_auth_hook_callbacks:
        if await callback(authenticator, handler, authentication):
            needs_restart = True

    logging.debug('Finished post authentication hooks. Needs restart: ' + str(needs_restart))

    if needs_restart:
        logging.info('restarting hub in 5 seconds...')
        subprocess.run(['systemd-run', '--on-active=5', 'systemctl', 'restart', 'jupyterhub'])
    
    return authentication

c.Authenticator.post_auth_hook = post_auth_callback

#-------------------------------------------------------------------------------
# write LTI data to logs
#-------------------------------------------------------------------------------

async def log_lti_data(authenticator: LTI13Authenticator, handler: LTI13CallbackHandler, authentication: dict) -> bool:
    """
    Additional bootstrapping function to log LTI relevant data.
    This hook will be called within the post_auth_callback() function and will always return `False`.
    This behaviour is necessary for the check if a restart is needed, see post_auth_callback().

    Parameters
    ----------
    authenticator : LTI13Authenticator
        The JupyterHub LTI 1.3 Authenticator.
    handler : LTI13CallbackHandler
        Handles JupyterHub authentication requests responses according to the LTI 1.3 standard.
    authentication : dict
        The authentication dict for the user.

    Returns
    -------
    bool
        Always `False`, as no restart of the JupyterHub is required.

    Notes
    -----
        The parameters `handler` and `authentication` have to be supplied, even though they are not accessed.
    """
    
    logging.debug(f'Received following LTI data: {authentication.get("auth_state")}')

    return False

c.post_auth_hook_callbacks.append(log_lti_data)

#-------------------------------------------------------------------------------
# user data base
#-------------------------------------------------------------------------------

c.user_data_path = '/opt/user_data.json'
logging.info('Reading user data base ' + c.user_data_path)
with open(c.user_data_path) as f:
    user_data = json.load(f)
logging.debug(str(len(user_data)) + ' users in data base')

async def update_user_data(authenticator: LTI13Authenticator, handler: LTI13CallbackHandler, authentication: dict) -> False:
    """
    Additional bootstrapping function to update the user database if necessary.
    This hook will be called within the post_auth_callback() function and will always return `False`.
    This behaviour is necessary for the check if a restart is needed, see post_auth_callback().

    Parameters
    ----------
    authenticator : LTI13Authenticator
        The JupyterHub LTI 1.3 Authenticator.
    handler : LTI13CallbackHandler
        Handles JupyterHub authentication requests responses according to the LTI 1.3 standard.
    authentication : dict
        The authentication dict for the user.

    Returns
    -------
    bool
        Always `False`, as no restart of the JupyterHub is required.

    Notes
    -----
        The parameters `handler` and `authentication` have to be supplied, even though they are not accessed.
    """
    
    username = authentication.get('name')
    logging.debug(f'Looking up user {username} in data base.')
    
    data = user_data.get(username, {})
    first = authentication.get('auth_state').get('given_name')
    last = authentication.get('auth_state').get('family_name')
    email = authentication.get('auth_state').get('email')
    sub = authentication.get('auth_state').get('sub')
    update = False
    if first and data.get('first') != first:
        data['first'] = first
        update = True
    if last and data.get('last') != last:
        data['last'] = last
        update = True
    if email and data.get('email') != email:
        data['email'] = email
        update = True

    if update or len(data) == 0: # len==0 is equivalent to new user without name/email info in LTI data
        logging.debug(f'User {username} is new or came in with new name/email. Updating user data base')
        data['lms_uid'] = sub
        user_data[username] = data
        with open(c.user_data_path, 'w') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            json.dump(user_data, f)
            fcntl.flock(f, fcntl.LOCK_UN)

    return False

c.post_auth_hook_callbacks.append(update_user_data)

#-------------------------------------------------------------------------------
# Authenticator
#-------------------------------------------------------------------------------

c.LTI13Authenticator.username_key = 'sub'
c.LTI13LaunchValidator.time_leeway = '0'
c.LTI13LaunchValidator.max_age = '600'

#-------------------------------------------------------------------------------
# Spawner
#-------------------------------------------------------------------------------

# prefer user config over env config ()
# https://jupyterhub.readthedocs.io/en/stable/howto/configuration/config-user-env.html#jupyter-environment-configuration-priority
c.Spawner.environment.update({'JUPYTER_PREFER_ENV_PATH': '0'})

c.Spawner.args = ['--KernelSpecManager.ensure_native_kernel=False']
c.JupyterHub.spawner_class = 'systemdspawner.SystemdSpawner'

c.SystemdSpawner.unit_extra_properties = {
    'RuntimeDirectoryPreserve': 'no', # always start with fresh server state (do not remember any state info)
    'User': '{USERNAME}' # set user name
}
c.SystemdSpawner.default_shell = '/bin/bash'
c.SystemdSpawner.disable_user_sudo = True
c.SystemdSpawner.readonly_paths = ['/']
c.SystemdSpawner.readwrite_paths = []
c.SystemdSpawner.dynamic_users = True

#-------------------------------------------------------------------------------
# load all config files from jupyterhub_config.d directory
#-------------------------------------------------------------------------------

config_files = sorted(glob('/opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_config.d/*.py'))
for config_file in config_files:
    load_subconfig(config_file)
