import asyncio
from enum import Enum, auto
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Collection, Dict, List, Tuple

__all__ = ['CacheSupport', 'dependency']


class CacheSupport(Enum):
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
