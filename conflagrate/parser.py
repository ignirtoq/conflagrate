from collections import defaultdict
from dataclasses import dataclass, field
import pydot
from typing import Dict, List, Tuple, Type, Union

from .controlflow import BranchType
from .registration import MatcherNodeType, NodeType, get_nodetypes


MATCH_VALUE_ATTRIBUTE = 'value'
NODE_TYPE_ATTRIBUTE = 'type'


@dataclass
class Node:
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
        return [self.edges]


@dataclass
class MatcherNode(Node):
    def __hash__(self):
        return hash(self.name)

    def get_output_data(self, callable_output):
        return callable_output[1]

    def get_next_node(self, callable_output):
        return [self.edges[callable_output[0]]]


_nodetype_to_node_type: Dict[Type[NodeType], Type[Node]] = {
    NodeType: Node,
    MatcherNodeType: MatcherNode
}


@dataclass
class Graph:
    nodes: Dict[str, Node]


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
    typename = dot_node.get(NODE_TYPE_ATTRIBUTE)
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
    node_to_edge_dict: Dict[Node, Union[Node, Dict[str, Node]]] = (
        defaultdict(dict)
    )
    for dot_edge in dot_edges:
        source, destination = get_source_destination_nodes_from_edge(
            dot_edge, nodes)
        # if not check_input_output_datatypes_match(source, destination):
        #     raise ValueError(f'output type of "{source.typename}" does not '
        #                      f'match input type of "{destination.typename}"\n'
        #                      f'output: {source.nodetype.output_datatype}\n'
        #                      f'input: {destination.nodetype.input_datatype}')
        if source.nodetype.branchtype == BranchType.matcher:
            match_value = dot_edge.get(MATCH_VALUE_ATTRIBUTE)
            node_to_edge_dict[source][match_value] = destination
        else:
            node_to_edge_dict[source] = destination

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


def check_input_output_datatypes_match(
        source: Node,
        destination: Node
) -> bool:
    return (source.nodetype.output_datatype ==
            destination.nodetype.input_datatype)


def parse(graph_filename):
    dot_graph = pydot.graph_from_dot_file(graph_filename)[0]
    return convert_from_dot_graph(dot_graph)
