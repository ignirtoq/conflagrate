import asyncio
from enum import Enum, auto
from functools import partial
from typing import Callable

__all__ = ['BlockingBehavior']


class BranchTracker:
    def __init__(self, num_starting_branches=1):
        self.branches = num_starting_branches
        self._future = asyncio.Future()

    def _check_done(self):
        if self._future.done():
            raise ValueError("all branches have already terminated")

    def add_branch(self):
        self._check_done()
        self.branches += 1

    def remove_branch(self):
        self._check_done()
        self.branches -= 1
        if self.branches <= 0:
            self._future.set_result(None)

    async def wait(self):
        await self._future


class BlockingBehavior(Enum):
    """
    Blocking behavior of the decorated node type definition function.
    By default, all regular functions are assumed BLOCKING and all coroutine
    functions are assumed NON_BLOCKING.

    Only use the NON_BLOCKING value on functions that do not block the execution
    thread in which they are called under ANY possible code path.
    """
    BLOCKING = auto()
    NON_BLOCKING = auto()


def ensure_awaitable(
        function: Callable,
        blocking_behavior: BlockingBehavior,
        *args,
        **kwargs
):
    if asyncio.iscoroutinefunction(function):
        return function(*args, **kwargs)
    else:
        return make_awaitable(function, blocking_behavior, *args, **kwargs)


async def make_awaitable(
        function: Callable,
        blocking_behavior: BlockingBehavior,
        *args,
        **kwargs
):
    """
    Builds an awaitable object out of the function and arguments that returns
    the actual return value of the object, unlike loop.call_soon().
    If the callable is a blocking function (the default assumed), then it is
    awaited with loop.run_in_executor() since that function *DOES* return the
    return value.
    If the callable is a non-blocking function, it schedules it on the event
    loop along with a future that is set with the result.  The future is awaited
    and the result is returned.

    :param function: Function to be executed on the loop (coroutine or
    otherwise).
    :param blocking_behavior: Flag to indicate whether the function is blocking
    or non-blocking.
    :param args: Positional arguments for the function.
    :param kwargs: Keyword arguments for the function.
    :return: An awaitable object to retrieve the output of the function upon
    completion.
    """
    loop = asyncio.get_running_loop()
    future = asyncio.Future()
    wrapped_function = partial(function, *args, **kwargs)
    if blocking_behavior is BlockingBehavior.BLOCKING:
        return await loop.run_in_executor(None, wrapped_function)

    loop.call_soon(call_and_set_future, future, wrapped_function)
    return await future


def call_and_set_future(
        future: asyncio.Future,
        function: Callable
):
    try:
        return_value = function()
    except Exception as e:
        future.set_exception(e)
    else:
        future.set_result(return_value)
