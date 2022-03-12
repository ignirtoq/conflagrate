import pydot
from typing import Type

from ..graph import (Node as ExecutionNode, MatcherNode as ExecutionMatcherNode,
                     Graph as ExecutionGraph)
from ..registration import get_nodetypes

__all__ = ['Graph', 'Node']


class Node:
    def __init__(self, *, type: str = None, branch: str = None,
                 **attributes):
        self._name = None
        self._typename = type
        default_branch = 'parallel' if type is not None else None
        self._branching_strategy = branch if branch else default_branch
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
        self._edges.append(Edge(self, other, **edge_attributes))


class Edge:
    def __init__(self, source, destination, **attributes):
        self.source = source
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
        # skip display nodes that don't map to execution nodes
        if name not in nodes:
            continue
        node = nodes[name]
        for edge in display_node._edges:
            destination = nodes[edge.destination._name]
            if isinstance(node, ExecutionMatcherNode):
                node.edges[edge.attributes.get('value')] = destination
            else:
                node.edges.append(destination)


class Graph(ExecutionGraph, metaclass=MetaGraph):
    def __init__(self):
        nodetypes = get_nodetypes()
        nodes = {
            name: create_node(name, display_node, nodetypes)
            for name, display_node in self.display_nodes.items()
            if display_node._typename is not None
        }
        add_edges_to_nodes(nodes, self.display_nodes)
        super().__init__(nodes)

    @classmethod
    def _to_dot_object(cls) -> pydot.Dot:
        graph = pydot.Dot(cls.__name__)
        nodes = {name: cls._display_node_to_pydot_node(name, node)
                 for name, node in cls.display_nodes.items()}
        for name, node in cls.display_nodes.items():
            graph.add_node(nodes[name])
            for edge in node._edges:
                gv_edge = pydot.Edge(edge.source._name, edge.destination._name,
                                     **edge.attributes)
                graph.add_edge(gv_edge)

        return graph

    @classmethod
    def _display_node_to_pydot_node(cls, name, node: Node):
        attributes = node._attributes.copy()
        if node._typename is not None:
            attributes['type'] = node._typename
        if node._branching_strategy is not None:
            attributes['branch'] = node._branching_strategy
        return pydot.Node(name, **attributes)

    def to_graphviz(self, filename: str):
        with open(filename, 'wb') as f:
            f.write(self._to_dot_object().create_dot())

    def to_png(self, filename: str):
        with open(filename, 'wb') as f:
            f.write(self._to_dot_object().create_png())
