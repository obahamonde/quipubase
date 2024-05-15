from __future__ import annotations

import asyncio
import json
import logging
import time
from functools import partial, wraps
from typing import Awaitable, Callable, Coroutine, Type, TypeVar, cast

from fastapi import HTTPException
from typing_extensions import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")


def get_logger(
    name: str | None = None,
    level: int = logging.DEBUG,
    format_string: str = json.dumps(
        {
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "name": "%(name)s",
            "message": "%(message)s",
        }
    ),
) -> logging.Logger:
    """
    Configures and returns a logger with a specified name, level, and format.

    :param name: Name of the logger. If None, the root logger will be configured.
    :param level: Logging level, e.g., logging.INFO, logging.DEBUG.
    :param format_string: Format string for log messages.
    :return: Configured logger.
    """
    if name is None:
        name = "QuipuBase 🚀"
    logger_ = logging.getLogger(name)
    logger_.setLevel(level)
    if not logger_.handlers:
        ch = logging.StreamHandler()
        formatter = logging.Formatter(format_string)
        ch.setFormatter(formatter)
        logger_.addHandler(ch)
    return logging.getLogger(name)


logger = get_logger()


def exception_handler(func: Callable[P, T]) -> Callable[P, T | Coroutine[None, T, T]]:
    """
    Decorator to handle exceptions in a function.

    :param func: Function to be decorated.
    :return: Decorated function.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error("%s: %s", e.__class__.__name__, e)
            raise HTTPException(
                status_code=500,
                detail=f"Internal Server Error: {e.__class__.__name__} => {e}",
            ) from e

    async def awrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            func_ = cast(Awaitable[T], func(*args, **kwargs))
            return await func_
        except Exception as e:
            logger.error("%s: %s", e.__class__.__name__, e)
            raise HTTPException(
                status_code=500,
                detail=f"Internal Server Error: {e.__class__.__name__} => {e}",
            ) from e

    if asyncio.iscoroutinefunction(func):
        awrapper.__name__ = func.__name__
        return awrapper
    wrapper.__name__ = func.__name__
    return wrapper


def timing_handler(func: Callable[P, T]) -> Callable[P, T | Coroutine[None, T, T]]:
    """
    Decorator to measure the time taken by a function.

    :param func: Function to be decorated.
    :return: Decorated function.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info("%s took %s seconds", func.__name__, end - start)
        return result

    async def awrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.time()
        func_ = cast(Awaitable[T], func(*args, **kwargs))
        result = await func_
        end = time.time()
        logger.info("%s took %s seconds", func.__name__, end - start)
        return result

    if asyncio.iscoroutinefunction(func):
        awrapper.__name__ = func.__name__
        return awrapper
    wrapper.__name__ = func.__name__
    return wrapper


def retry_handler(
    func: Callable[P, T], retries: int = 3, delay: int = 1
) -> Callable[P, T | Coroutine[None, T, T]]:
    """
    Decorator to retry a function with exponential backoff.

    :param func: Function to be decorated.
    :param retries: Number of retries.
    :param delay: Delay between retries.
    :return: Decorated function.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        nonlocal delay
        for _ in range(retries):
            try:
                return func(*args, **kwargs)
            except (Exception, HTTPException) as e:
                logger.error("%s: %s", e.__class__.__name__, e)
                time.sleep(delay)
                delay *= 2
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal Server Error: {e.__class__.__name__} => {e}",
                ) from e
        raise HTTPException(
            status_code=500,
            detail="Exhausted retries",
        )

    @wraps(func)
    async def awrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        nonlocal delay
        for _ in range(retries):
            try:
                func_ = cast(Awaitable[T], func(*args, **kwargs))
                return await func_
            except (
                Exception,
                AssertionError,
                KeyError,
                ValueError,
                HTTPException,
            ) as e:
                logger.error("%s: %s", e.__class__.__name__, e)
                await asyncio.sleep(delay)
                delay *= 2
        raise HTTPException(
            status_code=500,
            detail="Exhausted retries",
        )

    if asyncio.iscoroutinefunction(func):
        awrapper.__name__ = func.__name__
        return awrapper
    wrapper.__name__ = func.__name__
    return wrapper


def handle(
    func: Callable[P, T], retries: int = 3, delay: int = 1
) -> Callable[P, T | Coroutine[None, T, T]]:
    """
    Decorator to retry a function with exponential backoff and handle exceptions.

    :param func: Function to be decorated.
    :param retries: Number of retries.
    :param delay: Delay between retries.
    :return: Decorated function.
    """
    eb = partial(retry_handler, retries=retries, delay=delay)
    return cast(
        Callable[P, T | Coroutine[None, T, T]],
        timing_handler(exception_handler(eb(func))),
    )


def asyncify(func: Callable[P, T]) -> Callable[P, Coroutine[None, T, T]]:
    """
    Decorator to convert a synchronous function to an asynchronous function.

    :param func: Synchronous function to be decorated.
    :return: Asynchronous function.
    """

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        wrapper.__name__ = func.__name__
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


def singleton(cls: Type[T]) -> Type[T]:
    """
    Decorator that converts a class into a singleton.

    Args:
                    cls (Type[T]): The class to be converted into a singleton.

    Returns:
                    Type[T]: The singleton instance of the class.
    """
    instances: dict[Type[T], T] = {}

    @wraps(cls)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return cast(Type[T], wrapper)
