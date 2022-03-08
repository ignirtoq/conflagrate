import pydot
from typing import Dict, List, Tuple, Type, Union

from ..controlflow import BranchingStrategy
from ..graph import Graph, MatcherNode, MatcherNodeType, Node, NodeType
from ..registration import get_nodetypes

MATCH_VALUE_ATTRIBUTE = 'value'
NODE_TYPE_ATTRIBUTE = 'type'

_nodetype_to_node_type: Dict[Type[NodeType], Type[Node]] = {
    NodeType: Node,
    MatcherNodeType: MatcherNode
}


def convert_from_dot_graph(dot_graph: pydot.Graph):
    dot_nodes = dot_graph.get_nodes()
    dot_edges = dot_graph.get_edges()

    nodetypes = get_nodetypes()

    nodes: Dict[str, Node] = {
        node.get_name(): convert_from_dot_node(node, nodetypes)
        for node in dot_nodes
        if node.get(NODE_TYPE_ATTRIBUTE) is not None
    }
    add_edges_to_nodes(dot_edges, nodes)

    return Graph(nodes)


def convert_from_dot_node(
        dot_node: pydot.Node,
        nodetypes: Dict[str, NodeType]
) -> Node:
    name = dot_node.get_name()
    typename = dot_node.get(NODE_TYPE_ATTRIBUTE).strip('"')
    try:
        nodetype: NodeType = nodetypes[typename]
    except KeyError:
        raise ValueError(f'no nodetype associated with graphed node type '
                         f'"{typename}"')
    return _nodetype_to_node_type[type(nodetype)](name, typename, nodetype)


def add_edges_to_nodes(
        dot_edges: List[pydot.Edge],
        nodes: Dict[str, Node]
) -> None:
    node_to_edge_dict: Dict[Node, Union[List[Node], Dict[str, Node]]] = {}

    for node in nodes.values():
        if node.nodetype.branching_strategy == BranchingStrategy.matcher:
            node_to_edge_dict[node] = {}
        else:
            node_to_edge_dict[node] = []

    for dot_edge in dot_edges:
        source, destination = get_source_destination_nodes_from_edge(
            dot_edge, nodes)
        # TODO: Check call signature compatibilities.
        #   We want to fail-fast at parsing so the developer doesn't get
        #   surprised when the application goes down a rarely used branch
        #   and hits a TypeError due to incompatible signature.
        #   This is non-trivial and needs care to do right.
        if source.nodetype.branching_strategy == BranchingStrategy.matcher:
            match_value = dot_edge.get(MATCH_VALUE_ATTRIBUTE)
            node_to_edge_dict[source][match_value] = destination
        else:
            node_to_edge_dict[source].append(destination)

    for node, edges in node_to_edge_dict.items():
        node.edges = edges


def get_source_destination_nodes_from_edge(
        dot_edge: pydot.Edge,
        nodes: Dict[str, Node]
) -> Tuple[Node, Node]:
    source_name = dot_edge.get_source()
    destination_name = dot_edge.get_destination()

    try:
        source = nodes[source_name]
    except KeyError:
        raise ValueError(f'no node definition found for edge source '
                         f'"{source_name}"')
    try:
        destination = nodes[destination_name]
    except KeyError:
        raise ValueError(f'no node definition found for edge destination "'
                         f'{destination_name}')

    return source, destination


def parse(graph_filename):
    dot_graph = pydot.graph_from_dot_file(graph_filename)[0]
    return convert_from_dot_graph(dot_graph)
