import pytest
from unittest import mock

from conflagrate import BranchingStrategy, BlockingBehavior
from conflagrate.graph import NodeType, Node


@pytest.fixture
def node_type():
    return NodeType(mock.Mock(), BranchingStrategy.parallel,
                    BlockingBehavior.BLOCKING, (), ())


@pytest.fixture
def node():
    return Node('test', 'test', mock.Mock())


@mock.patch('conflagrate.graph.ensure_awaitable')
def test_NodeType_call(ensure_awaitable, node_type):
    node_type(1, "", b=2)
    ensure_awaitable.assert_called_with(node_type.callable,
                                        node_type.blocking_behavior, 1, "", b=2)


def test_NodeType_get_dependencies_no_kwargs(node_type):
    def my_func(posarg1, posarg2, *args) -> None:
        pass
    node_type.callable = my_func

    assert node_type.get_dependencies() == []


def test_NodeType_get_dependencies_with_kwargs(node_type):
    def my_func(posarg1, posarg2, *args, kwarg1, kwarg2=None) -> None:
        pass
    node_type.callable = my_func

    assert node_type.get_dependencies() == ['kwarg1', 'kwarg2']


def test_Node_hash(node):
    assert hash(node) == hash(node.name)


def test_Node_call(node):
    node(1, "", b=2)
    node.nodetype.assert_called_with(1, "", b=2)


def test_Node_get_output_data(node):
    mock_arg = object()
    return_value = node.get_output_data(mock_arg)
    assert return_value == mock_arg
