import inspect

from typing import Any, Callable, Dict, Tuple, Type

from .controlflow import BranchingStrategy
from .graph import MatcherNodeType, NodeType
from .asyncutils import BlockingBehavior

__all__ = ['nodetype']

_node_types: Dict[str, NodeType] = {}


def nodetype(
        name: str,
        branching_strategy: BranchingStrategy = BranchingStrategy.parallel,
        blocking_behavior: BlockingBehavior = BlockingBehavior.BLOCKING
) -> Callable:
    """
    Identify a function as the implementation of a type of node on graphs.

    The node type is the connection between a control flow graph diagram and a
    functional application.  As the application traverses the graph, at each
    node it will call the associated node type function.  The positional
    arguments of the function will be the return value of the previous node's
    function (returned collection objects will be unpacked as separate
    arguments).

    A node type can be a regular function or a coroutine function.  Regular
    functions should indicate if they are non-blocking, as otherwise they
    will be called in a dedicated thread, which incurs some overhead.

    :param name: The value of the "type" attribute annotated on nodes of the
        graph for which this function should be called.
    :param branching_strategy: How nodes following this node type should be
        called in the case there are multiple choices.  See the
        BranchingStrategy class for details and values.
    :param blocking_behavior: Whether the function is blocking or non-blocking.
        See the BlockingBehavior class for details and values.
    :return: Decorated function.
    """
    def decorator(function):
        blocking_flag = get_blocking_behavior(blocking_behavior, function)
        if name in _node_types:
            raise ValueError(f'node type already associated with name "{name}"')

        input_datatypes, output_datatypes = (
            get_input_output_datatypes_from_callable(function))

        node_type_class: Type[NodeType] = NodeType
        if branching_strategy == BranchingStrategy.matcher:
            try:
                output_datatypes = output_datatypes.__args__[1]
            except AttributeError:
                raise ValueError('matcher branching nodes must annotate their '
                                 'return value as a collection')
            node_type_class = MatcherNodeType

        _node_types[name] = node_type_class(function, branching_strategy, blocking_flag,
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
