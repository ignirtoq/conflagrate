from typing import Union

from .parser import Node, parse, Graph

__all__ = ['run']


def run(graph_filename: str, start_node_name: str):
    graph: Graph = parse(graph_filename)
    node: Union[Node, None] = graph.nodes[start_node_name]
    input_data = tuple()

    while node is not None:
        raw_node_output = node(*input_data)

        if not node.edges:
            node = None
            continue

        input_data = node.get_output_data(raw_node_output)
        if input_data is None or input_data == (None,):
            input_data = tuple()
        elif not isinstance(input_data, tuple):
            input_data = (input_data,)

        node = node.get_next_node(raw_node_output)
