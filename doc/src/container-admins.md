# For container admins 

Container admins have a regular user account on the host machine.
They may access the host machine via SSH to install, configure, start and stop the Podman container running the JupyterHub.

```{contents}
---
local: true
backlinks: none
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

Ananke uses [Podman](https://podman.io) containers for deployment.

### Introduction to images and containers

An *image* is a blueprint for containers.
A *container* is similar to a virtual machine.
Its purpose is to run a program in isolation from other programs on the machine.
From one image, one may create one or more containers.

Images are built from image definitions consisting of
* a `Containerfile` containing image building instructions for Podman,
* assets (files to copy to the image).

Ananke's image definitions are in `ananke/images`.

Containers are built from images. Ananke containers require several config files and directories for storing runtime data. These files and directories are referred to as *container definition* and reside in `ananke/containers`.

Currently, Ananke provides two images:
* `ananke-base` for JupyerHub without additional assessment tools,
* `ananke-nbgrader` for JupyterHub with nbgrader.

If you want to run more than one Ananke container, that is, if you want to run several JupyterHubs, each container needs a separate container definition (subdirectory of `ananke/containers`).

### Introduction to Podman

```{note}
You may skip this section, because under normal circumstances you won't have to use Podman directly.
```

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

(install)=
### Install and run a container

To get an Ananke container running proceed as follows (instructions are for Ananke without nbgrader, replace `base` by `nbgrader` wherever it appears to get Ananke with nbgrader):

#### Step 1: Get Ananke files

There are two alternatives to get Ananke

**Alternative 1:** Download Ananke's [zipped GitHub repository](https://github.com/jeflem/ananke/archive/refs/heads/main.zip) and unzip it to your home directory on the host machine. On the host machine:
```
cd ~
wget https://github.com/jeflem/ananke/archive/refs/heads/main.zip
unzip main.zip
mv ananke-main ananke
```

**Alternative 2:** Clone Ananke's GitHub repository. On the host machine:
```
cd ~
git clone https://github.com/jeflem/ananke.git
```

Then you should have a directory named `ananke` in your home directory.

#### Step 2: Get an Ananke image

There are two alternatives to get an Ananke image.

**Alternative 1** (faster): Run
```
cd ~/ananke
./ananke load
```
This asks for an image to load and then downloads the image file from [Ananke website](https://gauss.whz.de/ananke).

**Alternative 2** (customizable): Run
```
cd ~/ananke
./ananke build
```
This asks for an image definition and then builds a new image from that definition.
```{note}
If you want to build the `ananke-nbgrader` image, you first have to build `ananke-base`, because `ananke-nbgrader` is built on top of `ananke-base`.
```

#### Step 3: Choose container definition template

In `ananke/containers` there are several subdirectories starting with `template-`. Check each templates `readme.md` and decide for the most suitable one. Then copy the template (here we go with `template-base`):
```
cd ~/ananke/containers
cp -R template-base my-hub
```

#### Step 4: Adjust container configuration

Open your container definition's `config.py` in a text editor:
```
nano ~/ananke/containers/my-hub/config.py
```
Adjust settings as needed. In most cases the `port` has to be set to a value provided to you by your host machine's admin.

If you plan to mount external data directories to the container, do it now. Mounting directories to running containers is not supported by Podman. See [Shared directories](#shared-directories) for more details.

If you plan to use NVIDIA GPUs inside the container, set the `required` option as described in [Tensorflow with GPU support](#tensorflow-gpu).

#### Step 5: Adjust JupyterHub configuration

JupyterHub configuration files are in `ananke/containers/my-hub/jupyterhubc_conf.d`. Settings may be changed during container runtime, too. But some settings are required for successful start-up.

In `00_base.py` set `c.JupyterHub.base_url` to the value provided by your host machine's admin.

Configure communication with your learning management system (LMS) in `30_lms.py`. See [LTI configuration](#lti-configuration) for details.

#### Step 6: Create and start the container
 Now it's time to start the container:
```
cd ~/ananke
./ananke create
```
Select the container definition to use and answer all questions.

If you go to  `https://your-domain.org/your_hub_name` with your web browser, you should see some message that login requires LTI. Direct login without LMS is not possible!

