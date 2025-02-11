# For developers

This chapter collects technical background information relevant to developers.
It's not intended to be a complete description of the system (although that would be nice), but highlights very specific aspects only.

```{contents}
---
local: true
backlinks: none
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

## Local testing with LMS

Ananke cannot be used without LMS, because JupyterHub's login process solely relies on LTI. You may use whatever LTI capable LMS is available to you for testing. But to facilitate local development and testing the Ananke project ships with a Podman image for [Moodle](https://moodle.org/). In this section we describe how to set up your network and a local Moodle instance for Ananke development.
```{warning}
The Moodle Podman image is for local testing only.
Never (!!!) use it on a public facing server.
It's by no means secure!
```

### Overview

The following list shall guide you through the proper setup.
See the corresponding sections of individual steps.

* Adjust your development machine's networking configuration and (optionally) install a reverse proxy, see [Networking configuration](#networking-configuration).
* Start and configure Moodle, see [First start of Moodle](#first-start-of-moodle).
* Build Ananke images, configure LTI for JupyterHub, and run a container, see [Start JupyterHub](#start-jupyterhub).

(networking-configuration)=
### Networking configuration

You may choose between a simple networking setup (without reverse proxy and without HTTPS) or the full setup (with reverse proxy and HTTPS). The simple setup is sufficient for most development tasks. The full setup allows to test under more realistic conditions. In particular, several security features (and related troubles) will only be active with the full setup. Some JupyterLab extensions won't work in the simple setup. An example is [jupyter-fs](https://github.com/jpmorganchase/jupyter-fs).

#### Simple setup

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
Ports are specified in Moodle's `run.sh` and `config.php` as well as in an Ananke container's `config.py` script. If you are comfortable with `9090` and `8000` you do not have to modify those files (for the moment).

If the host machine is using SELinux run `sudo setenforce Permissive`. Otherwise there will be permission errors.

Note that in Chromium webbrowser some of the limitations of the simple networking setup can be circumvented as follows:
1. Type `chrome://flags/#unsafely-treat-insecure-origin-as-secure` in Chromium's address bar.
2. Fill the text area with your local IP and the JupyterHub port (`http://192.168.178.128:8000`).

#### Full setup

The simple networking setup has two major drawbacks:
* There's no HTTPS and no reverse proxy, which makes things much simpler and less error-prone than usual production setups.
* The LMS (Moodle) and Ananke use the same domain, which only in very rare cases is what will happen in production.

