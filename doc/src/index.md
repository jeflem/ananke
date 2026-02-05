# Ananke documentation

The Ananke project provides preconfigured [JupyterHub](https://jupyter.org/hub) images for [Podman](https://podman.io) (a [Docker](https://www.docker.com)-like containerization tool) with a focus on integrating [JupyterLab](https://jupyter.org) and [nbgrader](https://nbgrader.readthedocs.io) into learning management systems (LMS) like [Moodle](https://moodle.org), [Canvas](https://www.instructure.com/canvas) and many others.

The project's core is the Kore service providing GUI-based course management and an [LTI 1.3](https://en.wikipedia.org/wiki/Learning_Tools_Interoperability) interface for nbgrader.

Target group are administrators of small to medium-sized JupyterHubs used in teaching environments with a handful of courses.
The project's focus is not on large-scale JupyterHubs with thousands of users but on:
* easy setup and operation for instructors and students,
* advice and preconfiguration for administrators,
* flexibility to implement different application scenarios.

## Overall architecture

The structure of an Ananke-based JupyterHub deployment is as follows:
* A host machine runs one or several Podman containers.
* Each container represents one JupyterHub, which may be used by a whole university or a department or by only one instructor depending on individual configuration needs.
* One host machine may provide several JupyterHubs with different configurations and features.
* Each JupyterHub provides individual JupyterLabs for all its users (instructors and students).

## Available container images

The Ananke project uses [Podman](https://podman.io) for containerization.
Podman is free, open source, and compatible with [Docker](https://www.docker.com).
There are several reasons to choose Podman over Docker, the biggest being security-related (rootless containers, daemon-less).

The Ananke project provides the following container images:
* `ananke-base` (JupyterHub with LTI login and nbgitpuller)
* `ananke-nbgrader` (like `ananke-base` plus LTI integrated nbgrader)

## Where to go from here?

This documentation of the Ananke project aims at a wide audience including server administrators as well as instructors and students.
Read [this introduction](what-read.md) to find out what kind of user you are.
Then go on to the corresponding chapter targeting your role and needs.

For source code see [Ananke's GitHub repo](https://github.com/jeflem/ananke).

For general information and download, see [Ananke website](https://www2.htw-dresden.de/~fjeme691/ananke).

## Contact and contributors

The Ananke project started as a joint project of [Leipzig University of Applied Sciences](https://www.htwk-leipzig.de/en/htwk-leipzig) and [Zwickau University of Applied Sciences](https://www.fh-zwickau.de/english/).

The project team currently consists of:
* [Jens Flemming](https://www2.htw-dresden.de/~fjeme691/flemming)
* [Konrad Schöbel](https://fdit.htwk-leipzig.de/fakultaet-dit/personen/professoren/prof-dr-konrad-schoebel)
* [Marcus Wittig](https://www.fh-zwickau.de/?id=5361)

## Funding

The Ananke project started in 2022 as a government-funded project.
Funding is provided by [Saxon State Ministry of Education and Cultural Affairs](https://www.smk.sachsen.de/) (Germany) till the end of 2023.

For legal reasons, we state the following (funding information in German):

> Dieses Projekt wurde durch den [Arbeitskreis E-Learning](https://bildungsportal.sachsen.de/portal/parentpage/institutionen/arbeitskreis-e-learning-der-lrk-sachsen/) der [Landesrektorenkonferenz Sachsen](https://www.lrk-sachsen.de/) im Rahmen der sächsischen E-Learning-Landesinitiative gefördert.
> Die sächsische E-Learning-Landesinitiative wird mitfinanziert durch Steuermittel auf der Grundlage des vom [Sächsischen Landtag](https://www.landtag.sachsen.de) beschlossenen Haushaltes.

## Table of contents

```{toctree}
---
maxdepth: 1
---

what-read
hub-users
instructors
hub-admins
container-admins
host-admins
developers
```
 
