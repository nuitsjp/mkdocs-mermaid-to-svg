"""Performance profiling utilities."""

import cProfile
import functools
import io
import pstats
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, ParamSpec, TypeVar, overload

P = ParamSpec("P")
R = TypeVar("R")


class ProfileResult:
    """Container for profiling results."""

    def __init__(
        self,
        elapsed_time: float,
        stats: pstats.Stats | None = None,
    ) -> None:
        """Initialize ProfileResult.

        Parameters
        ----------
        elapsed_time : float
            Elapsed time in seconds
        stats : pstats.Stats | None
            cProfile statistics object
        """
        self.elapsed_time = elapsed_time
        self.stats = stats

    def print_stats(
        self,
        *,
        sort_by: str = "cumulative",
        limit: int = 20,
    ) -> None:
        """Print profiling statistics.

        Parameters
        ----------
        sort_by : str
            Sort criteria for stats (cumulative, time, calls, etc.)
        limit : int
            Number of top functions to show
        """
        if self.stats:
            print(f"\nTotal elapsed time: {self.elapsed_time:.4f} seconds")
            self.stats.sort_stats(sort_by).print_stats(limit)
        else:
            print(f"Elapsed time: {self.elapsed_time:.4f} seconds")

    def save_stats(self, filepath: str | Path) -> None:
        """Save profiling statistics to file.

        Parameters
        ----------
        filepath : str | Path
            Path to save the stats file
        """
        if self.stats:
            self.stats.dump_stats(str(filepath))


@contextmanager
def profile_context(
    *,
    enabled: bool = True,
    print_stats: bool = True,
    sort_by: str = "cumulative",
    limit: int = 20,
) -> Iterator[ProfileResult]:
    """Context manager for profiling code blocks.

    Parameters
    ----------
    enabled : bool
        Whether profiling is enabled
    print_stats : bool
        Whether to print stats after profiling
    sort_by : str
        Sort criteria for stats
    limit : int
        Number of top functions to show

    Yields
    ------
    ProfileResult
        Profiling results object

    Examples
    --------
    >>> with profile_context() as prof:
    ...     # Code to profile
    ...     time.sleep(0.1)
    >>> print(f"Took {prof.elapsed_time:.2f} seconds")
    """
    if not enabled:
        start_time = time.perf_counter()
        result = ProfileResult(0)
        yield result
        result.elapsed_time = time.perf_counter() - start_time
        return

    profiler = cProfile.Profile()
    start_time = time.perf_counter()

    profiler.enable()
    result = ProfileResult(0)

    try:
        yield result
    finally:
        profiler.disable()
        elapsed_time = time.perf_counter() - start_time

        # Create stats
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s)

        result.elapsed_time = elapsed_time
        result.stats = stats

        if print_stats:
            result.print_stats(sort_by=sort_by, limit=limit)


@overload
def profile(
    func: Callable[P, R],
) -> Callable[P, R]:
    """Profile a function (when used without arguments)."""
    ...


