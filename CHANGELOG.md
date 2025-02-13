# Changelog

## Next release (dev branch)

* New features:
  * install script for [jupyter_scheduler](https://github.com/jupyter-server/jupyter-scheduler)
  * [jupyter-resource-usage](https://github.com/jupyter-server/jupyter-resource-usage)
* Documentation improvements:
  * hints on batch autograding with Nbgrader
  * alternative method for enlarging container admins' home directories
  * more realistic test environment for development
  * connect to LMS via HTTPS with enterprise root CA
* Bugfixes:
  * increase PID limit in container templates
  * avoid `:` in nbgrader feedback paths (timestamps!) to be compatible with jupyter-fs
  * downgrade jupyter-collaboration to stable release (instead of beta)
* Update all packages:
  * JupyterHub 5.2.1
  * JupyterLab 4.3.5
  * Notebook 7.3.2
  * Nbgrader 9.5
  * Python 3.13.1

## Ananke 0.5

* New features:
  * **BREAKING CHANGE** - LTI/Nbgrader course and grades management is now accessible through the 'Kore' menu item in the instructor's JupyterLab (see [kore-extension](https://github.com/marcwit/kore-extension)). This replaces the former Kore service GUI. See [Update form Ananke 0.4 to Ananke 0.5](https://gauss.whz.de/ananke/doc/container-admins.html#update-to-0_5) for hints on updating your installation.
  * **BREAKING CHANGE** - Images and Containers now are managed by one Python script instead of several bash scripts. Directory structure changed, too. See [Update from Ananke 0.4 to Ananke 0.5](https://gauss.whz.de/ananke/doc/container-admins.html#update-to-0_5) for hints on updating your installation.
  * [jupyterlab-execute-time extension](https://github.com/deshaw/jupyterlab-execute-time) is activated in all JupyterLabs by default. 
* Minor additions and corrections to doc.
* Bugfixes:
  * hide Nbgrader menu in collaboration rooms
  * remove default Python kernel from formgrader user labs
* Update all packages:
  * JupyterHub 5.1.0
  * JupyterLab 4.2.4
  * Notebook 7.2.1
  * Nbgrader 9.3
  * Python 3.12.5
* Update to Moodle 4.4.2 for development/testing

## Ananke 0.4

* Minor additions and corrections to doc.
* Bugfixes:
  * Disable Jupyter's default kernel (cf. [issue 24](https://github.com/jeflem/ananke/issues/24)).
  * Disable Nbgrader menu in collaboration rooms (cf. [issue 23](https://github.com/jeflem/ananke/issues/23))
* Update all packages:
  * JupyterHub 4.0.2 (as before)
  * JupyterLab 4.1.1 (was 4.0.7)
  * Nbgrader 0.9.1 (as before)
  * Notebook 7.1.0 (was 7.0.6)
  * Python 3.11.8 (was 3.11.6)
* Podman image for Moodle to simplify testing for developers (partially based on work by [Carl Kuhligk](https://github.com/CarlKuhligk))

## Ananke 0.3

* Fixed typos and broken links in doc.
* Update all packages:
  * JupyterHub 4.0.2 (as before)
  * JupyterLab 4.0.7 (was 4.0.4)
  * Nbgrader 0.9.1 (as before)
  * Notebook 7.0.6 (was 7.0.2)
  * Python 3.11.6 (was 3.11.4)
* Change to JupyterHub's LTI config due to a bug in LTIAuthenticator/Traitlets (see [GitHub issue](https://github.com/jupyterhub/ltiauthenticator/issues/177) for details). **Maybe you have to modifiy your `30_lms.conf`. The value for `c.LTI13Authenticator.client_id` now always has to be a list!**
* Use [`nb_conda_kernels`](https://github.com/Anaconda-Platform/nb_conda_kernels) for kernel management. Commands for creating/cloning/removing local conda environments have slightly changed, see hub users doc.
* Add install scripts for optional features (base packages, MyST markdown rendering, WebDAV support, real-time collaboration).
* Simplify configuration of collaboration rooms.
* Container admin doc has new section on language server protocol (LSP) support.
* Conda uses `conda-forge` channel by default.
* Nbgrader feedbacks no longer remove output of hidden tests (but code of hidden tests is still removed). See instructors doc for corresponding config options.
* System load info with `htop` based on the container's resource limits is available inside containers.
* Several minor improvements to doc.

## Ananke 0.2

* Do not use LMS course title for creating nbgrader course ID. This allows to modify LMS course title without having to recreate the course for nbgrader. **Breaks courses created with Ananke 0.1** (undefined/untested behavior).
* Update developer doc (release procedure).
* Do not show formgrader services in hub control panel services drop down.

## Ananke 0.1

The first Ananke release.
