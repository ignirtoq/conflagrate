import asyncio
from typing import Any, Dict, List, Union

from .asyncutils import BranchTracker
from .dependencies import DependencyCache
from .graph import Graph, Node
from .parser import parse

__all__ = ['run']


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
        dependency_cache: DependencyCache,
        input_data=tuple()
) -> None:
    loop = asyncio.get_running_loop()

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
        loop.create_task(execute_node(next_node, branch_tracker,
                                      dependency_cache, input_data))
        if add_branch:
            branch_tracker.add_branch()
        add_branch = True


async def start_graph(
        first_node: Node,
        dependency_cache: DependencyCache
) -> None:
    loop = asyncio.get_running_loop()
    branch_tracker = BranchTracker()
    loop.create_task(execute_node(first_node, branch_tracker, dependency_cache))
    await branch_tracker.wait()


def run(
        graph_filename: str,
        start_node_name: str
) -> None:
    """
    Execute the graph defined in the file starting at the specified node.

    :param graph_filename: path from the current working directory to the
    graph file (currently only the Graphviz format is supported)
    :param start_node_name: name of the node (NOT type) in the graph to start
    :return: None
    """
    graph: Graph = parse(graph_filename)
    start_node: Union[Node, None] = graph.nodes[start_node_name]
    dependency_cache = DependencyCache()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(start_graph(start_node, dependency_cache))
    except KeyboardInterrupt:
        loop.close()
