import asyncio
from functools import partial
from typing import Callable


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


def make_awaitable(callable: Callable, *args, **kwargs):
    """
    Builds an awaitable object out of the callable and arguments.
    If the callable is a coroutine function, it calls the function as usual.
    If the callable is a regular function, it schedules it on the event loop
    along with a future that is set with the result.  The future is returned

    :param callable: Function to be executed on the loop (coroutine or
    otherwise).
    :param args: Positional arguments for the function.
    :param kwargs: Keyword arguments for the function.
    :return: An awaitable object to retrieve the output of the function upon
    completion.
    """
    if asyncio.iscoroutinefunction(callable):
        return callable(*args, **kwargs)

    loop = asyncio.get_running_loop()
    future = asyncio.Future()
    wrapped_function = partial(callable, *args, **kwargs)
    loop.call_soon(call_and_set_future, future, wrapped_function)
    return future


def call_and_set_future(
        future: asyncio.Future,
        callable: Callable
):
    future.set_result(callable())
