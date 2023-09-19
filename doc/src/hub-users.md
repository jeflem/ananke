# For hub users

Hub users login to the hub via a learning management system.
Each user has its own JupyterLab on the hub and its own directory for storing files.

```{contents}
---
local: true
---
```

## Cumbersome error messages

In rare circumstances, JupyterLab may show cumbersome messages ('Directory "" not found', 'No server available.', aso.).
Ignore those messages (click 'Dismiss').
After a few seconds, everything should work as expected.
The reason for this behavior is a restart of JupyterHub in the background due to configuration changes.

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

In JupyterLab, open a terminal and run the following command:
```
conda create -y --name NAME_OF_NEW_ENV
```
To make the new Python environment available as kernel in JupyterLab run:
```
conda activate NAME_OF_NEW_ENV
conda install -y ipykernel
python -m ipykernel install --user --name INTERNAL_NAME_OF_KERNEL --display-name "DISPLAYED NAME OF KERNEL"
```
The kernel will be available in your JupyterLab (reload the launcher tab).

Install packages via:
```
conda activate NAME_OF_NEW_ENV
conda install PACKAGE_NAME
```

#### Clone an environment

In JupyterLab, open a terminal and run the following command:
```
conda create --name NAME_OF_NEW_ENV --clone NAME_OF_EXISTING_ENV
```
Then
```
conda activate NAME_OF_NEW_ENV
python -m ipykernel install --name INTERNAL_NAME_OF_KERNEL --display-name "DISPLAYED NAME OF KERNEL" --user
```

Package installation works as described above.

#### Remove an environment

To remove a local environment, first remove the kernel: open a terminal and run
```
conda activate jhub
jupyter kernelspec list
jupyter kernelspec remove INTERNAL_NAME_OF_KERNEL
```
Then remove the environment with
```
conda remove --name NAME_OF_ENV --all
```

(file-transfer-hub-users)=
## File transfer hub users

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

```{note}
At the time of writing (July 2023) jupyter-fs does not provide support for copying directories.
Copy operation will **fail silently** (there will be a message in your Browsers JavaScript console).
```

(jupyterlab-real-time-collaboration)=
## JupyterLab real-time collaboration

If your JupyterHub provides real-time collaboration, click 'File' and 'Hub Control Panel' in your JupyterLab's menu.
In the top bar, click 'Services' and choose a collaboration room.
Inside such a collaboration room all users see all other user's edits and cell executions.

```{note}
If your hub supports collaboration your files will be autosaved every second (even in your lab, not only in collaboration rooms).
Thus, there's no need for manual saving.
```
