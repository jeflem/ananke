# create collaboration rooms

import os
import pwd

# create public rooms
for idx, room in enumerate(public_rtc_rooms):

    # create user account if not already there
    username = f'rtc-{room}'[:32]
    try:
        pwd.getpwnam(username)
    except KeyError:
        os.system(f'useradd --create-home --shell=/bin/bash {username}')
        os.system(f'usermod -L {username}')
        os.system(f'chown -R {username}:{username} /home/{username}')
        os.system(f'su - {username} -c \
                    "export JUPYTER_PREFER_ENV_PATH=0; \
                    source /opt/conda/etc/profile.d/conda.sh; \
                    conda activate jhub; \
                    jupyter labextension disable --level=user @jupyter/collaboration-extension; \
                    jupyter labextension enable --level=user @jupyter/collaboration-extension; \
                    jupyter labextension disable --level=user nbgrader:assignment-list; \
                    jupyter labextension disable --level=user nbgrader:validate-assignment"')

    # create JHub service for room
    port = 8500 + idx
    c.JupyterHub.services.append({
        'name': f'{room}',
        'url': f'http://127.0.0.1:{port}',
        'command': ['jupyterhub-singleuser', '--KernelSpecManager.ensure_native_kernel=False'],
        'user': f'{username}',
        'cwd': f'/home/{username}',
        'oauth_no_confirm': True
    })

# provide access to public rooms for all users
c.JupyterHub.load_roles.append({
    'name': 'user',
    'scopes': ['self'] + [f'access:services!service={room}' for room in public_rtc_rooms],
})

# create private rooms
for idx, room in enumerate(private_rtc_rooms):

    # create user account if not already there
    username = f'rtc-{room["name"]}'[:32]
    try:
        pwd.getpwnam(username)
    except KeyError:
        os.system(f'useradd --create-home --shell=/bin/bash {username}')
        os.system(f'usermod -L {username}')
        os.system(f'chown -R {username}:{username} /home/{username}')
        os.system(f'su - {username} -c \
                    "export JUPYTER_PREFER_ENV_PATH=0; \
                    source /opt/conda/etc/profile.d/conda.sh; \
                    conda activate jhub; \
                    jupyter labextension disable --level=user @jupyter/collaboration-extension; \
                    jupyter labextension enable --level=user @jupyter/collaboration-extension"')

    # create JHub service for room
    port = 8600 + idx
    c.JupyterHub.services.append({
        'name': f'{room["name"]}',
        'url': f'http://127.0.0.1:{port}',
        'command': ['jupyterhub-singleuser', '--KernelSpecManager.ensure_native_kernel=False'],
        'user': f'{username}',
        'cwd': f'/home/{username}',
        'oauth_no_confirm': True
    })
    
    # provide access to room
    c.JupyterHub.load_roles.append({
        'name': f'{room["name"]}-role',
        'scopes': [f'access:services!service={room["name"]}'],
        'users': room.get('users') or [],
        'groups': room.get('groups') or []
    })
