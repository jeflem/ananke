# For developers

This chapter collects technical background information relevant to developers.
It's not intended to be a complete description of the system (although that would be nice), but highlights very specific aspects only.

```{contents}
---
local: true
backlinks: none
---
```

## Development and testing

### Local testing with LMS

Ananke cannot be used without LMS, because JupyterHub's login process solely relies on LTI. You may use whatever LTI capable LMS is available to you for testing. But to facilitate local development and testing the Ananke project ships with a Podman image for [Moodle](https://moodle.org/). In this section we describe how to set up your network and a local Moodle instance for Ananke development.
```{warning}
The Moodle Podman image is for local testing only.
Never (!!!) use it on a public facing server.
It's by no means secure!
```

#### Overview

The following list shall guide you through the proper setup.
See the corresponding sections of individual steps.

* Adjust your development machine's networking configuration and install a reverse proxy, see [Networking configuration](#networking-configuration).
* Start and configure Moodle, see [First start of Moodle](#first-start-of-moodle).
* Build Ananke images, configure LTI for JupyterHub, and run a container, see [Start JupyterHub](#start-jupyterhub).

(networking-configuration)=
#### Networking configuration

For development you should have a local setup as close as possible to a production environment.
That is, LMS and JupyterHub should run on different domains (or IP addresses) and communication should run via HTTPS (not HTTP).
Else you won't see [CORS](https://en.wikipedia.org/wiki/Cross-origin_resource_sharing) related troubles and many other problems during development.

##### IP addresses

Create two additional IP addresses for `localhost`:
```
sudo ip addr add 192.168.178.28/32 dev lo scope host
sudo ip addr add 192.168.178.29/32 dev lo scope host
```
Ananke will use `192.168.178.28`. Moodle will be on `192.168.178.29`. So LMS and JupyterHub run on different domains.
You may choose other IP addresses depending on your overall network configuration.

```{note}
If the host machine is using SELinux run `sudo setenforce Permissive`. Otherwise there may be permission errors. Carefully check that this change does not impact your machine's security in an unacceptable manner!
```

```{warning}
Although those two additional IP addresses shouldn't have an effect on anything, side effects may occur for unknown reasons. The only side effect Ananke developers are currently aware of is that [MyST](https://mystmd.org/) rendering via `myst start` won't work if additional IP addresses are configured and (at the same time) the machine has no internet connectivity.
```

At any time you can remove IP addresses via
```
sudo ip addr del 192.168.178.28/32 dev lo
sudo ip addr del 192.168.178.29/32 dev lo
```

```{note}
Additional IP addresses will vanish at reboot. So after rebooting your machine you have to add them again.
```

##### Reverse proxy

Install [nginx](https://nginx.org/) as reverse proxy and HTTPS endpoint. See [Reverse proxy](#host-admins-reverse-proxy) in the host admins documentation for details.

Add following `location` blocks to the `server` block of nginx's site configuration:
```
        location /moodle/ {
                proxy_pass http://127.0.0.1:9090;
                proxy_redirect   off;
                proxy_set_header X-Real-IP $remote_addr;
                #proxy_set_header Host $host;  # Moodle fails with this line
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection $connection_upgrade;
        }

        location /dev-hub/ {
                proxy_pass http://127.0.0.1:8000;
                proxy_redirect   off;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header Host $host;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection $connection_upgrade;
        }
```

Then Moodle will be on `https://192.168.178.29/moodle` and JupyterHub will be on `https://192.168.178.28/dev-hub`. Note that both Moodle and JupyterHub are accessible via both IP addresses. But we will use `...29` for Moodle and `...28` for JupyterHub to have them on different domains.

##### Set up a root CA

In most cases the development machine won't have a server certificate issued by a commonly trusted [CA](https://en.wikipedia.org/wiki/Certificate_authority). Thus, to use HTTPS for testing you have to
* create your own root CA,
* add your root CA to your webbrowser and several other trust stores on your system,
* issue a server certificate,
* install the server certificate.

```{note}
Self-signed certs won't work, because JupyterHub (or Python packages it builds upon) does not trust them.
```

Create a private key and protect it by a password:
```
openssl genrsa -des3 -out myCA.key 2048
```
Then create the CA's cert valid for 5 years and signed with your private key:
```
openssl req -x509 -key myCA.key -sha256 -days 1825 -out myCA.pem -addext "keyUsage=critical,digitalSignature,keyCertSign,cRLSign"
```
Answer all questions somehow (empty or default values). Answers don't matter as long as you use your CA for local testing only. It's a good idea to choose a sensible common name. Else, you may have difficulties to find your cert in a list of many certs.

Now make your CA's cert known to your system's cert store. On Debian:
```
sudo cp myCA.pem /usr/local/share/ca-certificates/myCA.crt
sudo update-ca-certificates
```
You also have to add the cert to your browser's cert store, which for most browsers (at least Firefox and Chromium) is separate from your system's cert store. Firefox: Settings > Privacy & Security > Security > Certificates > View Certificates > Authorities > Import. Chromium: Settings > Privacy and security > Security > Advanced > Manage certificates > Authorities > Import.

##### Issue a certificate

Create a private key:
```
openssl genrsa -out localhost.key 2048
```
Create a certifcate signing request (CSR):
```
openssl req -new -key localhost.key -out localhost.csr
```
Answer all questions somehow (choose a sensible common name).

Create a file `localhost.ext` holding additional configuration for the certificate signing process:
```
authorityKeyIdentifier = keyid, issuer
basicConstraints = CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 192.168.178.28
IP.2 = 192.168.178.29
IP.3 = 127.0.0.1
```
Create the cert:
```
openssl x509 -req -in localhost.csr -CA myCA.pem -CAkey myCA.key -CAcreateserial -out localhost.crt -days 1825 -sha256 -extfile localhost.ext
```

##### Install the certificate

Move the private key and the cert to your system's corresponding locations. For Debian:
```
sudo cp localhost.crt /etc/ssl/certs/
sudo cp localhost.key /etc/ssl/private/
```
Set paths for both files in nginx site config file (`ssl_certificate` and `ssl_certificate_key` in `server` block).

(first-start-of-moodle)=
#### First start of Moodle

##### Image and container

Create Moodle's Podman image:
```
cd images/test-moodle
./build.sh
```
Then `cd ../../test-moodle` and
* adapt the `PORT` variable in `config.sh` to your needs (`9090` if follow these docs exactly),
* set `MOODLE_URL_DOMAIN` and maybe also other values in `container.env` to fit your environment (`https://192.168.178.29` if you use the IP address suggested in these docs),
* place your root CA's cert in `ca.pem` (if you use a custom root CA).

Now run `run.sh` to get the Moodle container is up and running.

##### Initialization of Moodle

On first boot of the container Moodle does some data base initialization. This may take a few minutes. Moodle's will place its data base and several other files in the `runtime` directory. If you remove the container and start a new one, Moodle will skip the initialization step use files from that directory if available. To start with a completely fresh Moodle containes delete all directories in `runtime`.

Enter the container's shell with `shell.sh` und run `journalctl` to check whether everything is working.

In your webbrowser open `https://192.168.178.29/moodle`. Log in as user `admin` with password `Admin123.`.
Answer all questions asked.
Even though the email addresses have to be entered, they serve no purpose because mail is not configured and so the addresses may be chosen at will.

```{note}
After applying the changes to the admin account Moodle will show an error page for some unknown reason. Simply load `https://192.168.178.29/moodle` again and everything works as expected.
```

The `admin` user is the only exiting user.
You may add other users for testing.

##### Moodle security settings

Moodle has a black list for hosts and a white list for hosts.
Moodle only sends requests to URLs matching both lists.
This is especially important for LTI communication in test environments with non-standard ports and requests to `localhost` and friends.
For instance, hosts `192.168.*.*` are black-listed by default.

Log in to Moodle as `admin`.
Go to 'Site Administration', 'General', 'Security', 'HTTP Security'.
Remove your IP pattern from the hosts black list.

##### Moodle LTI configuration

To access JupyterHub in the Moodle course context, it must be configured as an external tool.
This may be done globally at `Site administration` > `Plugins` > `Manage tools` > `configure a tool manually` or on a per course basis.

Tool settings:
* `Tool URL` - URL of `JupyterHub`, that is `https://192.168.178.29/dev-hub`
* `LTI version` - LTI 1.3
* `Public key type` - Keyset URL
* `Public keyset` - `https://192.168.178.29/dev-hub/services/kore/jwks`
* `Initiate login URL` - `https://192.168.178.29/dev-hub/hub/lti13/oauth_login`
* `Redirection URI(s)` - `https://192.168.178.29/dev-hub/hub/lti13/oauth_callback`
* `Default launch container` - New window

(start-jupyterhub)=
#### Start JupyterHub

Proceed as described in [Install and run a container](#install).
If you use a custom root CA for testing place the CA's cert in `ca.pem` the container definition directory.

Configuration files `20_users.py` and `30_lms.py` may look like

```python
# 20_users.py

c = get_config()

# username(s) of hub admin(s)
# (login to the hub and look at the URL to get your username)
c.Authenticator.admin_users.add('u123')
```

and

```python
# 30_lms.py

c = get_config()

# configuration data provided by your LMS
base_url = 'http://192.168.178.28/moodle'
c.LTI13Authenticator.client_id = ['SomeRandomString']
c.LTI13Authenticator.issuer = base_url
c.LTI13Authenticator.authorize_url = f'{base_url}/mod/lti/auth.php'
c.LTI13Authenticator.jwks_endpoint = f'{base_url}/mod/lti/certs.php'
c.LTI13Authenticator.access_token_url = f'{base_url}/mod/lti/token.php'
```

The user ID for `admin_users` may be extracted from Moodle's URL. The URL looks something like `http://192.168.178.28/moodle/user/profile.php?id=123`, where "123" is your user ID. Remember to prefix the ID with the letter 'u'.

All values for `30_lms.py` may be seen within Moodle's `Tool configuration details`. These are available from the list symbol of the tool (`Site administration` > `Plugins` > `Manage tools`).

### Building the documentation

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

### Release

Steps for new Ananke release:

1. Disable debug mode if necessary:
   * `images/ananke-base/assets/jupyterhub_config.py`
   * `images/ananke-nbgrader/assets/kore/kore.py`
   * `images/ananke-nbgrader/assets/kore/kore_jhub_config.py` (two times)
2. Update version string in doc (`doc/src/conf.py`) and render HTML.
3. Replace `next` heading in `CHANGELOG.md` by version number.
4. Merge `dev` branch into `main` branch.
5. Create release on GitHub.
6. Make image tar files:
   * `podman save -o ananke-base.tar ananke-base`
   * `gzip -9 ananke-base.tar`
   * `podman save -o ananke-nbgrader.tar ananke-nbgrader`
   * `gzip -9 ananke-nbgrader.tar`
7. Upload tar files to webserver.
8. Upload HTML doc to webserver.

## Deployment models

If providing Ananke-based JupyterHubs, one has to decide what kind of deployment model to use:
* *fully managed*: host admin is identical to container admin (no installation or config work for instructors, instructor cannot modify global Python environment)
* *managed host*: host admin is different from container admin (instructor is container admin, a good model for experienced JupyterHub admins with some need for individual/direct configuration including modifications to the global Python environment)
* *fully self-managed*: user sets up its own host machine along the lines of the Ananke project (good for people with special performance needs like GPU servers)

## Technical background

### User management

There is no root or sudo user inside an Ananke container.
Modifications to containers have to be implemented by the container admin, which is a regular user on the host machine.

Inside a container, users are generated dynamically via systemd's [dynamic users](https://0pointer.net/blog/dynamic-users-with-systemd.html) feature.
Home directories of dynamic users are persistent.
Thus, hub users shouldn't recognize that their accounts are created dynamically.

Container admins are unprivileged users on the host system.
Thus, they should not have access to another container admin's containers.

### Conda environments

Starting with 0.3 Ananke uses [`nb_conda_kernels`](https://github.com/Anaconda-Platform/nb_conda_kernels) to make IPython kernels from different conda environments available in Jupyter.
The advantage compared to usual kernel management via `ipykernel install` is that kernels installed by `nb_conda_kernels` automatically run `conda activate` at start-up.
This is necessary for some packages (TensorFlow, Plotly) to have access to relevant environment variables.
With standard kernel management there is no `conda activate` at start-up.

### Kore for LTI related features

Ananke adds LTI capabilities to JupyterHub and Nbgrader. Two components are involved:
* The *Kore service* running as a JupyterHub service provides a REST API for LTI functions. Before Ananke 0.5 this service also provided a GUI for course and grades management.
* The *Kore lab extension* provides a GUI in JupyterLab for course and grades management starting with Ananke 0.5.

Note that there is no Jupyter Server extension involved, because LTI functions heavily interact with the authentication process.
Thus, they have to be implemented globally for the whole JupyterHub.

**Explanation**
Kore is a Flask-based web application to manages courses, assignments, grades, and related functionalities through a set of routes and integrations with JupyterHub.
It handles configuration loading, session management, and various HTTP requests to process user actions like managing courses, sending grades, and handling course data.

The `grades_route.py` file implements a `/grades` endpoint, which processes grades and sends them securely to an external Learning Management System (LMS).
It handles JWT-based authentication, reads data from a local Gradebook, and ensures error handling across several steps, including reading configuration files and posting scores.

The `courses_route.py` file introduces routes for managing courses, including listing active and current courses, copying, backing up, resetting, and deleting courses.
It interacts with course directories, handles file operations, and modifies JupyterHub configurations for course management.
The file includes detailed error handling, particularly around system calls and configuration management, and ensures smooth integration with nbgrader for course grading.

The `assignments_route.py` and `problems_route.py` files define the `/assignments` and `/problems` endpoints for listing and copying assignments and problems respectively.
They retrieve data and manages file operations to copy assignments/problems between directories, ensuring proper permissions and error handling.

The `home_route.py` file in combination with the jinja template files is used to render the frontend if the service is accessed via the Hub Control Panel.

### Container structure

#### `systemd`
Ananke's Podman containers run `systemd` as the main process.
JupyterHub then is a `systemd` service and JupyterHub uses `systemdspawner` for running hub users' JupyterLabs.
This setup requires Linux with 'cgroups v2' and `systemd` on the host system (Debian, Ubuntu and most others).
Remember that containers are not virtual machines! All containers and the host machine share one and the same Linux kernel.

#### Boot script

Each Ananke image comes with a script `assets/boot.sh` which is run at container boot time.

#### Nbgrader exchange directory

The exchange directory for nbgrader inside a container is `/opt/nbgrader_exchange`.
It cannot be in `/home` because dynamic users have no access to `/home` (the home path is mapped to dynamic user's home path in `/var`).

### Arguments to `podman create`

Some special arguments are used in the Ananke Manager script `ananke` for creating containers:
* `-p 8000:8000` makes port 8000 (right one) inside the container available as port 8000 (left one) outside.
* `--cap-add SYS_ADMIN` allows the container to create dynamic systemd users.
* `--mount=type=bind,source=runtime/dyn_home,destination=/var/lib/private` mounts the host machines `runtime/dyn_home` to the container's `/var/lib/private` making dynamic users' home directories persist container rebuilds and restarts.
* `-m=8g` limits memory usage of the container to 8 GB.

(why-podman)=
### Why Podman?

[Podman](https://podman.io/) is an alternative to [Docker](https://www.docker.com/) providing almost identical command line interface.
In contrast to Docker Podman integrates more tightly with some modern Linux features used by the Ananke project (allowing for [systemd](https://en.wikipedia.org/wiki/Systemd) in containers, for instance) and provides a higher level of security (containers run as non-root user).
Here is a list of Podman's advantages:
* Containers run unprivileged and may be managed and started by unprivileged users. Docker requires root privileges or heavy tweaking.
* `systemd` inside containers is supported, whereas Docker requires heavy tweaking to get `systemd` running.
* Podman is a usual program, not a daemon, whereas Docker wants to run permanently in the background (with root permissions) even if there are no containers to run.
* Podman's CLI is compatible with Docker's CLI. Thus, nothing new to learn.
* Podman is available in almost all Linux distributions.

### Podman install hints

If you experience problems with Podman, your SELinux configuration may be a possible cause.
You may check your current mode with `sestatus | grep "Current mode"`.
If the mode is set to 'enforcing' change it temporarily with the command `sudo setenforce Permissive`.
The changes won't persist between reboots.

In some Linux distributions, relevant packages seem to be not installed properly.
If Podman throws errors try to install packages `runc` and `crun` manually.

### Dynamic user details

If `systemd` runs a command as dynamic user it takes the (possibly existing) state directory (dynamic user's home) and recursively sets its ownership to the dynamically created uid:gid value.

If the user's lab is running (and the lab may run even if the user is logged out) and we want to run a command within the user's home directory (to alter the user's Jupyter configuration, for instance), we have to remember and then reset original ownership.
Both commands (lab and some config command) run as different dynamic users with identical home directory.
The command issued last (config command) determines ownership of a user's home and may prevent the longer running command (lab) from accessing user's files! Lab having no (write) access to files in home makes files non-editable for the user in the lab session.

See [Dynamic Users with systemd](https://0pointer.net/blog/dynamic-users-with-systemd.html) for more details.

## See also

- [Reference implementation test tool](https://lti-ri.imsglobal.org) from IMS global
- [LTI bootcamp](https://ltibootcamp.theedtech.dev) utilizing a Flask server and Jupyter Notebook as tool
- [YouTube channel of Claude Vervoort](https://www.youtube.com/channel/UCKcdpZMUQj5kU4TssE8Q1Jg) with explanation and example videos
- [Google group thread](https://groups.google.com/g/jupyter-education/c/axpnAbNbq6I) for LMS integration and JupyterHub
- [Nbgrader LTI Export Plugin](https://github.com/huwf/nbgrader-export-plugin)
- [saltire](https://saltire.lti.app/) LTI tool and platform for testing without restrictions (more features than IMS global)
