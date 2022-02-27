import asyncio
from typing import Union

from .asyncutils import BranchTracker
from .parser import Graph, Node, parse

__all__ = ['run']


def convert_output_to_input(output_data):
    if output_data is None or output_data == (None,):
        return tuple()
    elif not isinstance(output_data, tuple):
        return output_data,
    else:
        return output_data


async def execute_node(
        node: Node,
        branch_tracker: BranchTracker,
        input_data=tuple()
) -> None:
    loop = asyncio.get_running_loop()

    raw_node_output = await node(*input_data)

    if not node.has_next_node():
        branch_tracker.remove_branch()
        return

    output_data = node.get_output_data(raw_node_output)
    input_data = convert_output_to_input(output_data)

    next_nodes = node.get_next_node(raw_node_output)
    add_branch = False
    for next_node in next_nodes:
        loop.create_task(execute_node(next_node, branch_tracker, input_data))
        if add_branch:
            branch_tracker.add_branch()
        add_branch = True


async def start_graph(
        first_node: Node
) -> None:
    loop = asyncio.get_running_loop()
    branch_tracker = BranchTracker()
    loop.create_task(execute_node(first_node, branch_tracker))
    await branch_tracker.wait()


def run(
        graph_filename: str,
        start_node_name: str
) -> None:
    graph: Graph = parse(graph_filename)
    start_node: Union[Node, None] = graph.nodes[start_node_name]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(start_graph(start_node))
    except KeyboardInterrupt:
        loop.close()
