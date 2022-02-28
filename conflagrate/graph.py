from dataclasses import dataclass, field
from typing import Callable, Dict, Tuple, Union

from .asyncutils import make_awaitable
from .controlflow import BranchType


@dataclass
class NodeType:
    """
    An association of an executable block of code with a type of node that
    can appear in a control flow graph.  An individual block of code may
    be associated with more than one node in a graph.
    """
    callable: Callable
    branchtype: BranchType
    input_datatype: Tuple
    output_datatype: Tuple

    def __call__(self, *args, **kwargs):
        return make_awaitable(self.callable, *args, **kwargs)


@dataclass
class MatcherNodeType(NodeType):
    """
    An association of an executable block of code with a type of node that
    can appear in a control flow graph.  The Matcher variation supports
    branching to multiple nodes further in the graph.  The code block is
    expected to emit a "match value" that is compared to values denoted for
    each branch.  The matching branch is then selected for the next execution.
    """
    pass


@dataclass
class Node:
    """
    A unique node in a control flow graph.  Connects a block of code from the
    NodeType with the possibly branching paths that follow execution.
    """
    name: str
    typename: str
    nodetype: NodeType
    edges: Union['Node', Dict[str, 'Node']] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.name)

    def __call__(self, *args, **kwargs):
        return self.nodetype(*args, **kwargs)

    def get_output_data(self, callable_output):
        return callable_output

    def has_next_node(self):
        return bool(self.edges)

    def get_next_node(self, callable_output):
        return self.edges


@dataclass
class MatcherNode(Node):
    """
    A unique node in a control flow graph.  Connects a block of code from the
    NodeType with the possibly branching paths that follow execution.  The
    matcher node selects a single branch from possible following paths based
    on a matching value.
    """
    def __hash__(self):
        return hash(self.name)

    def get_output_data(self, callable_output):
        return callable_output[1]

    def get_next_node(self, callable_output):
        try:
            return [self.edges[callable_output[0]]]
        except KeyError:
            return []


@dataclass
class Graph:
    nodes: Dict[str, Node]