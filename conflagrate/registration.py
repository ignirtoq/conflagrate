from dataclasses import dataclass
from typing import Any, Callable, Dict, Tuple, Type

from .asyncutils import make_awaitable
from .controlflow import BranchType

__all__ = ['nodetype']


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


_node_types: Dict[str, NodeType] = {}


def nodetype(name, branchtype=BranchType.simple):
    def decorator(callable):
        if name in _node_types:
            raise ValueError(f'node type already associated with name "{name}"')

        input_datatypes, output_datatypes = (
            get_input_output_datatypes_from_callable(callable))

        node_type_class: Type[NodeType] = NodeType
        if branchtype == BranchType.matcher:
            try:
                output_datatypes = output_datatypes.__args__[1]
            except AttributeError:
                raise ValueError('matcher branching nodes must annotate their '
                                 'return value as a collection')
            node_type_class = MatcherNodeType

        _node_types[name] = node_type_class(callable, branchtype,
                                            input_datatypes, output_datatypes)

        return callable

    return decorator


def get_input_output_datatypes_from_callable(callable: Callable) -> Tuple:
    if not callable.__annotations__:
        raise ValueError('node must define type annotations for inputs '
                         'and outputs')

    annotations: Dict[str, Any] = callable.__annotations__

    try:
        output_datatypes = annotations['return']
    except KeyError:
        raise ValueError('all nodetype definitions must be fully annotated')
    input_datatypes = [
        annotations[key] for key in annotations if key != 'return'
    ]
    return input_datatypes, output_datatypes


def get_nodetypes() -> Dict[str, NodeType]:
    return _node_types.copy()
