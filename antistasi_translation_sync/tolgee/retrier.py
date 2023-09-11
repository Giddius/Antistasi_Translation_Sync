
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from time import sleep
from typing import Any, Union, Callable, Iterable, Protocol, TypeAlias
from functools import wraps

# * Third Party Imports --------------------------------------------------------------------------------->
import httpx

# endregion [Imports]

ANY_NUMBER_TYPE: TypeAlias = Union[int, float]

TIMEOUT_FUNCTION_TYPE = Callable[[ANY_NUMBER_TYPE], ANY_NUMBER_TYPE]


def unchanged_timeout(base_timeout: ANY_NUMBER_TYPE, attempt: int) -> ANY_NUMBER_TYPE:
    return base_timeout


def increasing_timeout(base_timeout: ANY_NUMBER_TYPE, attempt: int) -> ANY_NUMBER_TYPE:
    return base_timeout * (attempt + 1)


def exponential_timeout(base_timeout: ANY_NUMBER_TYPE, attempt: int) -> ANY_NUMBER_TYPE:
    return base_timeout ** (attempt + 1)


class Retrier:
    __slots__ = ("errors",
                 "allowed_attempts",
                 "timeout",
                 "_timeout_function",
                 "on_error_func",
                 "log_function")
    default_timeout = 5.0
    default_on_error_function = lambda x: ...

    def __init__(self,
                 errors: Iterable[type[BaseException]] = None,
                 allowed_attempts: int = None,
                 timeout: ANY_NUMBER_TYPE = None,
                 timeout_function: TIMEOUT_FUNCTION_TYPE = None,
                 on_error_func: Callable[[Exception], None] = None,
                 log_function: Callable[[str], None] = print) -> None:

        self.errors = tuple(errors) or tuple()
        self.allowed_attempts = allowed_attempts or 3
        self.timeout = timeout or self.default_timeout
        self._timeout_function = timeout_function
        self.on_error_func = on_error_func or self.default_on_error_function
        self.log_function = log_function

    def _log_message(self, error: BaseException, attempt: int, seconds_to_sleep: float) -> None:
        if self.log_function is None:
            return

        msg = f"error: {error!r}, on attempt: {attempt!r}, sleeping {seconds_to_sleep!r} and retrying"

        self.log_function(msg)

    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def _helper_func(*args, attempt: int = 0, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except self.errors as error:

                self.on_error_func(error)

                if attempt > self.allowed_attempts:
                    raise

                seconds_to_sleep = unchanged_timeout(self.timeout, attempt) if self._timeout_function is None else self._timeout_function(self.timeout, attempt)
                self._log_message(error=error, attempt=attempt, seconds_to_sleep=seconds_to_sleep)
                sleep(seconds_to_sleep)
                return _helper_func(*args, attempt=attempt + 1, **kwargs)

        return _helper_func


class BaseResponsePaginator(Protocol):
    ...


class ResponsePaginator:
    # todo: Redo this thing
    # todo: Redo maybe as unique class for each kind of pagination (inherit from abstract-base-class or at least Protocol-class)
    # todo: test if it really works always

    __slots__ = ("client",
                 "url",
                 "params",
                 "response",
                 "response_data",
                 "request_function",
                 "finished")

    def __init__(self, response: httpx.Response, client: httpx.Client) -> None:
        self.client = client
        self.url = response.url.copy_with()
        self.params = dict(**response.url.params)
        self.response = response
        self.response_data = self.response.json()
        self.request_function: Callable = self.client.get if str(self.response.request.method).casefold() == "get" else getattr(self.client, str(self.response.request.method).casefold())
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
        new_response = self.request_function(url=self.url, params=self.params)
        self.response = new_response
        self.response_data = new_response.json()

    def request_next(self) -> None:
        if "nextCursor" in self.response_data:
            print("paginating via cursor")
            self._next_page_via_cursor()

        elif "page" in self.response_data:
            self._next_page_via_page()
            print("paginating via page")

        else:
            raise RuntimeError(repr(self))

    def __iter__(self):
        while self.finished is False:
            try:
                yield self.response_data["_embedded"].copy()

                self.request_next()
            except KeyError:
                break
