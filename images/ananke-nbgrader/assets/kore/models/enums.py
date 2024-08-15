from enum import Enum, auto


class Subset(Enum):
    """
    An enumeration representing the possible subsets of a collection.

    This enum defines three possible values for subsets:
    - `ALL`: Represents the entire collection. Used for retrieving the complete list of courses including all active/running courses as well as all backed up courses.
    Currently not used in code.
    - `ACTIVE`: Represents the subset indicating all active/running courses. This list will be used for course deletion.
    - `CURRENT`: Represents the current course (the course the user accessed JupyterHub from). This list will be used for grading, when grading_scope is current (see config.json).
    - `OTHER`: Represents the subset indicating a list of all courses except the one the user is currently

    """
    ALL = auto()
    ACTIVE = auto()
    CURRENT = auto()
    OTHER = auto()


class Content(Enum):
    COURSES = 'courses'
    ASSIGNMENTS = 'assignments'
    PROBLEMS = 'problems'
