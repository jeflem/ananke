# Ananke Jupyter Distribution

The Ananke project provides preconfigured [JupyterHub](https://jupyter.org/hub) images for [Podman](https://podman.io) (a [Docker](https://www.docker.com)-like containerization tool) with a focus on integrating [JupyterLab](https://jupyter.org) and [nbgrader](https://nbgrader.readthedocs.io) into learning management systems (LMS) like [Moodle](https://moodle.org), [Canvas](https://www.instructure.com/canvas) and many others.

The project's core is the Kore service providing GUI-based course management and an [LTI 1.3](https://en.wikipedia.org/wiki/Learning_Tools_Interoperability) interface for nbgrader.

Target group are administrators of small to medium-sized JupyterHubs used in teaching environments with a handful of courses.
The project's focus is not on large-scale JupyterHubs with thousands of users but on:
* easy setup and operation for instructors and students,
* advice and preconfiguration for administrators,
* flexibility to implement different application scenarios.

Also have a look at [Ananke website](https://www2.htw-dresden.de/~fjeme691/ananke).

## Overall architecture

The structure of an Ananke-based JupyterHub deployment is as follows:
* A host machine runs one or several Podman containers.
* Each container represents one JupyterHub, which may be used by a whole university or a department or by only one instructor depending on individual configuration needs.
* Each JupyterHub provides individual JupyterLabs for all its users (instructors and students).

## Available container images

The Ananke project uses [Podman](https://podman.io) for containerization.
Podman is free, open source, and compatible with [Docker](https://www.docker.com).
There are several reasons to choose Podman over Docker, the biggest being security-related (rootless containers, daemon-less).

The Ananke project provides the following container images:
* `ananke-base` (JupyterHub with LTI login and nbgitpuller)
* `ananke-nbgrader` (like `ananke-base` plus LTI integrated nbgrader)

## Documentation

See `doc` subdirectory.
There's also an [HTML rendering of the doc](https://www2.htw-dresden.de/~fjeme691/ananke/doc).

## Quickstart
Here are the major steps to get your own JupyterHub with LMS integration:
1. Get a server with Debian Linux (other distros should work, too).
2. Download or build an Ananke Podman image.
3. Choose a configuration template.
4. Create a container.
5. Configure your LMS.

See [documentation](https://www2.htw-dresden.de/~fjeme691/ananke/doc) for detailled install instructions.

## Contributing

Contributions are essential to this project’s growth and success, and we warmly welcome all who want to participate!
Whether you're fixing bugs, reviewing pull requests, opening issues, answering questions, or enhancing our documentation.

There are many ways to contribute:
- **Opening and reviewing pull requests** - Suggest improvements, help review existing changes, or submit your own pull requests with new features or bug fixes.
- **Reporting issues** - Found a bug or have an idea for an enhancement? Open an [issue](https://github.com/jeflem/ananke/issues) and let us know. Be sure to check out our guide on [Writing a good issue](#writing-a-good-issue) to help us understand and resolve it quickly.
- **Answering questions** - Help other users by answering questions and sharing your knowledge.
- **Improving documentation** - Help us keep our documentation clear, accurate, and up-to-date.

Whatever way you choose to contribute, we’re grateful for your time and effort in making this project better.

## Writing a good issue
Creating a well-structured issue helps us understand and resolve it more effectively. Here are some tips for writing a good issue:
- Use a **descriptive title** - Clearly summarize the issue in the title to help others quickly understand the topic.
- **Provide context** - Explain the problem or feature request in detail. Describe what you’re trying to achieve and why it’s important.
- **Steps to reproduce** (for bugs) - If you’re reporting a bug, include clear steps to reproduce the issue. Add screenshots, code snippets, or error messages if possible.
- **Expected vs. actual behavior** - For bugs, describe what you expected to happen and what actually happened.
- **Environment** details - Specify your setup or any other relevant environment details.
- **Label** appropriately - Use labels to classify the issue as a bug, enhancement, question, or other categories as relevant.

Following these steps helps us address issues quickly and effectively.

## Support

If you need assistance with this project, we’re here to help!
Here are ways to get support:

- **Documentation** - Begin with our documentation for answers to common questions and to understand the project’s features.
- **Known issues** - Check the [issue](https://github.com/jeflem/ananke/issues) tab to see if your question or issue is already known, along with any existing workarounds or general answers.

## Contact and contributors

The Ananke project started as a joint project of [Leipzig University of Applied Sciences](https://www.htwk-leipzig.de/en/htwk-leipzig) and [Zwickau University of Applied Sciences](https://www.fh-zwickau.de/english/).

The project team currently consists of:
* [Jens Flemming](https://www2.htw-dresden.de/~fjeme691/flemming)
* [Konrad Schöbel](https://fdit.htwk-leipzig.de/fakultaet-dit/personen/professoren/prof-dr-konrad-schoebel)
* [Marcus Wittig](https://www.fh-zwickau.de/?id=5361)