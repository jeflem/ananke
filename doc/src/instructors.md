# For instructors

Instructors are regular hub users with additional permission to manage courses in nbgrader.
In the learning management system (LMS) they create courses and control access to those courses and, thus, to the JupyterHub.

```{contents}
---
local: true
---
```

## Nbgitpuller

Ananke-based JupyterHubs have [nbgitpuller](https://github.com/jupyterhub/nbgitpuller) installed.
Nbgitpuller takes content from a git repository (GitHub, GitLab and others), synchronizes the repo into each user's home directory and opens the requested notebook when the user clicks the nbgitpuller link.

To generate nbgitpuller links use the [nbgitpuller link generator](https://nbgitpuller.readthedocs.io/en/latest/link.html).

```{important}
If your users log in to the hub via LTI they first have to come to their JupyterLab via the LMS.
Then they can click the nbgitpuller link.
```

## Shared directories

If you want to provide data to your hub users or if hub user shall have access to shared directories, ask your container admin to activate this feature.

## Nbgrader

### Basic usage

To create and manage nbgrader assignments in your JupyterLab session click 'Nbgrader', 'Course List'.
In the list, click your course.
A new JupyterLab session opens.
This session belongs to a separate user account created for the course.

In the course's Lab session click 'Nbgrader', 'Formgrader'.
Usage of the formgrader GUI is described in [nbgrader's documentation](https://nbgrader.readthedocs.io/en/stable/user_guide/creating_and_grading_assignments.html).

```{important}
If you create a new course in your LMS you have to visit the hub via that course before any student is able to use the course.
On first visit modified course structure is synced between LMS and JupyterHub.
```

```{hint}
After creating a new LMS course the first login to the hub from this course takes several seconds.
Even if you see the JupyterLab GUI wait another 5 seconds and ignore cumbersome messages appearing on screen (click 'Dismiss').
The hub is restarting in the background, which takes a while.
```

```{note}
When collecting submissions with the formgrader, nbgrader will complain about possible cheating attempts in the log output due to unexpected file ownerships. This warning can be savely ignored as long as no student tries cheating ;-) The warning is caused by Ananke's management of user accounts. Developers plan to tackle this problem in a future release.
```

### Feedback configuration

Nbgrader provides two configuration options for feedback generation. In the course's Lab open a terminal and run `nano .jupyter/nbgrader_config.py`. A console based text editor will open showing a few lines of Python code. Do not change anything here except for (un)commenting following two lines:
* If `'nbgrader.preprocessors.ClearHiddenTests',` is active (not commented out), then students won't see the code of hidden tests in their feedback files. Else you will disclose your hidden tests. Note that this option does not (!) remove output of hidden tests.
* If `'nbgrader.preprocessors.Execute'` is active (not commented out), then the students' notebooks will be reexecuted. If you have removed code of hidden tests with above option, then reexecution will remove output of hidden tests, too (including tracebacks). Whether this is a good idea depends on your test and feedback design, because reexecution will remove any outputs (feedback!) from hidden tests, too.

Close the editor with Ctrl-C, then Y, then return. Close the terminal by typing `logout`.

### Further configuration

To use custom delimiters for your sample solution add following lines to the formgrader user's `.jupyter/nbgrader_config.py` (cf. above):
```python
c.ClearSolutions.begin_solution_delimeter = "BEGIN MY SOLUTION"
c.ClearSolutions.end_solution_delimeter = "END MY SOLUTION"
```

Code cells to be filled by the student contain `raise NotImplementedError` by default. You may place different code there by adding
```python
c.ClearSolutions.code_stub = {
    "python": "YOUR_DEFAULT_CODE_FOR_STUDENT_CELLS"
}
```
to `.jupyter/nbgrader_config.py`.

## Kore

The Kore service on the one hand sends nbgrader's grades to the LMS.
On the other hand, it provides course management functionality for nbgrader.

Access Kore from your JupyterLab session by clicking 'File', 'Hub Control Panel', 'Services', 'kore'.

Sending grades to the LMS only works for the LMS course you started your Jupyter session from.
All other functionality works for all your courses.
If you are a hub admin, then you have access to all instructors' courses on the hub via Kore.