#### Step 7: (Almost) done

Configure your LMS, see [LTI configuration](#lti-configuration) for details. Then go to JupyterHub via your LMS.

If something isn't working properly, open a root shell inside the container:
```
cd ~/ananke
./ananke-my-hub.sh
```
In the root shell type
```
journalctl
```
to see the logs.

#### Step 8: Optional features

You may install some or all optional features provided my Ananke. See [Useful optional features](#optional-features) for details.

(root-shell)=
### Root access to a container

For each container created with `ananke create` there is a shell script `ananke-container-name.sh` starting a root shell inside the container:
```
cd ~/ananke
./ananke-my-hub.sh
```
This opens a shell inside the container. There you are the container's root user. You may check the logs (`journalctl`) or install additional software.

The hub users home directories are in `/var/lib/private` inside the container.

### Remove a container

To remove an Ananke container run
```
cd ~/ananke
./ananke remove
```
Choose the container to remove.

Files living in volumes mounted to the container (everything you see in `ananke/containers/my-hub`) won't be removed. During the removal procedure you'll be asked whether ownership of those file shall be transfered to you. Without transfering ownership you may have problems deleting files because you do not have sufficient permissions. Do NOT transfer ownership if you plan to reuse the volumes in a new container!

```{important}
If you remove a container, all modifications to files inside the container not living in a mounted volume will be lost.
```

## JupyterHub configuration options

Behavior of JupyterHub can be adjusted in `ananke/containers/my-hub/jupyterhub_config.d`. After modifying files there, you have to restart the hub: [open a root shell](#root-shell) and run
```
systemctl restart jupyterhub
```
Restarting the hub does not kill user's JupyterLabs.
Thus, the hub can be restarted whenever necessary.
Only users currently active users may experience [cumbersome error messages](#cumbersome-errors) for some seconds.

(lti-configuration)=
### LTI configuration

LTI communication between JupyterHub and your learning management system (LMS) has to be configured on both sides.

#### JupyterHub

On hub side LTI configuration is in `ananke/containers/my-hub/jupyterhub_config.d/30_lms.py`. Write the URLs provided by your LMS to corresponding lines.

```{important}
Note that the value for `c.LTI13Authenticator.client_id` has to be a list of strings even if only one client ID is present.
```

Don't abuse `30_lms.py` for other configuration purposes than the described LTI configuration.
This may lead to unexpected behavior.

(lti-lms)=
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

#### HTTPS with enterprise root CA or self-signed cert

If JupyterHub shall connect to your LMS via HTTPS with a cert issued by an enterprise root CA, you have to install the CA's root cert in the Ananke container:
1. On the host machine copy the cert file to your container's `jupyterhub_config.d` directory.
2. In the container's root shell run
   ```
   mv /opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_config.d/YOUR_CERT_FILE /usr/local/share/ca-certificates/
   update-ca-certificates
   ```
3. Check that the output contains `1 added`.

```{important}
JupyterHub refuses to connect to servers via HTTPS if the cert is self-signed. Thus, if you want or have to use a self-signed cert for your LMS, you have to create a custom root CA and issue your own certs with that CA. See [documentation for developers](developers.md), where the process of creating a custom CA and issuing certs is described for setting up the development environment.
```

### Hub admins

To give a hub user admin privileges inside the hub (see [For hub admins](hub-admins.md)), get the user's username (from URL `.../user/USERNAME/...` when user visits the hub) and write it to `ananke/containers/my-hub/jupyterhub_config.d/20_users.py`:
```
c.Authenticator.admin_users.add('hub_admin_user_id')
```

If there are more than one hub admin, use one such line per hub admin.

### User server behavior

In `ananke/containers/my-hub/jupyterhub_config.d/10_servers.py` you may modify JupyterHub's behavior concerning single user's JupyterLabs.

### Time zone

After start-up the container's time zone is set to `Europe/Berlin`. To modify the time zone run `timedatectl list-timezones` in the container's root shell and then set the time zone with `timedatectl set-timezone TIME_ZONE_FROM_LIST`.

(backups)=
## Backups

Hub user's home directories and the hub's configuration are accessible from outside the container.
To back up home directories and configuration, simply make a copy of the `ananke/containers/my-hub` directory.

Example backup procedure:
1. Log in to the host machine via SSH (see [SSH login to host machine](#ssh-login-to-host-machine)).
2. Go to the `containers` directory:
   ```
   cd ~/ananke/containers
   ```
3. Copy all relevant files to a tar archive:
   ```
   tar czfv backup.tar.gz ./my-hub
   ```
   (some files aren't readable, but those files only contain runtime information from Jupyter and can be safely ignored).
4. Move the tar archive to some save place (see [File Transfer](#file-transfer)).

## Modify global Python environment

There are two default Python environments: `jhub` (contains all the Jupyter stuff, do not modify), `python3` (the environment in which notebooks run, install all required packages here): inside the container's [root shell](#root-shell) run
```
conda install package_name
```

```{important}
Modification of Python environment is done inside the container.
Replacing the container by a new one (even from the same image) resets the Python environment.

Python environments live in `/opt/conda/envs` inside the container.
```

## Additional global Python environments

To create another conda environment for all users next to the default `python3` environment in the container's root shell proceed as follows:
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
   python -m nb_conda_kernels list --CondaKernelSpecManager.kernelspec_path='--sys-prefix' --CondaKernelSpecManager.env_filter=None
   ```

The new environment's kernel appears in all users' JupyterLabs after a few seconds without restarting the hub or user servers.

```{important}
Creation of an additional global Python environment is done inside the container.
Replacing the container by a new one (even from the same image) removes all additional Python environments.

Python environments live in `/opt/conda/envs` inside the container.
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

## Check resource limits

To see resource limits of the container, run
```
cat /sys/fs/cgroup/cpu.max
cat /sys/fs/cgroup/memory.max
```
in the container's root shell.

You may set a container's resource limits by editing `ananke/containers/my-hub/config.py` before (!) creating the container.

Per-user resource limits can be configured in `ananke/containers/my-hub/jupyterhub_config.d/10_servers.py`.

## Updates

You should update your JupyterHub container regularly.

### Updates inside container

You may run standard update commands in the container's root shell:
```
apt update
apt upgrade
```
Update your Python environments, too, by running
```
conda update --all
```
in each environment.

```{important}
Updating packages in the `jhub` environment may cause lots of troubles. Unexperienced users better do not touch this environment. To get newer versions of Jupyter components update the whole container (see below).
```

### Update the whole container

Alternatively to in-container updates yoyu may replace your container by a new one based on the latest Ananke release.

Remember to back up your user's home directories and modifications you made to the container (Python environments, ...).

(update-to-0_5)=
### Update from Ananke 0.4 to Ananke 0.5

Ananke 0.5 brings breaking changes in course handling for the Ananke nbgrader image and modified directory structure for both images base and nbgrader. Thus, update from Ananke 0.4 needs some extra attention.

All courses have to be recreated and container configuration files as well as hub user data have to be moved. We assume that you have following directory structure:
```
~/ananke/  --> copy of Ananke 0.4 repository
    ananke-nbgrader-hub/  --> the container to update
        runtime/  --> container configuration and data
    images/  ---> Ananke 0.4 image definitions
```
Proceed as follows:
1. Follow steps 1 and 2 of above [install instructions](#install), but name the base directory `ananke_0.5` instead of `ananke` (don't overwrite your Ananke 0.4 install).
2. (nbgrader only) Tell your instructor users to backup all their courses. Alternatively, [Backup](#backups) all courses of your hub.
3. Start a root shell in the old container with `shell.sh` and remove all directories in `/home` starting with `c-` (the courses).
4. Remove the old container with `remove.sh` from Ananke 0.4.
5. Rename the container directory from `ananke-nbgrader-hub` to `containers`.
6. Rename the runtime directory from `containers/runtime` to `containers/my-hub`.
7. Copy `config.py` from a `ananke_0.5/containers/templates-base_or_nbgrader` to `ananke/containers/my-hub`.
8. Adjust settings in `config.py` according to settings in former `run.sh`.
9. Copy all relevant files from `ananke_0.5` to `ananke`. These include `images` (replace old directory), `ananke` (the new management script), `containers/templates-*` (if you need them).
10. Start the new container with
 ```
cd ~/ananke
./ananke create
```
11. Tell your instructor users to log in to the hub from all their LMS courses. Then backup data can be copied to the new courses.

(optional-features)=
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
Files cannot be copied or moved between jupyter-fs file browsers and JupyterLab's standard file browser. Thus, the install script will add a jupyter-fs file browser to all users' JupyterLabs showing a user's home directory. To copy/move files from a user-defined WebDAV or other source the files have to be pasted in the jupyter-fs home file browser, not in the standard file browser.
```

To add further default file browsers for all users edit `/opt/conda/envs/jhub/etc/jupyter/jupyter_server_config.py`.

See [File transfer for hub users](hub-users.md#file-transfer) for configuration of user-defined file systems.

(shared-directories)=
### Shared directories

If your hub users need to share files, either because you don't want them to upload and store identical copies of large data sets to their home directories or your users want to send files to other users, you can set this up as follows:

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
config['volumes'].append(('/home/username/container-data', '/data'))
```
to the container definitions `config.py`.
```{important}
Do not use `~` in paths in `config['volumes']`. The `~` will not be resolved to the your home directory.
```
```{note}
After modifying `config.py` you have to recreate your container if it already exists, that is, run `./ananke remove` and then run `./ananke create` again.
At the time of writing (August 2024) Podman does not support adding mounts to running containers.
```

Make the `share` directory writable inside the container by adding
```
c.SystemdSpawner.readwrite_paths.append('/data/share')
```
to your container's `ananke/containers/my-hub/jupyterhub_config.d/10_servers.py`.
Then restart JupyterHub with `systemctl restart jupyterhub` in the container's root shell.

If you use jupyter-fs, you may add a file browser for the `data` directory to all users' JupyterLabs.
Simply add
```
    {
        'name': 'data',
        'url': 'osfs:///data/'
    },
```
to the block
```
c.Jupyterfs.resources = [
    ...
]
```
in `/opt/conda/envs/jhub/etc/jupyter/jupyter_server_config_jupyterfs.py`.

### JupyterLab real-time collaboration

The [`jupyterlab-collaboration`](https://github.com/jupyterlab/jupyter-collaboration) extension provides real-time collaboration for working with notebooks.
Several users share one JupyterLab session and instantly see other users' edits and cell execution results.

#### Install

Install the collaboration extension by running `/opt/install/rtc.sh` in the container's root shell.

Rename the `80_rtc.py.disabled` in `ananke/containers/my-hub/jupyterhub_config.d/` to `80_rtc.py` and define your public and private collaboration rooms in that file.

Then restart the hub with `systemctl restart jupyterhub`.

```{note}
For each collaboration room there is a user account inside the container. All files created during collaboration sessions are stored in `/home/rtc-name-of-room` inside the container.
```

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

(tensorflow-gpu)=
### TensorFlow with GPU support

If the host machine has got one or more GPUs and Podman is configured to provide GPU access inside containers, then TensorFlow should be installed with GPU support. Have a look at [GPU support](host-admins.md#gpu-support) in the documentation for host admins and/or ask your host admin for details on GPU availability.

#### Configuration

Ananke supports autoconfiguration of NVIDIA GPUs during container creation (if GPU support for Podman is available on your host machine). If no GPUs are found by the container creation procedure (either not NVIDIA or for other reasons), add a line
```
config['podman_args'].append('--device=YOUR_GPU_DEVICE_NAME')
```
to your container definition's `config.py`. Multiple such lines are possible, too, if you want to have access to multiple GPUs.

#### Test Podman GPU support

In the container's root shell run `nvidia-smi` to see whether and how many GPUs are available inside the container (NVIDIA only).

#### Install Tensorflow

To install TensorFlow run `/opt/install/tensorflow.sh` in the container's root shell.

The install script also runs some TensorFlow commands to test the installation. Carefully check the output for errors.

```{important}
TensorFlow 2.17 does not have NumPy 2 support. The install script will downgrade NumPy to 1.26.4!
```

#### Assign GPUs to users

Every hub user has access to all GPUs. How to confine a user's TensorFlow commands to a subset of GPUs is described in [TensorFlow and GPUs](hub-users.md#tensorflow-and-gpus).
