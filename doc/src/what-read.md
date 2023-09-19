# What to read?

This documentation aims at different types of users:
* regular Jupyter users like students (denoted *hub users*)
* Jupyter users with course management permissions (denoted *instructors*)
* Jupyter users with maximum permissions inside Jupyter (denoted *hub admins*)
* users with access to the host system (denoted *container admins*)
* users with maximum permissions on the host system (denoted *host admins*)
* members of the development team (denoted *developers*)

The Documentation structure follows these user types.
Depending on your roles, you should read the corresponding sections.

Users may have different roles at once.
An instructor is likely to be a hub admin, too.
In small deployments hub admin, container admin and host admin may be one and the same person.

Below, you find more details on the mentioned types of users.

```{contents}
---
local: true
---
```

## Hub users

*Hub user* login to the JupyterHub and work in their JupyterLab environment.
They have access to their personal files only and to nbgrader courses made available to them by an instructor.

In a teaching environment, students are hub users.

## Instructors

*Instructors* are regular hub users with additional privileges.
They configure access to the JupyterHub via LMS user groups, and they may create courses for nbgrader.
There may exist several instructors on one and the same JupyterHub deployment.

## Hub admins

A *hub admin* is a more privileged instructor.
Hub admins see who is currently active on the JupyterHub and other details.
They may look into currently running user sessions, and they may stop or restart a user's JupyterLab.

## Container admins

*Container admins* have access to the host system (via SSH or physical) with regular Linux user permissions.
They have full control of their JupyterHub's Podman container, may log in to the Podman container, and have maximum permissions inside the container.

Typical tasks for container admins are updating software inside the container, restarting the container, changing the container's configuration.
In particular, container admins are responsible for the whole JupyterHub's configuration including LMS communication via LTI.

## Host admins

A *Host admin* has maximum permissions on the host machine.
Host admins may add or remove container admin accounts.
They activate and deactivate access to JupyterHubs running on the host machine, and they are responsible for overall security of the system.

## Developers

*Developers* create container images and tools used inside containers for LMS communication of JupyterHub and for nbgrader course management.