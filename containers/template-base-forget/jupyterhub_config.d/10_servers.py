# configure single-user server behavior for JupyterHub

import sys

c = get_config()  # noqa

# multiple servers per user allowed?
c.JupyterHub.allow_named_servers = False

# maximum number of servers per user
c.JupyterHub.named_server_limit_per_user = 1

# on hub restart do not restart user servers and proxy
# (hub restart will be more or less transparent to the users)
c.JupyterHub.cleanup_servers = False
c.JupyterHub.cleanup_proxy = False

# maximum number of concurrent users that can be spawning at a time.
# (if set to 0, no limit is enforced)
c.JupyterHub.concurrent_spawn_limit = 100

# shut down user server(s) on logout?
c.JupyterHub.shutdown_on_logout = True

# resource limits (per user server)
c.SystemdSpawner.unit_extra_properties.update({
    'MemoryHigh': '2G', # soft memory limit
    'CPUQuota': '200%' # up to 2 cores
})

# empty home directories at shut down
c.SystemdSpawner.unit_extra_properties.update({
    'ExecStopPost': 'bash -c "rm -rf /var/lib/private/{USERNAME}/* /var/lib/private/{USERNAME}/.*"',
})

#-------------------------------------------------------------------------------
# idle-culler
#-------------------------------------------------------------------------------

c.JupyterHub.load_roles.append({
    'name': 'jupyterhub-idle-culler-role',
    'scopes': ['list:users', 'read:users:activity', 'read:servers', 'delete:servers'],
    'services': ['jupyterhub-idle-culler-service'],
})

c.JupyterHub.services.append({
    'name': 'jupyterhub-idle-culler-service',
    'command': [
        sys.executable, '-m', 'jupyterhub_idle_culler',
        '--cull-every=1800', # check every 30 minutes (in seconds)
        '--timeout=3600' # cull if 1 hour inactive (in seconds)
    ]
})
