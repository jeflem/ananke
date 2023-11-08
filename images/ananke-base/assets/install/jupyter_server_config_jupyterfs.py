# configuration for jupyter server

import jupyterfs.metamanager

c = get_config()

# use jupyterfs for file access
c.ServerApp.contents_manager_class = jupyterfs.metamanager.MetaManager

# make jupyterfs provide hidden files, too
c.ContentsManager.allow_hidden = True

# default jupyterfs resources for all users
c.JupyterFs.resources = [
    {
        'name': 'home',
        'url': 'osfs://~'
    },
]
 
