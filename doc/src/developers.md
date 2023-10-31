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

Starting with 0.3 Ananke uses [`nb_conda_kernels`](https://github.com/Anaconda-Platform/nb_conda_kernels) to make IPython kernels from different conda environments available in Jupyter. The advantage compared to usual kernel management via `ipykernel install` is that kernels installed by `nb_conda_kernels` automatically run `conda activate` at start-up. This is necessary for some packages (TensorFlow, Plotly) to have access to relevant environment variables. With standard kernel management there is no `conda activate` at start-up.

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

For local testing, one may use Moodle in a Podman container and Ananke containers directly, without a reverse proxy.

To get network communication between containers running don't use `localhost` or `127.0.0.1`, because `localhost` inside a container refers to the container's `localhost`.
Instead, create a new IP address (outside any container) for `localhost` and use only this new address:
```
sudo ip addr add 192.168.178.28 dev lo
```
This address will be removed on reboot
To remove it manually run
```
sudo ip addr del 192.168.178.28 dev lo
```
```{important}
Rootless (that is, run by an unprivileged user) Podman containers do not have an IP address.
Communication with the container has to use Podman's port forwarding.
```
Moodle then is at `192.168.178.28:9090` and JupyterHub is at `192.168.178.28:8000`, for instance.

Where to place the new IP address:
* in `docker-compose.yaml` of Moodle image (`MOODLE_DOMAIN: 192.168.178.28` twice),
* in `/opt/moodle_docker/moodle/config.php` (`$CFG->wwwroot = 'http://192.168.178.28:9090';`),
* in tool's and platform's LTI configuration URLs (`192.168.178.28:9090` or `192.168.178.28:8000`).

In `docker-compose.yaml` the `port` argument for nginx should be `0.0.0.0:9090:80`.
This directs all requests coming in via port 9090 to nginx in the container, independently of the IP address (even `localhost` should work).

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

If the user's lab is running (and the lab may run even if the user is logged out) and we want to run a command within the user's home directory (to alter the user's Jupyter configuration, for instance), we have to remember and then reset original ownership. Both commands (lab and some config command) run as different dynamic users with identical home directory. The command issued last (config command) determines ownership of a user's home and may prevent the longer running command (lab) from accessing user's files! Lab having no (write) access to files in home makes files non-editable for the user in the lab session.

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