@overload
def profile(
    *,
    enabled: bool = True,
    print_stats: bool = True,
    sort_by: str = "cumulative",
    limit: int = 20,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Profile a function with options."""
    ...


def profile(
    func: Callable[P, R] | None = None,
    *,
    enabled: bool = True,
    print_stats: bool = True,
    sort_by: str = "cumulative",
    limit: int = 20,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for profiling functions.

    Parameters
    ----------
    func : Callable | None
        Function to profile (when used without parentheses)
    enabled : bool
        Whether profiling is enabled
    print_stats : bool
        Whether to print stats after each call
    sort_by : str
        Sort criteria for stats
    limit : int
        Number of top functions to show

    Returns
    -------
    Callable
        Decorated function

    Examples
    --------
    >>> @profile
    ... def slow_function():
    ...     time.sleep(0.1)
    ...     return 42

    >>> @profile(enabled=False)
    ... def fast_function():
    ...     return 1 + 1

    >>> @profile(sort_by="time", limit=10)
    ... def complex_function():
    ...     # Complex logic here
    ...     pass
    """

    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not enabled:
                return f(*args, **kwargs)

            with profile_context(
                enabled=True,
                print_stats=print_stats,
                sort_by=sort_by,
                limit=limit,
            ):
                result = f(*args, **kwargs)

            # Add function name to output
            if print_stats:
                print(f"\nProfile for {f.__name__}")

            return result

        # Add attribute to access profiling on/off
        wrapper.profiling_enabled = enabled  # type: ignore[attr-defined]

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


def timeit(
    func: Callable[P, R] | None = None,
    *,
    enabled: bool = True,
    print_time: bool = True,
    precision: int = 4,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """Simple timing decorator.

    Parameters
    ----------
    func : Callable | None
        Function to time
    enabled : bool
        Whether timing is enabled
    print_time : bool
        Whether to print timing after each call
    precision : int
        Decimal precision for time display

    Returns
    -------
    Callable
        Decorated function

    Examples
    --------
    >>> @timeit
    ... def some_function():
    ...     time.sleep(0.1)

    >>> @timeit(precision=6)
    ... def precise_function():
    ...     return sum(range(1000))
    """

    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not enabled:
                return f(*args, **kwargs)

            start = time.perf_counter()
            result = f(*args, **kwargs)
            elapsed = time.perf_counter() - start

            if print_time:
                print(f"{f.__name__} took {elapsed:.{precision}f} seconds")

            return result

        wrapper.timing_enabled = enabled  # type: ignore[attr-defined]
        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


class Timer:
    """Simple timer class for measuring elapsed time.

    Examples
    --------
    >>> timer = Timer()
    >>> timer.start()
    >>> # Do some work
    >>> elapsed = timer.stop()
    >>> print(f"Elapsed: {elapsed:.2f} seconds")

    >>> # Use as context manager
    >>> with Timer() as timer:
    ...     # Do some work
    ...     pass
    >>> print(f"Elapsed: {timer.elapsed:.2f} seconds")
    """

    def __init__(self, *, name: str | None = None) -> None:
        """Initialize Timer.

        Parameters
        ----------
        name : str | None
            Optional name for the timer
        """
        self.name = name
        self._start_time: float | None = None
        self._elapsed: float = 0.0

    def start(self) -> None:
        """Start the timer."""
        self._start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop the timer and return elapsed time.

        Returns
        -------
        float
            Elapsed time in seconds

        Raises
        ------
        RuntimeError
            If timer was not started
        """
        if self._start_time is None:
            raise RuntimeError("Timer not started")

        self._elapsed = time.perf_counter() - self._start_time
        self._start_time = None
        return self._elapsed

    @property
    def elapsed(self) -> float:
        """Get elapsed time.

        Returns
        -------
        float
            Elapsed time in seconds
        """
        if self._start_time is not None:
            # Timer is still running
            return time.perf_counter() - self._start_time
        return self._elapsed

    def __enter__(self) -> "Timer":
        """Enter context manager."""
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager."""
        self.stop()
        if self.name:
            print(f"{self.name}: {self._elapsed:.4f} seconds")


def compare_performance(
    functions: dict[str, Callable[[], Any]],
    *,
    iterations: int = 1,
    warmup: int = 0,
) -> dict[str, float]:
    """Compare performance of multiple functions.

    Parameters
    ----------
    functions : dict[str, Callable]
        Dictionary of function names to functions
    iterations : int
        Number of iterations to run each function
    warmup : int
        Number of warmup iterations before timing

    Returns
    -------
    dict[str, float]
        Dictionary of function names to average execution times

    Examples
    --------
    >>> def approach1():
    ...     return sum(range(1000))
    ...
    >>> def approach2():
    ...     return sum(x for x in range(1000))
    ...
    >>> results = compare_performance({
    ...     "list": approach1,
    ...     "generator": approach2,
    ... }, iterations=1000)
    """
    results: dict[str, float] = {}

    for name, func in functions.items():
        # Warmup runs
        for _ in range(warmup):
            func()

        # Timed runs
        times: list[float] = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        results[name] = avg_time

    # Print comparison
    if results:
        baseline_name = next(iter(results))
        baseline_time = results[baseline_name]

        print("\nPerformance Comparison:")
        print("-" * 50)
        for name, avg_time in sorted(results.items(), key=lambda x: x[1]):
            ratio = avg_time / baseline_time
            print(f"{name:20} {avg_time * 1000:10.4f} ms ({ratio:6.2f}x)")

    return results
