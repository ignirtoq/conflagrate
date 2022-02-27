from enum import Enum

__all__ = ['BranchType']


class BranchType(str, Enum):
    simple = 'simple'
    matcher = 'matcher'
