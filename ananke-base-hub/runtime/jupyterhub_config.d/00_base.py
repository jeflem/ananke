# basic hub configuration

c = get_config()  # noqa

# hub URL (www.some-domain.org/testhub --> 'testhub/')
c.JupyterHub.base_url = '/'

# log level
c.Application.log_level = 'INFO'