Both points disable security features of modern browsers, like [CORS](https://developer.mozilla.org/de/docs/Web/HTTP/CORS). The full networking setup descibed in this section should yield a development environment very similar to typical production environments.

##### IP addresses

Create two additional IP addresses for `localhost` (cf. simple setup):
```
sudo ip addr add 192.168.178.28 dev lo
sudo ip addr add 192.168.178.29 dev lo
```
Ananke will use `192.168.178.28`. Moodle will be on `192.168.178.29`. So LMS and JupyterHub run on different domains.

##### Reverse proxy

Install [nginx](https://nginx.org/) as reverse proxy and HTTPS endpoint. See [Reverse proxy](#host-admins-reverse-proxy) in the host admins documentation for details.

If you have a certificate issued by a commonly trusted CA, install the cert to your system's cert store (see below for Debian). If you do not have a cert issued by a commonly trusted CA, you have to set up your own root CA, because JupyterHub (or Python packages it builds upon) does not accept self-signed certs from servers requesting data from.

##### Redirects

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
Then Moodle will be on `https://192.168.178.29/moodle` and JupyterHub will be on `https://192.168.178.28/dev-hub`. Note that both Moodle and JupyterHub are on accessible via both IP addresses. But we will use `...29` for Moodle and `...28` for JupyterHub to have them on different domains.

##### Set up a root CA

Create a private key and protect it by a password:
```
openssl genrsa -des3 -out myCA.key 2048
```
Then create the CA's cert valid for 5 years and signed with your private key:
```
openssl req -x509 -key myCA.key -sha256 -days 1825 -out myCA.pem
```
Answer all questions somehow (empty or default values). Answers do not matter as long as you use your CA for local testing only. It's a good idea to choose a sensible common name. Else, you may have difficulties to find your cert in a list of many certs.

Now make your CA's cert known to your systems cert store. On Debian:
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
### First start of Moodle

#### Image and container

Create Moodle's Podman image:
```
cd images/test-moodle
./build.sh
```
Then `cd ../../test-moodle` and start the Moodle container with `run.sh` (after properly setting the `PORT` variable, if you do not want to have Moodle on `9090`).

Now the Moodle container is up and running, but requires some initialization.

#### Initialization of Moodle

Enter the container's shell with `shell.sh` und run `/opt/init_moodle.sh`.
This creates the Moodle database and basic Moodle configuration.
The script will ask you for your Moodle container's URL.
With the above network configuration use `http://192.168.178.28:9090` (simple networking) or `https://192.168.178.29/moodle` (full networking).

If you are using the full networking setup, in the container's shell edit both files `/var/www/html/moodle/config.php` and `/opt/moodledata/config.php` to contain the config option `$CFG->sslproxy = true;`. The file then might look like:
```
...
$CFG->dataroot = '/opt/moodledata';
$CFG->admin = 'admin';
$CFG->reverseproxy = true;
$CFG->sslproxy = true;

$CFG->directorypermissions = 02777;

require_once(__DIR__ . '/lib/setup.php');
```

In your webbrowser open `http://192.168.178.28:9090/moodle` (simple networking) or `https://192.168.178.29/moodle` (full networking).
Log in as user `admin` with password `Admin123.`.
Answer all questions asked.
Even though the email addresses have to be entered, they serve no purpose because mail is not configured and so the addresses may be chosen at will.
The `admin` user is the only exiting user.
You may add other users for testing.
```{important}
Although the container is running at `http://192.168.178.28:9090` in the simple networking setting Moodle's URL is `http://192.168.178.28:9090/moodle`. Contrary, in the full networking setting Moodle's URL ist `.../moodle`, not `.../moodle/moodle` as one might expect from the reverse proxy's config.
```

#### Moodle security settings

Moodle has a black list for hosts and a white list for hosts.
Moodle only sends requests to URLs matching both lists.
This is especially important for LTI communication in test environments with non-standard ports and requests to `localhost` and friends.
For instance, hosts `192.168.*.*` are black-listed by default.

Log in to Moodle as `admin`.
Go to 'Site Administration', 'General', 'Security', 'HTTP Security'.
Remove your IP pattern from the hosts black list (for simple and full networking) and add your JupyterHub port to the ports white list (for simple networking only).

#### Moodle LTI configuration

To access JupyterHub in the Moodle course context, it must be configured as an external tool.
This may be done at `Site administration` > `Plugins` > `Manage tools` > `configure a tool manually`.

Tool settings (simple networking):
* `Tool URL` - URL of `JupyterHub`, that is `http://192.168.178.28:8000`
* `LTI version` - LTI 1.3
* `Public key type` - Keyset URL
* `Public keyset` - `http://192.168.178.28:8000/services/kore/jwks`
* `Initiate login URL` - `http://192.168.178.28:8000/hub/lti13/oauth_login`
* `Redirection URI(s)` - `http://192.168.178.28:8000/hub/lti13/oauth_callback`
* `Default launch container` - New window

If you use the full networking setting, replace `http://192.168.178.28:8000` by `https://192.168.178.29/dev-hub`.

#### Persistent data

All data created by Moodle at runtime (users, courses, grades, ...) will be stored in `test-moodle/runtime` on the host machine.
If you destroy the container und start a fresh one, everything will still be available to the new container.
Running `init_moodle.sh` again is NOT required and may result in errors and corrupted data.

To get rid of Moodle's data and start with a fresh Moodle installation, delete the contents of `test-moodle/runtime/moodle_data` and `test-moodle/runtime/mariadb_data` before you create the container.

(start-jupyterhub)=
### Start JupyterHub

Proceed as described in [Install and run a container](#install).
Remember to move your localhost cert to the container, see [HTTPS with enterprise root CA or self-signed cert](container-admins-enterprise-ca).
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
base_url = 'http://192.168.178.28:9090/moodle'
c.LTI13Authenticator.client_id = ['SomeRandomString']
c.LTI13Authenticator.issuer = base_url
c.LTI13Authenticator.authorize_url = f'{base_url}/mod/lti/auth.php'
c.LTI13Authenticator.jwks_endpoint = f'{base_url}/mod/lti/certs.php'
c.LTI13Authenticator.access_token_url = f'{base_url}/mod/lti/token.php'
```

The user ID for `admin_users` may be extracted from Moodle's URL. The URL looks something like `http://192.168.178.28:9090/moodle/user/profile.php?id=123`, where "123" is your user ID. Remember to prefix the ID with the letter 'u'.

All values for `30_lms.py` may be seen within Moodle's `Tool configuration details`. These are available from the list symbol of the tool (`Site administration` > `Plugins` > `Manage tools`).

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

## Arguments to `podman create`

Some special arguments are used in the Ananke Manager script `ananke` for creating containers:
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

## Links

- [Reference implementation test tool](https://lti-ri.imsglobal.org) from IMS global
- [LTI bootcamp](https://ltibootcamp.theedtech.dev) utilizing a Flask server and Jupyter Notebook as tool
- [YouTube channel from Claude Vervoort](https://www.youtube.com/channel/UCKcdpZMUQj5kU4TssE8Q1Jg) with explanation and example videos
- [Google group thread](https://groups.google.com/g/jupyter-education/c/axpnAbNbq6I) for LMS integration and JupyterHub
- [Nbgrader LTI Export Plugin](https://github.com/huwf/nbgrader-export-plugin)
- [saltire](https://saltire.lti.app/) LTI tool and platform for testing without restrictions (more features than IMS global)
