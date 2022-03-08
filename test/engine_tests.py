import pytest
from unittest import mock

from conflagrate.asyncutils import BranchTracker
from conflagrate.dependencies import DependencyCache
from conflagrate.engine import (convert_output_to_input, get_dependencies,
                                execute_node, get_context_dependency_cache,
                                run_graph, CacheUsage)
from conflagrate.graph import Node, MatcherNode


@pytest.fixture
def branch_tracker():
    return BranchTracker()


@pytest.fixture
def mock_branch_tracker():
    return mock.Mock()


@pytest.fixture
def dependency_cache():
    return DependencyCache()


@pytest.fixture
def node():
    return Node('test', 'test', mock.AsyncMock())


@pytest.fixture
def matcher_node():
    return MatcherNode('matcher_test', 'match_test', mock.AsyncMock())


def test_convert_output_to_input_None():
    input_data = convert_output_to_input(None)
    assert input_data == ()


def test_convert_output_to_input_None_tuple():
    input_data = convert_output_to_input((None,))
    assert input_data == ()


def test_convert_output_to_input_scalar():
    input_data = convert_output_to_input(0)
    assert input_data == (0,)

    input_data = convert_output_to_input(False)
    assert input_data == (False,)

    sentinel = object()
    input_data = convert_output_to_input(sentinel)
    assert input_data == (sentinel,)

    input_data = convert_output_to_input(1)
    assert input_data == (1,)


def test_convert_output_to_input_tuple():
    output = (1, "abc", object())
    input_data = convert_output_to_input(output)
    assert input_data == output

    output = (None, 1)
    input_data = convert_output_to_input(output)
    assert input_data == output


@pytest.mark.asyncio
async def test_get_dependencies_none(dependency_cache):
    dependency_cache.call_dependency = mock.Mock()

    dep_dict = await get_dependencies(dependency_cache, [])

    dependency_cache.call_dependency.assert_not_called()
    assert not dep_dict


@pytest.mark.asyncio
async def test_get_dependencies_with_list(dependency_cache):
    dep_names = ['first', 'second', 'third']
    dep_values = [1, 2, 3]
    dependency_cache.call_dependency = mock.AsyncMock(side_effect=dep_values)

    dep_dict = await get_dependencies(dependency_cache, dep_names)

    assert dep_dict == dict(zip(dep_names, dep_values))


@pytest.mark.asyncio
async def test_execute_node_no_next_node(node, mock_branch_tracker):
    with mock.patch('conflagrate.engine.get_dependencies',
                    mock.AsyncMock(return_value={})) as get_deps, (
            mock.patch('asyncio.get_running_loop')) as mock_loop:
        await execute_node(node, mock_branch_tracker)

    node.nodetype.assert_called_with()
    mock_branch_tracker.remove_branch.assert_called_once()
    mock_branch_tracker.add_branch.assert_not_called()
    mock_loop.return_value.create_task.assert_not_called()


@pytest.mark.asyncio
async def test_execute_node_one_next_node(node, mock_branch_tracker):
    node.edges = [node]
    with mock.patch('conflagrate.engine.get_dependencies',
                    mock.AsyncMock(return_value={})) as get_deps, (
            mock.patch('asyncio.get_running_loop')) as mock_loop:
        await execute_node(node, mock_branch_tracker)

    node.nodetype.assert_called_with()
    mock_branch_tracker.remove_branch.assert_not_called()
    mock_branch_tracker.add_branch.assert_not_called()
    mock_loop.return_value.create_task.assert_called_once()


@pytest.mark.asyncio
async def test_execute_node_two_next_nodes(node, mock_branch_tracker):
    node.edges = [node, node]
    with mock.patch('conflagrate.engine.get_dependencies',
                    mock.AsyncMock(return_value={})) as get_deps, (
            mock.patch('asyncio.get_running_loop')) as mock_loop:
        await execute_node(node, mock_branch_tracker)

    node.nodetype.assert_called_with()
    mock_branch_tracker.remove_branch.assert_not_called()
    mock_branch_tracker.add_branch.assert_called_once()
    mock_loop.return_value.create_task.assert_called()
    assert len(mock_loop.return_value.create_task.mock_calls) == 2


@pytest.mark.asyncio
async def test_start_graph_shared_cache():
    outer_dependency_cache = get_context_dependency_cache()
    inner_dependency_cache = []

    def mock_execute(_, branch_tracker: BranchTracker):
        inner_dependency_cache.append(get_context_dependency_cache())
        branch_tracker.remove_branch()

    mock_execute = mock.AsyncMock(side_effect=mock_execute)
    with mock.patch('conflagrate.engine.parse'), (
            mock.patch('conflagrate.engine.execute_node', mock_execute)):
        await run_graph('test', 'test')

    assert outer_dependency_cache == inner_dependency_cache[0]


@pytest.mark.asyncio
async def test_start_graph_independent_cache():
    outer_dependency_cache = get_context_dependency_cache()
    inner_dependency_cache = []

    def mock_execute(_, branch_tracker: BranchTracker):
        inner_dependency_cache.append(get_context_dependency_cache())
        branch_tracker.remove_branch()

    mock_execute = mock.AsyncMock(side_effect=mock_execute)
    with mock.patch('conflagrate.engine.parse'), (
            mock.patch('conflagrate.engine.execute_node', mock_execute)):
        await run_graph('test', 'test', CacheUsage.INDEPENDENT)

    assert outer_dependency_cache != inner_dependency_cache[0]
