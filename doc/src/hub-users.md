# For hub users

Hub users log in to the hub via a learning management system.
Each user has its own JupyterLab on the hub and its own directory for storing files.

```{contents}
---
local: true
backlinks: none
---
```

(cumbersome-errors)=
## Cumbersome error messages

In rare circumstances, JupyterLab may show cumbersome messages ('Directory "" not found', 'No server available.', aso.).
Ignore those messages (click 'Dismiss').
After a few seconds, everything should work as expected.
The reason for this behavior is a restart of JupyterHub in the background due to configuration changes.

## Missing context menu items in file browser

With old Firefox versions some context menu items (like Copy and Paste, for instance) aren't shown if right-clicking a file in JupyterLab's file browser. Either update Firefox or use the follow workaround:
1. Open the URL `about:config` in the browser.
2. Search for `layout.css.has-selector.enabled`.
3. Set the value to `true`.

See [JupyterLab issue 16391](https://github.com/jupyterlab/jupyterlab/issues/16391) for some background information.

## Restarting JupyterLab

If something goes completely wrong or if you have installed new Python environments (see below), restart JupyterLab: click 'File', then 'Hub Control Panel'.
In the control panel, click 'Stop My Server' followed by 'Start My Server'.

## Terminals

To install additional Python packages or to run any other Linux command, start a terminal via JupyterLab's Launcher Tab.

The terminal accepts all Linux/Bash commands.
For basic usage information, see [The Linux command line for beginners](https://ubuntu.com/tutorials/command-line-for-beginners) or [Introduction to the Linux Command Line Interface](https://www.marquette.edu/high-performance-computing/linux-intro.php) or [Learning the Shell](https://linuxcommand.org/lc3_learning_the_shell.php).

Close the terminal by typing `logout`.

## Python environments

Python environments are managed via `conda`.
For installing Python packages in a `conda` environment `pip` is available, too.

### Global environment

There's a global Python environment named `python3` available to all users.
This environment is read-only, that is, you are not allowed to install additional packages or to update packages in this environment.

Additional global environments may be installed by your hub's container admin.

```{warning}
Using `pip` in a readonly `conda` environment installs packages locally, potentially messing up the environment.
Use `pip` only in local environments created by you (see below).
```

### Local environments

You may create additional Python environments available only to you.
Either create a new environment from scratch or clone an existing environment and modify it.

Details on working with conda may be found in [conda's documentation](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

#### New environment from scratch

In JupyterLab, open a terminal and proceed as follows:
1. Create a new conda environment and install the `ipykernel` package to the new environment.
   ```
   conda create -y --name NAME_OF_NEW_ENV ipykernel
   ```
2. (optional) Rename the new environment's Python kernel. Default name is `Python 3 (ipykernel)`.
   ```
   conda activate NAME_OF_NEW_ENV
   python -m ipykernel install --sys-prefix --display-name 'NEW DISPLAY NAME OF KERNEL'
   ```
3. Update Jupyter's kernel list.
   ```
   conda activate jhub
   python -m nb_conda_kernels list
   ```

The kernel of the new environment will be available in your JupyterLab after a few seconds.

Install packages via:
```
conda activate NAME_OF_NEW_ENV
conda install PACKAGE_NAME
```

#### Clone an environment

Get a list of available environments with
```
conda env list
```
in a terminal. The default environment is `python3`. This is a good starting point for cloning.

Then proceed as described above for new environments, but in step 1 use
```
conda create --name NAME_OF_NEW_ENV --clone NAME_OF_EXISTING_ENV
```

#### Remove an environment

To remove an environment create by you open a terminal and run
```
conda remove --name NAME_OF_ENV --all
```
Then update Jupyter's kernel list:
```
conda activate jhub
python -m nb_conda_kernels list
```

(hub-users-file-transfer)=
## File transfer

If the jupyter-fs extension is available in your JupyterLab, you may set up access to external file systems like cloud storage or Windows shares.

In JupyterLab's menu click 'Settings', 'Settings Editor', 'jupyter-fs', 'Add'.
Choose a name for the external resource and provide a URL:
* for WebDAV (Nextcloud, for instance) use `webdavs://YOUR_CLOUD_USERNAME:{{password}}@YOUR_CLOUDS_WEBDAV_URL` (`{{password}}` may be replaced by your cloud password if you don't want to be asked for the password at JupyterLab start-up; special characters like `@` in your cloud's WebDAV URL have to be %-quoted, `@` is `%40`, for instance),
* for local file systems on the host machine use `osfs://PATH` (to get access to your home directory via jupyter-fs use `osfs://~/`, for instance),
* for Windows shares use `smb://YOUR_WINDOWS_USERNAME:{{passwd}}@SERVER/PATH?name-port=3669` (not tested by Ananke team),
* for other supported resources, have a look at [Index of Filesystems](https://www.pyfilesystem.org/page/index-of-filesystems/) (non-built-in file systems may require additional setup by your admin).

In the auth list choose 'ask'.

```{note}
Each resource you specify in the settings yields an additional file browser (tree symbols in the left vertical toolbar).
Files may be copied between different jupyter-fs resources, but not between jupyter-fs and JupyterLab's original file browser.
Thus, it's a good idea to always have a jupyter-fs resource for your home directory.
```

## JupyterLab real-time collaboration

### Collaboration rooms

If your JupyterHub provides real-time collaboration (RTC), click 'File' and 'Hub Control Panel' in your JupyterLab's menu.
In the top bar, click 'Services' and choose a collaboration room.
Inside such a collaboration room all users see all other user's edits and cell executions.

```{note}
In collaboration rooms files will be autosaved every second. Thus, there's no need for manual saving.
```

### Sharing your personal JupyterLab

You may also share your personal JupyterLab session with other users. But be careful! Other users with access to your Lab session have read and write access to all your files! To enable RTC for your Lab run
```
jupyter labextension disable --level=user @jupyter/collaboration-extension
jupyter labextension enable --level=user @jupyter/collaboration-extension
```
(both lines!) in a terminal. Then restart your server ('File', 'Hub Control Panel', 'Stop My Server', 'Start My Server').
In the upper right corner you should see a share link button. Everyone who has this link may join your Lab session.

### User name and avatar

At the moment there is no support for setting your displayed user name in collaboration rooms. Initials, color and symbol are chosen by JupyterLab. With the following workaround you may set at least your initials and your color:
1. Join a collaboration room.
2. Open your browser's developer tools (Firefox: 'Tools', 'Browser Tools', Web Developer Tools'; Chromium: 'More Tools', 'Developer Tools').
3. Navigate to the sites local storage (Firefox: 'Storage', 'Local Storage'; Chromium: 'Application', 'Local storage').
4. Edit (double click) the value of key '@jupyterlab/services:UserManager#user'.
5. Refresh your browser (press F5).

## TensorFlow and GPUs

If your JupyterHub provides GPU access via TensorFlow you may want (or have) to restrict your TensorFlow commands to a subset of available GPUs. Else GPUs may be blocked for other users.

To get a list of available GPUs and their current load open a terminal and run `nvidia-smi`.

To select one or more GPUs for your code to run on use the following code snipped at the top of your Jupyter notebook:
```python
import tensorflow as tf

gpus = tf.config.list_physical_devices('GPU')
print(gpus)

# new cell

gpus = gpus[0]  # or gpus = gpus[1:3], for instance
tf.config.set_visible_devices(gpus, 'GPU')
```

## System load

To get system load information open a terminal and run `htop`. To close `htop` press Q.

## Autocompletion

If [Jupyter LSP](https://github.com/jupyter-lsp/jupyterlab-lsp) is available on your JupyterHub, you should open a terminal in JupyterLab and run
```
cd ~
ln -s / .lsp_symlink
```
once. This makes more detailed package information available to Jupyter LSP.
