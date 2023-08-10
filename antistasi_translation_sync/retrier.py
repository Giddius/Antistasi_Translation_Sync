
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from time import sleep
from typing import Any, Union, Callable, Iterable
from functools import wraps

# * Third Party Imports --------------------------------------------------------------------------------->
from yarl import URL
from httpx import Limits, Timeout

import httpx
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# endregion [Imports]


TIMEOUT_FUNCTION_TYPE = Callable[[Union[int, float]], Union[int, float]]


def unchanged_timeout(base_timeout: Union[int, float], attempt: int) -> Union[int, float]:
    return base_timeout


def increasing_timeout(base_timeout: Union[int, float], attempt: int) -> Union[int, float]:
    return base_timeout * (attempt + 1)


def exponential_timeout(base_timeout: Union[int, float], attempt: int) -> Union[int, float]:
    return base_timeout ** (attempt + 1)


class Retrier:
    default_timeout = 5.0

    def __init__(self,
                 errors: Iterable[type[BaseException]] = None,
                 allowed_attempts: int = None,
                 timeout: Union[int, float] = None,
                 timeout_function: TIMEOUT_FUNCTION_TYPE = None,
                 on_error_func: Callable[[], None] = None) -> None:
        self.errors = tuple(errors) or tuple()
        self.allowed_attempts = allowed_attempts or 3
        self.timeout = timeout or self.default_timeout
        self._timeout_function = timeout_function
        self.on_error_func = on_error_func

    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def _helper_func(*args, attempt: int = 0, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except self.errors as error:
                if attempt > self.allowed_attempts:
                    raise

                if self.on_error_func:
                    self.on_error_func()

                seconds_to_sleep = unchanged_timeout(self.timeout, attempt) if self._timeout_function is None else self._timeout_function(self.timeout, attempt)
                msg = f"error: {error!r}, on attempt: {attempt!r}, sleeping {seconds_to_sleep!r} and retrying"

                print(msg, flush=True)

                sleep(seconds_to_sleep)
                return _helper_func(*args, attempt=attempt + 1, **kwargs)

        return _helper_func


class ResponsePaginator:
    __slots__ = ("client",
                 "url",
                 "params",
                 "response",
                 "response_data",
                 "finished")

    def __init__(self, response: httpx.Response, client: httpx.Client) -> None:
        self.client = client
        self.url = response.url.copy_with()
        self.params = dict(**response.url.params)
        self.response = response
        self.response_data = self.response.json()
        self.finished: bool = False

    def _next_page_via_cursor(self) -> None:
        next_cursor = self.response_data["nextCursor"]
        if next_cursor is None:
            self.finished = True
            return

        self.params["cursor"] = next_cursor
        self._execute_next_page_request()

    def _next_page_via_page(self) -> None:
        curr_page = self.response_data["page"]["number"]
        total_pages = self.response_data["page"]["totalPages"]
        if (curr_page + 1) == total_pages:
            self.finished = True
            return

        self.params["page"] = curr_page + 1
        self._execute_next_page_request()

    def _execute_next_page_request(self) -> None:
        new_response = self.client.request(method=self.response.request.method, url=self.url, params=self.params)
        self.response = new_response
        self.response_data = new_response.json()

    def request_next(self) -> None:
        if "nextCursor" in self.response_data:
            self._next_page_via_cursor()

        elif "page" in self.response_data:
            self._next_page_via_page()

        else:
            raise RuntimeError(repr(self))

    def __iter__(self):
        while self.finished is False:
            try:
                yield self.response_data["_embedded"]

                self.request_next()
            except KeyError:
                break
