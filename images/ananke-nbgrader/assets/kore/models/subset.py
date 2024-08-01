from enum import Enum


class Subset(Enum):
    """
    An enumeration representing the possible subsets of a collection.

    This enum defines three possible values for subsets:
    - `ALL`: Represents the entire collection. Used for retrieving the complete list of courses including all active/running courses as well as all backed up courses.
    Currently not used in code.
    - `ACTIVE`: Represents the subset indicating all active/running courses. This list will be used for course deletion.
    - `OTHER`: Represents the subset indicating a list of all courses except the one the user is currently

    """
    ALL = 'all'
    ACTIVE = 'active'
    OTHER = 'other'
