import asyncio
import pytest
import unittest.mock as mock

from conflagrate.asyncutils import (BlockingBehavior, BranchTracker,
                                    call_and_set_future, ensure_awaitable,
                                    make_awaitable)


@pytest.fixture
def branch_tracker():
    with mock.patch('asyncio.Future'):
        branch_tracker = BranchTracker()
        branch_tracker._future.done.return_value = False
    return branch_tracker


@pytest.fixture
def mock_func():
    return mock.Mock(return_value=mock.Mock())


@pytest.fixture
def mock_future():
    return mock.AsyncMock()


@pytest.fixture
def mock_loop():
    loop = mock.Mock()
    loop.run_in_executor = mock.AsyncMock()
    return loop


def test_branch_tracker_add_branch_not_done(branch_tracker):
    assert branch_tracker.branches == 1
    branch_tracker.add_branch()
    assert branch_tracker.branches == 2


def test_branch_tracker_add_branch_done(branch_tracker):
    branch_tracker._future.done.return_value = True
    with pytest.raises(ValueError):
        branch_tracker.add_branch()


def test_branch_tracker_remove_last_branch(branch_tracker):
    branch_tracker.remove_branch()
    branch_tracker._future.set_result.assert_called()


def test_branch_tracker_remove_not_last_branch(branch_tracker):
    branch_tracker.branches = 2
    branch_tracker.remove_branch()
    branch_tracker._future.set_result.assert_not_called()
    assert branch_tracker.branches == 1


@mock.patch('asyncio.iscoroutinefunction', return_value=True)
def test_ensure_awaitable_coroutine(mock_iscoroutine, mock_func):
    ensure_awaitable(mock_func, BlockingBehavior.NON_BLOCKING, None, 1, a=2)
    mock_iscoroutine.assert_called_with(mock_func)
    mock_func.assert_called_with(None, 1, a=2)


@mock.patch('conflagrate.asyncutils.make_awaitable')
@mock.patch('asyncio.iscoroutinefunction', return_value=False)
def test_ensure_awaitable_function(mock_iscoroutine, mock_await, mock_func):
    ensure_awaitable(mock_func, BlockingBehavior.NON_BLOCKING, None, 1, a=2)
    mock_iscoroutine.assert_called_with(mock_func)
    mock_await.assert_called_with(mock_func, BlockingBehavior.NON_BLOCKING,
                                  None, 1, a=2)


@pytest.mark.asyncio
async def test_make_awaitable_blocking(monkeypatch, mock_loop, mock_future):
    monkeypatch.setattr(asyncio, 'Future', mock_future)
    monkeypatch.setattr(asyncio, 'get_running_loop',
                        mock.Mock(return_value=mock_loop))
    await make_awaitable(lambda: None, BlockingBehavior.BLOCKING)
    mock_loop.run_in_executor.assert_awaited()
    mock_future.assert_not_awaited()


@pytest.mark.asyncio
async def test_make_awaitable_nonblocking(monkeypatch, mock_loop, mock_future):
    monkeypatch.setattr(asyncio, 'Future', mock_future)
    monkeypatch.setattr(asyncio, 'get_running_loop',
                        mock.Mock(return_value=mock_loop))
    await make_awaitable(lambda: None, BlockingBehavior.NON_BLOCKING)
    mock_loop.run_in_executor.assert_not_awaited()
    mock_future.assert_awaited()


def test_call_and_set_future(mock_func, mock_future):
    call_and_set_future(mock_future, mock_func)

    mock_func.assert_called_with()
    mock_future.set_result.assert_called_with(mock_func.return_value)
    mock_future.set_exception.assert_not_called()


def test_call_raises(mock_func, mock_future):
    exc = TypeError('test exception')
    mock_func.side_effect = exc

    call_and_set_future(mock_future, mock_func)

    mock_func.assert_called_with()
    mock_future.set_exception.assert_called_with(exc)
    mock_future.set_result.assert_not_called()
