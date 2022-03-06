import pytest
import unittest.mock as mock

from conflagrate.dependencies import (CacheSupport, Dependency, DependencyCache,
                                      dependency as con_dependency)


@pytest.fixture
def dependency():
    return Dependency('test_name', tuple(), mock.Mock(),
                      CacheSupport.CACHE_PERMANENTLY)


@pytest.fixture
def dependency_cache(dependency):
    with mock.patch('conflagrate.dependencies._dependencies'):
        cache = DependencyCache()
    cache._dependency_cache = mock.MagicMock()
    cache._is_in_cache = mock.Mock(return_value=False)
    cache._get_dependency = mock.Mock(return_value=dependency)
    cache._get_from_cache = mock.Mock()
    return cache


def test_Dependency_hash(dependency: Dependency):
    assert hash(dependency) == hash(dependency.name)


def test_Dependency_call(dependency: Dependency):
    dependency(1, 2, b=3)
    dependency.callable.assert_called_with(1, 2, b=3)


@pytest.mark.asyncio
async def test_DependencyCache_call_dependency_cached(
        dependency_cache, dependency):
    dependency_cache._is_in_cache.return_value = True

    await dependency_cache.call_dependency(dependency.name)

    dependency_cache._is_in_cache.assert_called_with(dependency.name)
    dependency_cache._get_dependency.assert_not_called()


@pytest.mark.asyncio
async def test_DependencyCache_call_dependency_not_cached_no_subdeps(
        dependency_cache, dependency):
    dependency.callable = mock.AsyncMock()

    call_dependency = dependency_cache.call_dependency
    dependency_cache.call_dependency = mock.AsyncMock()

    await call_dependency(dependency.name)

    dependency_cache._is_in_cache.assert_called_with(dependency.name)
    dependency_cache._get_from_cache.assert_not_called()
    dependency_cache.call_dependency.assert_not_awaited()
    dependency.callable.assert_awaited_with()
    dependency_cache._dependency_cache.__setitem__.assert_called_with(
        dependency.name, dependency.callable.return_value)


@pytest.mark.asyncio
async def test_DependencyCache_call_dependency_not_cached_subdeps(
        dependency_cache, dependency):
    dependency.callable = mock.AsyncMock()
    dependency.dependencies = ('test_dep',)

    call_dependency = dependency_cache.call_dependency
    dependency_cache.call_dependency = mock.AsyncMock()

    await call_dependency(dependency.name)

    dependency_cache._is_in_cache.assert_called_with(dependency.name)
    dependency_cache._get_from_cache.assert_not_called()
    dependency_cache.call_dependency.assert_awaited_with(
        dependency.dependencies[0])
    dependency.callable.assert_awaited_with(
        dependency_cache.call_dependency.return_value)
    dependency_cache._dependency_cache.__setitem__.assert_called_with(
        dependency.name, dependency.callable.return_value)


def test_dependency_with_function():
    with pytest.raises(TypeError):
        con_dependency(lambda: None)


@mock.patch('conflagrate.dependencies._dependencies')
def test_dependency_with_already_registered_function(_dependencies):
    _dependencies.__contains__.return_value = True

    with pytest.raises(ValueError):
        @con_dependency
        async def my_dep():
            pass


@mock.patch('conflagrate.dependencies._dependencies')
def test_dependency_registration(_dependencies):
    _dependencies.__contains__.return_value = False

    @con_dependency
    async def my_dep():
        pass

    _dependencies.__setitem__.assert_called_once()
    _dependencies.__setitem__.assert_called_with('my_dep', mock.ANY)
    call = _dependencies.__setitem__.mock_calls[0]
    pos_or_kwargs = call[1]
    dep = pos_or_kwargs[1]
    assert dep.name == 'my_dep'
    assert dep.dependencies == tuple()
    assert dep.callable == my_dep
    assert dep.cache_support == CacheSupport.CACHE_PERMANENTLY


@mock.patch('conflagrate.dependencies._dependencies')
def test_dependency_registration_with_cache_flag(_dependencies):
    _dependencies.__contains__.return_value = False

    @con_dependency(CacheSupport.NEVER_CACHE)
    async def my_dep():
        pass

    _dependencies.__setitem__.assert_called_once()
    _dependencies.__setitem__.assert_called_with('my_dep', mock.ANY)
    call = _dependencies.__setitem__.mock_calls[0]
    pos_or_kwargs = call[1]
    dep = pos_or_kwargs[1]
    assert dep.name == 'my_dep'
    assert dep.dependencies == tuple()
    assert dep.callable == my_dep
    assert dep.cache_support == CacheSupport.NEVER_CACHE
