# For developers

This chapter collects technical background information relevant to developers.
It's not intended to be a complete description of the system (although that would be nice), but highlights very specific aspects only.

```{contents}
---
local: true
---
```

## Building the documentation

Ananke's documentation uses the [Sphinx Python Documentation Generator](https://www.sphinx-doc.org) with [MyST markdown](https://mystmd.org/) and the [Sphinx book theme](https://sphinx-book-theme.readthedocs.io).

Install with conda:
```
conda install sphinx myst-parser sphinx-book-theme
```

Build documentation:
```
cd doc/src
./make_html.sh
```

View documentation:
```
cd doc/html
firefox index.html
```

## Deployment models

If providing Ananke-based JupyterHubs, one has to decide what kind of deployment model to use:
* *fully managed*: host admin is identical to container admin (no installation or config work for instructors, instructor cannot modify global Python environment)
* *managed host*: host admin is different from container admin (instructor is container admin, a good model for experienced JupyterHub admins with some need for individual/direct configuration including modifications to the global Python environment)
* *fully self-managed*: user sets up its own host machine along the lines of the Ananke project (good for people with special performance needs like GPU servers)

## User management

There is no root or sudo user inside an Ananke container.
Modifications to containers have to be implemented by the container admin, which is a regular user on the host machine.

Inside a container, users are generated dynamically via systemd's [dynamic users](https://0pointer.net/blog/dynamic-users-with-systemd.html) feature.
Home directories of dynamic users are persistent.
Thus, hub users shouldn't recognize that their accounts are created dynamically.

Container admins are unprivileged users on the host system.
Thus, they should not have access to another container admin's containers.

## Conda environments

