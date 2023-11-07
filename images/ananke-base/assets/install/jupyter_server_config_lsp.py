# jupyterlab-lsp configuration for jupyter server

c = get_config()

# make content manager provide hidden files, so jupyter-lsp may follow the .lsp_symlink symlink
c.ContentsManager.allow_hidden = True
