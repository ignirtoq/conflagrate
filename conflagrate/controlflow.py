from enum import Enum

__all__ = ['BranchingStrategy']


class BranchingStrategy(str, Enum):
    """
    Strategy for choosing which trailing branches to execute from a node when
    multiple paths are available.

    The "parallel" strategy is the default and executes all trailing branches
    simultaneously asynchronously.

    The "matcher" strategy chooses a trailing branch based on a value emitted
    by the node, finding the branch annotated with the matching value.  This
    puts constraints on the node type function and the graph definition.  The
    node type function is assumed to output a Collection containing the value to
    be used for matching.  The remaining elements of the collection are treated
    as the functions "intended" output for passing as input to the first nodes
    on the trailing branches.  The values for matching must be defined on the
    edges of the graph using the "value" attribute.  If a branch with the
    matching value is not found, execution terminates at the matcher node.
    """
    parallel = 'parallel'
    matcher = 'matcher'
