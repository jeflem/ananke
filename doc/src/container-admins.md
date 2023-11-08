# For container admins 

Container admins have a regular user account on the host machine.
They may access the host machine via SSH to install, configure, start and stop the Podman container running the JupyterHub.

```{contents}
---
local: true
---
```

(ssh-login-to-host-machine)=
## SSH login to host machine

The host machine (if configured along the lines of the [instructions for host admins](host-admins.md)) provides SSH access for container admins with two-factor authentication: password plus cryptographic key.

Login to the host machine:
```
ssh -p 986 testhub_user@your-host.your-domain.org
```
where `986` is to be replaced by the host machine's SSH port (ask your host admin for this number).

After the first login, change your password:
```
passwd
```

Logout from the host machine with
```
logout
```

If you are on Windows, you may try [PuTTY](https://www.putty.org/).
Newer variants of Windows 10 (and also Windows 11) provide Linux-like SSH.

(file-transfer)=
## File Transfer

To transfer files to the host machine connect via `sshfs`:
```
sshfs -p 986 testhub_user@your-host.your-domain.org: /your/local/mount/point
```
where `986` is to be replaced by the host machine's SSH port and `/your/local/mount/point` is an empty directory on your local machine (create before first use).
Contents of your home directory then should appear in that directory.

To close the connection run:
```
fusermount -u /your/local/mount/point
```

If you are in Windows, you may try [WinSCP](https://winscp.net).

## Run an Ananke container

### Container files, images and containers

An image is a blueprint for containers.
A *container* is similar to a virtual machine.
Its purpose is to run a program in isolation from other programs on the machine.
From one image, one may create one or more containers.

A container file contains all information relevant to Podman to build an image.

The Ananke project's files are split into four separate parts:
* Directories `images/ananke-base` and `images/ananke-nbgrader` contain all files needed to build Ananke's Podman images (without or with nbgrader).
* In particular, they contain the container files, named `Containerfile`.
* Directories `ananke-base-hub` and `ananke-nbgrader-hub` contain everything you need to run an Ananke container (without or with nbgrader).
* They contain config files as well as subdirectories holding data generated during container runtime.

If you want to run more than one Ananke container, each container needs a separate copy of the relevant directory (`ananke-base-hub` or `ananke-nbgrader-hub`).

### Basic Podman commands

Podman provides several (sub-)commands to manage images and containers.
To see all currently installed images, run
```
podman image ls
```
To remove an image run
```
podman rmi image_label_or_id
```
With
```
podman ps
podman ps --all
```
we get a list of currently running containers or of all containers on the system, respectively.
To stop a currently running container run
```
podman stop container_label_or_id
```
Then either remove the container with
```
podman rm container_label_or_id
```
or continue its execution with
```
podman restart container_label_or_id
```

```{important}
Above Podman commands are rarely needed for Ananke images and containers because Ananke ships with several shell scripts for standard procedures like image building, running a container, or removing a container.
See instructions below.
```

### Install and run the container

To get an Ananke container running proceed as follows (instructions are for Ananke without nbgrader, replace `base` by `nbgrader` wherever it appears to get Ananke with nbgrader):

1. Copy all Ananke files to your `home` directory on the host machine. See [File Transfer](#file-transfer) for details.
2. Build the image by running
   ```
   cd ~/ananke/images/ananke-base
   ./build.sh
   ```
   **on the host machine** (see [SSH login to host machine](#ssh-login-to-host-machine)). Alternative: if you obtained a tar file containing the image, run
   ```
   podman load -i filename.tar
   ```
3. Get your JupyterHub's port from your host admin and replace `PORT=8000` in `ananke-base-hub/run.sh` by `PORT=your_port`.
4. Get your JupyterHub's name (last part of URL) from your host admin and write it to `ananke-base-hub/runtime/jupyterhub_config.d/00_base.py`:
   ```
   c.JupyterHub.base_url = 'your_hub_name/'
   ```
5. Run
   ```
   cd ~/ananke/ananke-base-hub
   ./run.sh
   ```

Now the JupyterHub is running, and you should at least get some message produced by JupyterHub when visiting `https://your-domain.org/your_hub_name`.
You have to access JupyterHub via some LTI platform (Moodle aso.).
**Direct login won't work.** LTI configuration will be described below: [LTI configuration](#lti-configuration).

(root-access-to-the-container)=
### Root access to the container

To work inside the container (checking the logs, for instance) run
```
cd ~/ananke/ananke-base-hub
./shell.sh
```
This opens a shell inside the container.
There you are the container's root user.

### Remove the container

To remove a Podman container created by `run.sh` use `remove.sh`.

```{important}
If you remove a container all modifications to files inside the container will be lost.
Some exceptions for Ananke based containers will be discussed below.
```

## Container configuration options

(lti-configuration)=
### LTI configuration

LTI communication between JupyterHub and your learning management system (LMS) has to be configured on both sides.

#### JupyterHub

On hub side LTI configuration is in `runtime/jupyterhub_config.d/30_lms.py`.
Rename `30_lms.py.template` to `30_lms.py` and write the URLs provided by your LMS to corresponding lines.

```{important}
Note that the value for `c.LTI13Authenticator.client_id` has to be a list of strings even if only one client ID is present.
```

Don't abuse `30_lms.py` for other configuration purposes than the described LTI configuration.
This may lead to unexpected behavior.

#### LMS

For your LMS you need the following configuration information (field names are taken from Moodle here and may be slightly different in other LMS):
* tool URL: `https://your-domain.org/your_hub_name/`
* public key type: `Keyset URL`
* public keyset: `https://your-domain.org/your_hub_name/services/kore/jwks`
* initiate login URL: `https://your-domain.org/your_hub_name/hub/lti13/oauth_login`
* redirection URI(s): `https://your-domain.org/your_hub_name/hub/lti13/oauth_callback`
* default launch container: `Existing window`

```{important}
For security reasons JupyterHub does not allow to be embedded into another website.
Thus, in Moodle only `Existing window` works.
Even `new window` is not possible due to it's implementation in Moodle via embedding techniques.
```

### Hub admins

To give a hub user admin privileges inside the hub (see [here](hub-admins.md)), get the user's username (from URL `.../user/USERNAME/...` when user visits the hub) and write it to `runtime/jupyterhub_config.d/20_users.py` (rename `20_users.py.template`):
```
c.Authenticator.admin_users.add('hub_admin_user_id')
```

If there is more than one hub admin, use one such line per hub admin.

### User server behavior

In `runtime/jupyterhub_config.d/10_servers.py` you may modify JupyterHub's behavior concerning single user's JupyterLabs.

### Restarting the hub

Configuration changes require restarting JupyterHub to take effect.
Restarting the hub does not kill user's JupyterLabs.
Thus, the hub can be restarted whenever necessary.
Only users currently logging in may experience problems.

To restart the hub run
```
systemctl restart jupyterhub
```
**inside the container** (see [Root access to the container](#root-access-to-the-container)).

## Backups

Hub user's home directories and the hub's configuration are accessible from outside the container.
To back up home directories and configuration, simply make a copy of the `runtime` directory.

Example backup procedure:
1. Log in to the host machine via SSH (see [SSH login to host machine](#ssh-login-to-host-machine)).
2. Go to the container's directory:
   ```
   cd ananke-base-hub
   ```
3. Copy all relevant files to a tar archive:
   ```
   tar czfv backup.tar.gz ./runtime
   ```
   (some files aren't readable, but those files only contain runtime information from Jupyter and can be safely ignored).
4. Move the tar archive to some save place (see [File Transfer](#file-transfer)).


## Modify global Python environment

There are two default Python environments: `jhub` (contains all the Jupyter stuff, do not modify), `python3` (the environment in which notebooks run, install all required packages here): inside the container's root shell (see [Root access to the container](#root-access-to-the-container)) run
```
conda install package_name
```

```{important}
Modification of Python environment is done inside the container.
Replacing the container by a new one (even from the same image) resets the Python environment.
```

## Additional global Python environments

In the container's root shell, run
```
conda create -y --name NAME_OF_NEW_ENV
```
Then
```
conda activate NAME_OF_NEW_ENV
conda install -y ipykernel
python -m ipykernel install --name INTERNAL_NAME_OF_KERNEL --display-name "DISPLAYED NAME OF KERNEL"
```

New environment and kernel are available to all users immediately without restarting the hub or a user's lab.

```{important}
Creation of additional global Python environment is done inside the container.
Replacing the container by a new one (even from the same image) removes all additional Python environments.
```

## Log files

To see the container's log files, run
```
journalctl -r
```
inside the container.
The `-r` option shows the newest messages first.

There's also a list of all users having visited the hub via LTI.
It's a JSON file with hub username, first name, last name, email, LMS username.
It's at `/opt/userdata.json`.

## Resource limits

To see resource limits of the containern, run
```
cat /sys/fs/cgroup/cpu.max
cat /sys/fs/cgroup/memory.max
```
in the container's root shell.

You may modify the container's resource limits by editing `run.sh` (the script used for starting a container).
The argument `-m=8g` limits available memory (8 GB).
There are arguments for limiting CPU usage, too.
See [Podman documentation](https://docs.podman.io/en/latest/markdown/podman-run.1.html).

Per user resource limits can be configured in `runtime/jupyterhub_config.d/10_servers.py`.

## Updates

You should update your JupyterHub container regularly.

### Updates inside container

You may run standard update commands in the container's root shell:
```
apt update
apt upgrade
```
Update your Python environments, too:
```
conda update --all
```

### Update the whole container

Alternatively, you may get the newest Ananke files and rebuild image and container.
Rebuilding the image will install most current versions of all components.

Remember to back up your user's home directories and modifications you made to the container (Python environments, ...).

## Useful optional features

### Base packages

To install [NumPy](https://numpy.org/), [Pandas](https://pandas.pydata.org/), [Matplotlib](https://matplotlib.org/), [Seaborn](https://seaborn.pydata.org/), [Plotly](https://plotly.com/python/) run `/opt/install/base.sh` in the container's root shell.

You have to restart all user servers to make Matplotlib and Plotly work.

To get interactive Matplotlib output use the cell magic `%matplotlib widget`. To deactivate interactive output use `%matplotlib inline`.

### MyST markdown rendering

To make JupyterLab render [MyST markdown](https://mystmd.org/) run `/opt/install/myst.sh` in the container's root shell and restart all user servers.

### WebDAV and other file systems

The JupyterLab extension [jupyter-fs](https://github.com/jpmorganchase/jupyter-fs) allows adding additional file managers based on a wide range of file systems, including WebDAV.
WebDAV provides access to Nextcloud accounts, for instance.

To install jupyter-fs run `/opt/install/jupyterfs.sh` in the container's root shell and restart all user servers.

```{note}
Files cannot be copied or moved between jupyterfs file browsers and JupyterLab's standard file browser. Thus, the install script will add a jupyterfs file browser to all users' JupyterLabs showing a user's home directory. To copy/move files from a user-defined WebDAV or other source the files have to be pasted in the jupyterfs home file browser, not in the standard file browser.
```

To add further default file browsers for all users edit `/opt/conda/envs/jhub/etc/jupyter/jupyter_server_config.py`.

See [File transfer for hub users](hub-users.md#file-transfer) for configuration of user-defined file systems.

### Shared directories

If your hub users need to share files, either because you don't want them to upload and store identical copies of large data sets to their home directories or your users, want to send files to other users, you can set this up as follows:

Create a directory `data` somewhere in your home directory on the host machine.
Create a `datasets` subdirectory with read permission for all users and a `share` subdirectory with write permission for all users.
```
cd ~
mkdir container-data
chmod a+rx container-data
cd container-data
mkdir datasets
chmod a+rx datasets
mkdir share
chmod a+rwx share
```
Mount this directory into the container by appending
```
--mount=type=bind,source=../container-data,destination=/data
```
in the container's `run.sh`.
```{note}
After modifying `run.sh` you have to recreate your container if it already exists, that is, stop the container, remove it, and then run `run.sh`.
At the time of writing (July 2023) Podman does not support adding mounts to running containers.
```

Make the `share` directory writable inside the container by adding
```
c.SystemdSpawner.readwrite_paths.append('/data/share')
```
to your container's `runtime/jupyterhub_config.d/10_servers.py`.
Then restart JupyterHub with `systemctl restart jupyterhub`.

If you use jupyter-fs, you may add a file browser for the `data` directory to all users' JupyterLabs.
Simply add
```
c.Jupyterfs.resources = [
    {
        'name': 'data',
        'url': 'osfs:///data/'
    },
]
```
to `/opt/conda/envs/jhub/etc/jupyter/jupyter_server_config.py`.

### JupyterLab real-time collaboration

The [`jupyterlab-collaboration`](https://github.com/jupyterlab/jupyter-collaboration) extension provides real-time collaboration for working with notebooks.
Several users share one JupyterLab session and instantly see other user's edits and cell execution results.

#### Install

Install the collaboration extension by running `/opt/install/rtc.sh` in the container's root shell.

Rename the template `08_rtc.py.template` in `runtime/jupyterhub_config.d/` (in your container's working directory on the host machine) to `80_rtc.py` and define your public and private collaboration rooms in that file.

Then restart the hub with `systemctl restart jupyterhub`.

````{note}
For each collaboration room there is a user account inside the container. All files created during collaboration sessions are stored in `/home/name-of-room` inside the container. To simplify backup of files from collaboration sessions you may want to make the container's `home` directory available outside the container. For this purpose add
```
--mount=type=bind,source=runtime/home,destination=/home \
```
to your container's `run.sh` script. This is only necessary for Ankane base image. Ananke nbgrader image already has this line.
````

```{note}
The collaboration extension is disabled by default for all hub users. But users may enable the extension on their own. See [JupyterLab RTC for hub users](hub-users.md#jupyterlab-real-time-collaboration).
```

#### Usage

Usage of the collaboration feature is described in [JupyterLab RTC for hub users](hub-users.md#jupyterlab-real-time-collaboration).

#### Remove a collaboration room

To remove a collaboration room modify `80_rtc.py`, and remove the room's user account inside the container: `userdel rtc-ROOM-NAME`.
This does not remove any files create during corresponding collaboration sessions. To remove files, too, either use `userdel -r rtc-ROOM-NAME` instead or remove `/home/rtc-ROOM-NAME` manually.

### Language server protocols (LSP)

LSP support allows for code completion, automatic code formatting and several other useful features. To install LSP support for JupyterLab run `/opt/install/lsp.sh` in the container's root shell and restart the hub as well as all user servers.

### TensorFlow with GPU support

If the host machine has got one or more GPUs and Podman is configured to provide GPU access inside containers, then TensorFlow should be installed with GPU support. Have a look at [GPU support](host-admins.md#gpu-support) in the documentation for host admins and/or ask your host admin for details on GPU availability.

#### Test Podman GPU support

If GPU support for Podman is available on your host machine, add the line
```
--device nvidia.com/gpu=all \
```
below `podman create` in your container's `run.sh`.
In the container's root shell run `nvidia-smi` to see whether and how many GPUs are available inside the container.

#### Install Tensorflow

To install TensorFlow run `/opt/install/tensorflow.sh` in the container's root shell. Note that this will downgrade Python to version 3.10 to resolve package conflicts.

The install script also runs some TensorFlow commands to test the installation. Carefully check the output for errors.

#### Assign GPUs to users

Every hub user has access to all GPUs. How to confine a user's TensorFlow commands to a subset of GPUs is described in [TensorFlow and GPUs](hub-users.md#tensorflow-and-gpus).
