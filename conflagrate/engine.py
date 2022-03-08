import asyncio
import contextvars
from enum import Enum, auto
from typing import Any, Dict, List, Union

from .asyncutils import BranchTracker
from .dependencies import DependencyCache
from .graph import Graph, Node
from .parse.graphviz import parse
from .parse.native import Graph

__all__ = ['run', 'run_graph']

dependency_cache_ctx_var = contextvars.ContextVar("dependency_cache")


class CacheUsage(Enum):
    SHARED = auto()
    INDEPENDENT = auto()


def set_new_context_dependency_cache():
    dependency_cache_ctx_var.set(DependencyCache())
    return dependency_cache_ctx_var.get()


def get_context_dependency_cache():
    try:
        return dependency_cache_ctx_var.get()
    except LookupError:
        return set_new_context_dependency_cache()


def convert_output_to_input(output_data):
    if output_data is None or output_data == (None,):
        return tuple()
    elif not isinstance(output_data, tuple):
        return output_data,
    else:
        return output_data


async def get_dependencies(
        dependency_cache: DependencyCache,
        dependency_names: List[str]
) -> Dict[str, Any]:
    return {
        name: await dependency_cache.call_dependency(name)
        for name in dependency_names
    }


async def execute_node(
        node: Node,
        branch_tracker: BranchTracker,
        input_data=tuple()
) -> None:
    loop = asyncio.get_running_loop()
    dependency_cache = get_context_dependency_cache()

    # Construct full input for the node.
    # This is positional arguments created from the output of the previous node,
    # as well as keyword arguments pulled from the dependency injector.
    dependencies = await get_dependencies(dependency_cache,
                                          node.get_dependencies())

    # Call the node.
    try:
        raw_node_output = await node(*input_data, **dependencies)
    except Exception:
        # Any exception skips everything below, so it effectively kills the
        # branch.  We can't make any assumptions, so we can't handle the
        # exception, except to keep track of the branch terminating.
        branch_tracker.remove_branch()
        raise

    # Process the return value.
    # The Matcher node requires the return value to have a certain form, and
    # the value used for branch matching should not be passed to the next node.
    output_data = node.get_output_data(raw_node_output)
    next_nodes = node.get_next_node(raw_node_output)

    if not next_nodes:
        # With no following node, this branch ends, so remove it from the
        # tracker to ensure the graph coroutine returns when all work is done.
        branch_tracker.remove_branch()
        return

    # Prepare positional input arguments for the trailing node(s).
    input_data = convert_output_to_input(output_data)

    # The first node kicked off is a continuation of this branch.
    # The rest, if any, are new branches that need to be tracked.
    add_branch = False
    for next_node in next_nodes:
        loop.create_task(execute_node(next_node, branch_tracker, input_data))
        if add_branch:
            branch_tracker.add_branch()
        add_branch = True


async def start_graph(
        first_node: Node,
        cache_usage: CacheUsage
) -> None:
    loop = asyncio.get_running_loop()
    branch_tracker = BranchTracker()

    if cache_usage == CacheUsage.INDEPENDENT:
        set_new_context_dependency_cache()

    loop.create_task(execute_node(first_node, branch_tracker))
    await branch_tracker.wait()


async def run_graph(
        graph: Union[str, Graph],
        start_node_name: str,
        cache_usage: CacheUsage = CacheUsage.SHARED
) -> None:
    """
    Execute the graph defined in the file starting at the specified node.

    :param graph: path from the current working directory to a graph file
        (currently only the Graphviz format is supported) OR a native graph
        class object
    :param start_node_name: name of the node (NOT type) in the graph to start
    :param cache_usage: if run from within another graph, whether to share the
        dependency cache with the parent graph or use its own
    :return: None
    """
    loop = asyncio.get_running_loop()
    if isinstance(graph, str):
        graph: Graph = await loop.run_in_executor(None, parse, graph)
    start_node: Node = graph.nodes[start_node_name]

    await loop.create_task(start_graph(start_node, cache_usage))


def run(
        graph: Union[str, Graph],
        start_node_name: str,
        cache_usage: CacheUsage = CacheUsage.SHARED
) -> None:
    """
    Execute the graph defined in the file starting at the specified node.

    :param graph: path from the current working directory to a graph file
        (currently only the Graphviz format is supported) OR a native graph
        class object
    :param start_node_name: name of the node (NOT type) in the graph to start
    :param cache_usage: if run from within another graph, whether to share the
        dependency cache with the parent graph or use its own
    :return: None
    """
    try:
        asyncio.run(run_graph(graph, start_node_name, cache_usage))
    except KeyboardInterrupt:
        pass
