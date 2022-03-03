import inspect

from typing import Any, Callable, Dict, Tuple, Type

from .controlflow import BranchType
from .graph import MatcherNodeType, NodeType
from .asyncutils import BlockingBehavior

__all__ = ['nodetype']

_node_types: Dict[str, NodeType] = {}


def nodetype(
        name: str,
        branchtype: BranchType = BranchType.simple,
        blocking_behavior: BlockingBehavior = BlockingBehavior.BLOCKING
) -> Callable:
    def decorator(function):
        blocking_flag = get_blocking_behavior(blocking_behavior, function)
        if name in _node_types:
            raise ValueError(f'node type already associated with name "{name}"')

        input_datatypes, output_datatypes = (
            get_input_output_datatypes_from_callable(function))

        node_type_class: Type[NodeType] = NodeType
        if branchtype == BranchType.matcher:
            try:
                output_datatypes = output_datatypes.__args__[1]
            except AttributeError:
                raise ValueError('matcher branching nodes must annotate their '
                                 'return value as a collection')
            node_type_class = MatcherNodeType

        _node_types[name] = node_type_class(function, branchtype, blocking_flag,
                                            input_datatypes, output_datatypes)

        return function

    return decorator


def get_input_output_datatypes_from_callable(callable: Callable) -> Tuple:
    if not callable.__annotations__:
        raise ValueError('node must define type annotations for outputs')

    annotations: Dict[str, Any] = callable.__annotations__

    try:
        output_datatypes = annotations['return']
    except KeyError:
        raise ValueError('all nodetype definitions must be fully annotated')
    input_datatypes = [
        annotations[key] for key in annotations if key != 'return'
    ]
    return input_datatypes, output_datatypes


def get_blocking_behavior(
        blocking_flag: BlockingBehavior,
        function: Callable
) -> BlockingBehavior:
    if (blocking_flag is BlockingBehavior.NON_BLOCKING
            or inspect.iscoroutinefunction(function)):
        return BlockingBehavior.NON_BLOCKING
    else:
        return BlockingBehavior.BLOCKING


def get_nodetypes() -> Dict[str, NodeType]:
    return _node_types.copy()