Starting with 0.3 Ananke uses [`nb_conda_kernels`](https://github.com/Anaconda-Platform/nb_conda_kernels) to make IPython kernels from different conda environments available in Jupyter.
The advantage compared to usual kernel management via `ipykernel install` is that kernels installed by `nb_conda_kernels` automatically run `conda activate` at start-up.
This is necessary for some packages (TensorFlow, Plotly) to have access to relevant environment variables.
With standard kernel management there is no `conda activate` at start-up.

## Kore for LTI related features

Ananke adds LTI capabilities to JupyterHub and Nbgrader. Two components are involved:
* The *Kore service* running as a JupyterHub service provides a REST API for LTI functions. Before Ananke 0.5 this serivce also provided a GUI for course and grades management.
* The *Kore lab extension* provides a GUI in JupyterLab for course and grades management starting with Ananke 0.5.

Note that there is no Jupyter Server extension involved, because LTI functions heavily interact with the authentication process. Thus, they have to be implemented globally for the whole JupyterHub.

## Container structure

### `systemd`
Ananke's Podman containers run `systemd` as the main process.
JupyterHub then is a `systemd` service and JupyterHub uses `systemdspawner` for running hub users' JupyterLabs.
This setup requires Linux with 'cgroups v2' and `systemd` on the host system (Debian, Ubuntu and most others).
Remember that containers are not virtual machines! All containers and the host machine share one and the same Linux kernel.

### Boot script

Each Ananke image comes with a script `assets/boot.sh` which is run at container boot time.

### Nbgrader exchange directory

The exchange directory for nbgrader inside a container is `/opt/nbgrader_exchange`.
It cannot be in `/home` because dynamic users have no access to `/home` (the home path is mapped to dynamic user's home path in `/var`).

## Local testing with LMS

The Ananke project ships with a Podman image for Moodle.
```{warning}
The Moodle Podman image is for local testing only.
Never (!!!) use it on an internet facing server.
It's by no means secure!
```

### Workflow

The following list shall guide you through the proper setup.
See the corresponding sections of individual steps.

* Build both images with the corresponding `build.sh` scripts as needed.
* Adjust host configuration, see [Networking configuration](#networking-configuration).
* Start and configure Moodle, see [First start of Moodle](#first-start-of-moodle).
* Prepare `External Tool`, see [LTI tool configuration (Moodle)](#lti-tool-configuration-moodle).
* Change LTI tool visibility (tick `Show in activity chooser` at course view > `More` > `LTI External tools`).
* Follow [Example Ananke configuration for local testing with Moodle](#example-ananke-configuration-for-local-testing-with-moodle).
* Start Ananke container with `run.sh`.


(networking-configuration)=
### Networking configuration

For local testing, you have to run both Podman containers, Moodle and Ananke.
No reverse proxy is required.
To get network communication between containers running don't use `localhost` or `127.0.0.1`, because `localhost` inside a container refers to the container's `localhost`.
Instead, create a new IP address (outside any container) for `localhost` and use only this new address:
```
sudo ip addr add 192.168.178.28 dev lo
```
This address will be removed on reboot.
To remove it manually, run
```
sudo ip addr del 192.168.178.28 dev lo
```
```{important}
Rootless (that is, run by an unprivileged user) Podman containers do not have an IP address.
Communication with the container has to use Podman's port forwarding.
```
Moodle then is at `192.168.178.28:9090` and JupyterHub is at `192.168.178.28:8000`, for instance.
Ports are specified in `config.sh` and `run.sh` scripts for Ananke and Moodle respectively.

If the host machine is using SELinux run `sudo setenforce Permissive` otherwise there will be permission errors.

(first-start-of-moodle)=
### First start of Moodle

Start the Moodle container with `run.sh`.
Then enter the container's shell with `shell.sh` und run `/opt/init_moodle.sh`.
This creates the Moodle database and basic Moodle configuration.
The script will ask you for your Moodle container's URL.
With the above network configuration use `http://192.168.178.28:9090`.

In your webbrowser open `http://192.168.178.28:9090/moodle`.
Log in as user `admin` with password `Admin123.`.
Answer all questions asked.
Even though the email addresses have to be entered, they serve no purpose because mail is not configured and so the addresses may be selected at will.
The `admin` user is the only exiting user.
You may add other users for testing.
```{important}
Although the container is running at `http://192.168.178.28:9090` Moodle's URL is `http://192.168.178.28:9090/moodle`.
```

### Moodle security settings

Moodle has a black list for hosts and a white list for hosts.
Moodle only sends requests to URLs matching both lists.
This is especially important for LTI communication in test environments with non-standard ports and requests to `localhost` and friends.
For instance, hosts `192.168.*.*` are black listed by default.

Log in to Moodle as `admin`.
Go to 'Site Administration', 'General', 'Security', 'HTTP Security'.
Remove your IP pattern from the hosts black list and add your JupyterHub port to the ports white list.

(lti-tool-configuration-moodle)=
### LTI tool configuration (Moodle)

To access the JupyterHub in the Moodle course context, it must be configured as an external tool.
This may be done at `Site administration` > `Plugins` > `Manage tools` > `configure a tool manually`.

Tool settings:
* `Tool URL` - URL of the `JupyterHub` as described above.
* `LTI version` - LTI 1.3
* `Public key type` - Keyset URL
* `Public keyset` - `http://192.168.178.28:8000/services/kore/jwks` (alter base URL as needed)
* `Initiate login URL` - `http://192.168.178.28:8000/hub/lti13/oauth_login` (alter base URL as needed)
* `Redirection URI(s)` - `http://192.168.178.28:8000/hub/lti13/oauth_callback` (alter base URL as needed)
* `Default launch container` - New window

### Persistent data

All data created by Moodle at runtime (users, courses, grades, ...) will be stored in `test-moodle/runtime` on the host machine.
If you destroy the container und start a fresh one, everything will still be available to the new container.
Running `init_moodle.sh` again is NOT required and may result in errors and corrupted data.

To get rid of Moodle's data and start with a fresh Moodle installation, delete the contents of `test-moodle/runtime/moodle_data` and `test-moodle/runtime/mariadb_data` before you create the container.

(example-ananke-configuration-for-local-testing-with-moodle)=
### Example Ananke configuration for local testing with Moodle

Before starting the container of Ananke make sure to add / alter the `20_users.py` and `30_lms.py` files.
Exemplary configurations may look like:

```python
# 20_users.py

c = get_config()  # noqa

# username(s) of hub admin(s)
# (login to the hub and look at the URL to get your username)
c.Authenticator.admin_users.add('u123')
```

and

```python
# 30_lms.py

c = get_config()  # noqa

# configuration data provided by your LMS
base_url = 'http://192.168.178.28:9090/moodle'
c.LTI13Authenticator.client_id = ['SomeRandomString']
c.LTI13Authenticator.issuer = base_url
c.LTI13Authenticator.authorize_url = f'{base_url}/mod/lti/auth.php'
c.LTI13Authenticator.jwks_endpoint = f'{base_url}/mod/lti/certs.php'
c.LTI13Authenticator.access_token_url = f'{base_url}/mod/lti/token.php'
```

Here are some notes to fill in the correct values:
* `admin_users` - The ID may be extracted from Moodle's URL. The URL might look something like this: yoursite.com/user/profile.php?id=123, where "123" is your user ID. Remember to prefix the ID with the letter 'u'.
* All values for `30_lms.py` may be seen within the `Tool configuration details`. These are available from the list symbol (left to the cog symbol) of the tool (`Site administration` > `Plugins` > `Manage tools`).

## Arguments to `podman run`

Some special arguments used in `run.sh`:
* `-p 8000:8000` makes port 8000 (right one) inside the container available as port 8000 (left one) outside.
* `--cap-add SYS_ADMIN` allows the container to create dynamic systemd users.
* `--mount=type=bind,source=runtime/dyn_home,destination=/var/lib/private` mounts the host machines `runtime/dyn_home` to the container's `/var/lib/private` making dynamic users' home directories persist container rebuilds and restarts.
* `-m=8g` limits memory usage of the container to 8 GB.

(why-podman)=
## Why Podman?

[Podman](https://podman.io/) is an alternative to [Docker](https://www.docker.com/) providing almost identical command line interface.
In contrast to Docker Podman integrates more tightly with some modern Linux features used by the Ananke project (allowing for [systemd](https://en.wikipedia.org/wiki/Systemd) in containers, for instance) and provides a higher level of security (containers run as non-root user).
Here is a list of Podman's advantages:
* Containers run unprivileged and may be managed and started by unprivileged users. Docker requires root privileges or heavy tweaking.
* `systemd` inside containers is supported, whereas Docker requires heavy tweaking to get `systemd` running.
* Podman is a usual program, not a daemon, whereas Docker wants to run permanently in the background (with root permissions) even if there are no containers to run.
* Podman's CLI is compatible with Docker's CLI. Thus, nothing new to learn.
* Podman is available in almost all Linux distributions.

## Podman install hints

If you experience problems with Podman, your SELinux configuration may be a possible cause.
You may check your current mode with `sestatus | grep "Current mode"`.
If the mode is set to 'enforcing' change it temporarily with the command `sudo setenforce Permissive`.
The changes won't persist between reboots.

In some Linux distributions, relevant packages seem to be not installed properly.
If Podman throws errors try to install packages `runc` and `crun` manually.

## Dynamic user details

If `systemd` runs a command as dynamic user it takes the (possibly existing) state directory (dynamic user's home) and recursively sets its ownership to the dynamically created uid:gid value.

If the user's lab is running (and the lab may run even if the user is logged out) and we want to run a command within the user's home directory (to alter the user's Jupyter configuration, for instance), we have to remember and then reset original ownership.
Both commands (lab and some config command) run as different dynamic users with identical home directory.
The command issued last (config command) determines ownership of a user's home and may prevent the longer running command (lab) from accessing user's files! Lab having no (write) access to files in home makes files non-editable for the user in the lab session.

See [Dynamic Users with systemd](https://0pointer.net/blog/dynamic-users-with-systemd.html) for more details.

## Release

Steps for new Ananke release:

1. Disable debug mode if necessary:
   * `images/ananke-base/assets/jupyterhub_config.py`
   * `images/ananke-nbgrader/assets/kore/kore.py`
   * `images/ananke-nbgrader/assets/kore/kore_jhub_config.py` (two times)
   * `ananke-base-hub/runtime/jupyterhub_config.d/00_base.py`
   * `ananke-nbgrader-hub/runtime/jupyterhub_config.d/00_base.py`
2. Disable output of LTI state on Kore home page if necessary:
   * `images/ananke-nbgrader/assets/kore/templates/home.html.jinja`
3. Update version string in doc (`doc/src/conf.py`) and render HTML.
4. Replace `next` heading in `CHANGELOG.md` by version number.
5. Merge `dev` branch into `main` branch.
6. Create release on GitHub.
7. Make image tar files:
   * `podman save -o ananke-base.tar ananke-base`
   * `gzip -9 ananke-base.tar`
   * `podman save -o ananke-nbgrader.tar ananke-nbgrader`
   * `gzip -9 ananke-nbgrader.tar`
8. Upload tar files to webserver.
9. Upload HTML doc to webserver.

## Links

- [Reference implementation test tool](https://lti-ri.imsglobal.org) from IMS global
- [LTI bootcamp](https://ltibootcamp.theedtech.dev) utilizing a Flask server and Jupyter Notebook as tool
- [YouTube channel from Claude Vervoort](https://www.youtube.com/channel/UCKcdpZMUQj5kU4TssE8Q1Jg) with explanation and example videos
- [Google group thread](https://groups.google.com/g/jupyter-education/c/axpnAbNbq6I) for LMS integration and JupyterHub
- [Nbgrader LTI Export Plugin](https://github.com/huwf/nbgrader-export-plugin)
- [saltire](https://saltire.lti.app/) LTI tool and platform for testing without restrictions (more features than IMS global)
