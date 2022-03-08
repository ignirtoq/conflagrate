from typing import Type

from ..graph import (Node as ExecutionNode, MatcherNode as ExecutionMatcherNode,
                     Graph as ExecutionGraph)
from ..registration import get_nodetypes

__all__ = ['Graph', 'Node']


class Node:
    def __init__(self, *, type: str, branch: str = 'parallel', **attributes):
        self._name = None
        self._typename = type
        self._branching_strategy = branch
        self._attributes = attributes
        self._edges = []
        self._last_edge_attributes = {}

    def __call__(self, *_, **attributes):
        # To support the edge definition syntax
        #     source > destination (**edge_attributes)
        # in graph class definitions, we overload the node call definition
        # to capture these attributes locally.  When the edge is defined
        # in the comparison overload, we grab the attributes and replace
        # the dictionary with an empty one for the next usage in an edge
        # definition.
        self._last_edge_attributes = attributes
        return self

    def __gt__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        edge_attributes = other._last_edge_attributes
        other._last_edge_attributes = {}
        self._edges.append(Edge(other, **edge_attributes))


class Edge:
    def __init__(self, destination, **attributes):
        self.destination = destination
        self.attributes = attributes


class MetaGraph(type):
    def __new__(mcs, clsname, bases, classdict):
        display_nodes = {
            name: value
            for name, value in classdict.items()
            if isinstance(value, Node)
        }
        # Set the name on the display node for easier lookup when filling out
        # node edges.
        for name, value in display_nodes.items():
            value._name = name

        final_dict = {
            name: value for name, value in classdict.items()
            if not isinstance(value, Node)
        }
        final_dict['display_nodes'] = display_nodes

        return super().__new__(mcs, clsname, bases, final_dict)


def create_node(name: str, display_node: Node, nodetypes):
    typename = display_node._typename
    node_cls: Type[ExecutionNode] = (
        ExecutionMatcherNode
        if display_node._branching_strategy == 'matcher' else ExecutionNode)
    return node_cls(name, typename, nodetypes[typename],
                    [] if node_cls is ExecutionNode else {})


def add_edges_to_nodes(nodes, display_nodes):
    for name, display_node in display_nodes.items():
        node = nodes[name]
        for edge in display_node._edges:
            destination = nodes[edge.destination._name]
            if isinstance(node, ExecutionMatcherNode):
                node.edges[edge.attributes['value']] = destination
            else:
                node.edges.append(destination)


class Graph(ExecutionGraph, metaclass=MetaGraph):
    def __init__(self):
        nodetypes = get_nodetypes()
        nodes = {
            name: create_node(name, value, nodetypes)
            for name, value in self.display_nodes.items()
        }
        add_edges_to_nodes(nodes, self.display_nodes)
        super().__init__(nodes)
