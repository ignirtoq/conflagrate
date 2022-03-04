import asyncio
from enum import Enum, auto
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Collection, Dict, List, Tuple

__all__ = ['CacheSupport', 'dependency']


class CacheSupport(Enum):
    """
    Parameter describing the circumstances under which a dependency function's
    output value can be cached.

    CACHE_PERMANENTLY: (Default) Call the dependency function only once and
        store the returned value forever.  This is useful for dependencies that
        only need to be invoked once, such as reading a configuration file.
    NEVER_CACHE: Call the dependency function each time it is needed by a node.
        This includes as a direct dependency or in a hierarchy.  This is useful
        for dependencies that provide a time-limited interface, such as
        external API interfaces that have an authentication session that can
        expire.
    """
    CACHE_PERMANENTLY = auto()
    NEVER_CACHE = auto()


@dataclass
class Dependency:
    name: str
    dependencies: Tuple[str]
    callable: Callable
    cache_support: CacheSupport

    def __hash__(self):
        return hash(self.name)

    def __call__(self, *args, **kwargs):
        return self.callable(*args, **kwargs)


class DependencyCache:
    def __init__(self):
        self._dependency_registry: Dict[str, Dependency] = _dependencies.copy()
        self._dependency_cache: Dict[Dependency, Any] = {}

    async def call_dependency(self, name):
        if self._is_in_cache(name):
            return self._get_from_cache(name)

        dep = self._get_dependency(name)
        args = [await self.call_dependency(name) for name in dep.dependencies]

        result = await dep(*args)
        self._save_in_cache(name, result)
        return result

    def _get_dependency(self, name) -> Dependency:
        return self._dependency_registry[name]

    def _get_subdependencies(self, dependency: Dependency) -> List[Dependency]:
        return [self._get_dependency(subdep)
                for subdep in dependency.dependencies]

    def _is_in_cache(self, name):
        return name in self._dependency_cache

    def _get_from_cache(self, name):
        return self._dependency_cache[name]

    def _save_in_cache(self, name, value):
        if self._is_cachable(name):
            self._dependency_cache[name] = value

    def _is_cachable(self, name):
        return (self._get_dependency(name).cache_support is not
                CacheSupport.NEVER_CACHE)


_dependencies: Dict[str, Dependency] = {}


def get_dependency(function):
    return _dependencies[function.__name__]


def get_direct_dependency_names(function) -> Tuple[str]:
    signature = inspect.signature(function)
    return tuple([name for name in signature.parameters])


def get_direct_dependencies(dependency_names: Collection[str]):
    return [_dependencies[name] for name in dependency_names]


def get_recursive_dependencies(dependency: Dependency) -> List[Dependency]:
    all_deps = get_direct_dependencies(dependency.dependencies)
    for dep in all_deps.copy():
        all_deps.extend(get_recursive_dependencies(dep))
    return all_deps


def dependency(arg, /):
    """
    Declare the coroutine function is a dependency provider.

    Some resources or interfaces are needed by few nodes that are not efficient
    or elegant to pass through the whole graph as function arguments and return
    values.  "Dependencies" are a mechanism to provide these specially used
    externalities.

    A node type that has an external dependency declares it in its function
    signature as a keyword-only argument.  The name of that argument is then
    matched to the name of a function decorated with the dependency decorator.
    At the point that a node of that type is to be invoked, all of its
    dependencies are fetched from the dependency cache.  If the dependency
    function has never been called, it is called, and its return value is
    stored in the cache and provided to the node through its keyword argument.

    Dependencies can declare their own dependencies as regular
    (positional-or-keyword) arguments in their own signature.  In this way,
    data and interfaces common to multiple dependencies can be efficiently
    shared.  For example, a "config()" dependency can load an entire
    configuration specification from file, while another dependency
    "username(config)" can provide just the username out of the configuration.

    The dependency decorator can be provided a CacheSupport argument to specify
    whether it can be cached.  See the CacheSupport class for details.

    :param arg: When used as a decorator without arguments, this is the
        decorated function.  When called with arguments this is the cache
        support parameter.  See the CacheSupport enum.
    :return: Decorated function.
    """
    if inspect.isfunction(arg) and not inspect.iscoroutinefunction(arg):
        raise TypeError(f'dependency "{arg.__name__}" must be a coroutine '
                        f'function (must be defined with "async def")')

    if inspect.isfunction(arg):
        called_with_function_argument = True
        cache_support = CacheSupport.CACHE_PERMANENTLY
    else:
        called_with_function_argument = False
        cache_support = arg

    def decorator(function):
        name = function.__name__
        if name in _dependencies:
            raise ValueError(f'dependency already defined named "{name}"')
        if not asyncio.iscoroutinefunction(function):
            raise TypeError(f'dependency "{name}" must be a coroutine function '
                            f'(must be defined with "async def")')

        subdependencies = get_direct_dependency_names(function)
        _dependencies[name] = Dependency(name, subdependencies, function,
                                         cache_support)
        return function

    if called_with_function_argument:
        return decorator(arg)
    else:
        return decorator
