"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from typing import TYPE_CHECKING, Union, Optional, Callable
from pathlib import Path
from datetime import datetime, timezone
from time import sleep
from httpx._config import DEFAULT_LIMITS, Limits, Proxy
from httpx._models import Request, Response
from functools import partial
import enum
import re
from httpx._types import CertTypes, VerifyTypes
import random
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

# * Standard Library Imports ---------------------------------------------------------------------------->
from types import TracebackType

# * Third Party Imports --------------------------------------------------------------------------------->
import httpx

from .models import Tag, Project, Language, ProjectInfo, EntryState, TranslationKey, TranslationEntry, GeneralProjectData, GeneralOrganizationData, TranslationNamespace, MachineTranslationProvider, EntryState, ProjectRepository
from .rate_limiter import RateLimit, get_rate_limiter, seconds_until_next_full_minute

from ..errors import MaxRetriesReachedError, NoRetryStatusError


import logging
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from ..stringtable import LanguageLike

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = logging.getLogger(__name__)

# endregion [Constants]


class ApiKeyType(enum.Enum):
    PERSONAL_ACCESS_TOKEN = enum.auto()
    PROJECT_KEY = enum.auto()


def identify_api_key_type(in_token: str) -> ApiKeyType:
    if in_token.casefold().startswith("tgpat_"):
        return ApiKeyType.PERSONAL_ACCESS_TOKEN

    if in_token.casefold().startswith("tgpak"):
        return ApiKeyType.PROJECT_KEY

    raise ValueError("unknown api_key type.")


def get_all_projects_data_from_access_token(in_base_url: Union[str, httpx.URL], access_token: str) -> tuple["GeneralProjectData"]:
    """
    BROKEN CURRENTLY because of "api_access_forbidden"
    """

    import pp

    TO_REMOVE_PROJECT_DATA_KEYS = {"organizationOwner", "organizationRole", "directPermission", "computedPermission", "baseLanguage"}

    full_url = httpx.URL(in_base_url).join("/v2/projects")

    params = {"page": 0}
    headers = {"X-API-Key": access_token}

    raw_projects_data = []

    while True:
        response = httpx.get(full_url, headers=headers, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPError as e:
            log.error("status_code: %r, text: %r", response.status_code, response.text)
            raise e

        response_data = response.json()
        for _project_data in response_data["_embedded"]["projects"]:

            _organization = GeneralOrganizationData(organization_id=_project_data["organizationOwner"]["id"], name=_project_data["organizationOwner"]["name"], slug=_project_data["organizationOwner"]["slug"], description=_project_data["organizationOwner"]["description"])
            _mod_project_data = {k: v for k, v in _project_data.items() if k not in TO_REMOVE_PROJECT_DATA_KEYS}
            _project_id = _mod_project_data.pop("id")
            _project_url = httpx.URL(_mod_project_data.pop("_links")["self"]["href"], scheme="https")
            _project_description = _mod_project_data["description"] or ""

            if _mod_project_data["avatar"] is not None:
                _avatar_url = str(httpx.URL(_project_url).join(_mod_project_data["avatar"]["large"]))
                _avatar_thumbnail_url = str(httpx.URL(_project_url).join(_mod_project_data["avatar"]["thumbnail"]))

            else:
                _avatar_url = None
                _avatar_thumbnail_url = None

            raw_projects_data.append(GeneralProjectData(project_id=_project_id,
                                                        name=_mod_project_data["name"],
                                                        slug=_mod_project_data["slug"],
                                                        project_url=_project_url,
                                                        description=_project_description,
                                                        avatar_url=_avatar_url,
                                                        avatar_thumbnail_url=_avatar_thumbnail_url,
                                                        organization=_organization))

        max_pages = response_data["page"]["totalPages"]
        current_page = response_data["page"]["number"]

        params["page"] += 1

        if params["page"] >= max_pages:
            break

    return raw_projects_data


def get_project_repository(in_base_url: Union[str, httpx.URL], access_token: str) -> ProjectRepository:
    repository = ProjectRepository()
    for project in get_all_projects_data_from_access_token(in_base_url=in_base_url, access_token=access_token):
        repository.add_project(project=project)

    return repository


class CustomTransport(httpx.HTTPTransport):

    def __init__(self,
                 verify: VerifyTypes = True,
                 cert: CertTypes | None = None,
                 http1: bool = True,
                 http2: bool = False,
                 limits: Limits = DEFAULT_LIMITS,
                 trust_env: bool = True,
                 proxy: Proxy | None = None,
                 uds: str | None = None,
                 local_address: str | None = None,
                 connection_retries: int = 0,
                 max_error_retries: int = 5,
                 base_error_sleep_time: float = 2.0) -> None:

        super().__init__(verify=verify,
                         cert=cert,
                         http1=http1,
                         http2=http2,
                         limits=limits,
                         trust_env=trust_env,
                         proxy=proxy,
                         uds=uds,
                         local_address=local_address,
                         retries=connection_retries)

        self.max_error_retries = max_error_retries
        self.base_error_sleep_time = base_error_sleep_time
        self._error_retry_code_map: dict[int, Callable[[Request, Response, httpx.HTTPError], float]] = {429: self._on_rate_limited,
                                                                                                        400: self._dont_retry,
                                                                                                        401: self._dont_retry,
                                                                                                        404: self._dont_retry,
                                                                                                        500: self._dont_retry,
                                                                                                        000: self._default_retry}

    def _default_retry(self, request: Request, response: Response, error: httpx.HTTPError) -> float:
        return self.determine_retry_sleep_time(request.retry_number)

    def _on_rate_limited(self, request: Request, response: Response, error: httpx.HTTPError) -> float:
        try:
            error_data = response.json()
            retry_sleep_time = (error_data["retryAfter"] / 1000) * 1.15
            return retry_sleep_time
        except Exception as e:
            log.error(e, exc_info=True)
            log.critical(f"Encountered Exception {e!r} trying to get error_data {response.content!r}")

        return self.determine_retry_sleep_time(request.retry_number)

    def _dont_retry(self, request: Request, response: Response, error: httpx.HTTPError) -> float:
        log.error("status_code: %r, text: %r", response.status_code, response.text)
        raise NoRetryStatusError(f"Unable to retry for status {response.status_code!r} for request {request!r} with params {request.url.params!r} ({response.text}).") from error

        return 0.0

    def determine_retry_sleep_time(self, retry_number: int) -> float:
        fixed_sleep_time = self.base_error_sleep_time * (self.base_error_sleep_time**(retry_number - 1))

        sleep_time = fixed_sleep_time * (1 + (random.random() / 2))
        return round(sleep_time, ndigits=3)

    def on_error(self, request: Request, response: Response, error: httpx.HTTPError) -> Response:
        response.read()
        retry_sleep_time = self._error_retry_code_map.get(response.status_code, self._error_retry_code_map[0])(request, response, error)
        log.critical(f"sleeping {retry_sleep_time!r} s, because of {response.status_code!r} {response.text!r} from {request.url!r}.")
        sleep(retry_sleep_time)

        return self.handle_request(request=request)

    def handle_request(self, request: Request) -> Response:
        retry_number = getattr(request, "retry_number", 0) + 1
        setattr(request, "retry_number", retry_number)

        try:
            response = super().handle_request(request)
            response.request = request

            response.raise_for_status()

        except httpx.HTTPError as e:
            if retry_number > self.max_error_retries:
                raise MaxRetriesReachedError(f"Exhausted all retries ({self.max_error_retries!r}) for request {request!r}.") from e
            response = self.on_error(request=request, response=response, error=e)

        return response


class TolgeeClient:

    __slots__ = ("_base_url",
                 "_api_key",
                 "client",
                 "project",
                 "rate_limit_spec",
                 "__weakref__")

    def __init__(self,
                 base_url: Union[str, httpx.URL],
                 api_key: str) -> None:
        self._base_url = httpx.URL(base_url)
        self._api_key = api_key
        self.client: httpx.Client = None
        self.project: "Project" = None
        self.rate_limit_spec: RateLimit = get_rate_limiter(self._base_url)

    @ property
    def project_info(self) -> ProjectInfo:
        return self.project.project_info

    @ property
    def default_language(self) -> Language:
        return self.project.default_language

    @ property
    def languages(self) -> tuple[Language]:
        return self.project.languages

    def on_response(self, response: httpx.Response):
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            response.read()
            log.error(f"{response.text=}")
            log.error(f"{response.url=}")

            raise e

    def on_request(self, request: httpx.Request):
        # print(f"{request.url.raw=}")

        self.rate_limit_spec.consume()
        # log.debug("did a request type: %r, url: %r", request.method, request.url)
        ...

    def _create_client(self) -> httpx.Client:
        client = httpx.Client(base_url=self._base_url,
                              headers={"X-API-Key": self._api_key},
                              event_hooks={'response': [self.on_response],
                                           "request": [self.on_request]},
                              timeout=httpx.Timeout(timeout=60.0),
                              limits=httpx.Limits(max_connections=5, max_keepalive_connections=5),
                              transport=CustomTransport())
        return client

    def _get_project_info(self) -> "ProjectInfo":
        stats_unwanted_keys = {"languageStats"}
        stats_response = self.client.get("/stats", params={})

        stats_data = {k: v for k, v in stats_response.json().items() if k not in stats_unwanted_keys}

        if re.search(r"\/\d+$", str(self._base_url).removesuffix("/")):
            info_unwanted_keys = {"userFullName", "id", "scopes", "expiresAt", "username", "description", "permittedLanguageIds", "expiresAt"}

            project_id = int(re.search(r"\/(?P<project_id>\d+)$", str(self._base_url).removesuffix("/")).group("project_id"))
            info_request = self.client.build_request("GET", str(self._base_url).removesuffix("/").rsplit("/", 1)[0], params={"size": 250})
            info_response = self.client.send(info_request)

            _raw_data = [project_data for project_data in info_response.json()["_embedded"]['projects'] if project_data['id'] == project_id][0]
            info_data = {"projectName": _raw_data["name"], "lastUsedAt": None, "projectId": project_id, }

        else:
            info_unwanted_keys = {"userFullName", "id", "scopes", "expiresAt", "username", "description", "permittedLanguageIds", "expiresAt"}

            info_request = self.client.build_request("GET", str(self._base_url).removesuffix("/").removesuffix("/projects") + "/api-keys/current")

            info_response = self.client.send(info_request)

            info_data = {k: v for k, v in info_response.json().items() if k not in info_unwanted_keys}
            info_data["lastUsedAt"] = datetime.fromtimestamp(info_data["lastUsedAt"] / 1000, tz=timezone.utc)
        return ProjectInfo(**(stats_data | info_data))

    def _build_project_tree(self, project: "Project") -> None:

        params = {"languages": [lang.tag for lang in project.language_map.values()],
                  "size": 50
                  }

        while True:
            response = self.client.get("/translations", params=params)

            general_response_data = response.json()
            try:
                response_data = general_response_data["_embedded"]
            except KeyError:
                break
            for data in response_data["keys"]:
                namespace = project.get_or_create_namespace(namespace_id=data["keyNamespaceId"], name=data["keyNamespace"])
                key = TranslationKey(key_id=data["keyId"],
                                     name=data["keyName"],
                                     namespace=namespace,
                                     tags=[project.get_or_create_tag(tag_id=i["id"], tag_name=i["name"]) for i in data["keyTags"]])
                namespace.add_key(key)

                for language_tag, translation_data in data["translations"].items():

                    if not translation_data["text"]:
                        continue

                    translation = TranslationEntry(entry_id=translation_data["id"],
                                                   key=key,
                                                   language=project.get_language(language_tag),
                                                   text=translation_data["text"],
                                                   state=translation_data["state"],
                                                   outdated=translation_data["outdated"],
                                                   auto=translation_data["auto"],
                                                   mtProvider=translation_data["mtProvider"],
                                                   commentCount=translation_data["commentCount"],
                                                   unresolvedCommentCount=translation_data["unresolvedCommentCount"],
                                                   fromTranslationMemory=translation_data["fromTranslationMemory"])
                    key.add_entry(translation)

            try:
                cursor = general_response_data["nextCursor"]
                if not cursor:
                    break
                params["cursor"] = cursor
            except KeyError:
                break

    def get_available_languages(self) -> tuple[Language]:
        data = []
        params = {"page": 0}
        while True:
            response = self.client.get("/languages", params=params)
            response_data = response.json()
            data += [Language.from_response_data(**i) for i in response.json()["_embedded"]["languages"]]

            curr_page = response_data["page"]["number"]
            total_pages = response_data["page"]["totalPages"]

            if (curr_page + 1) == total_pages:
                break

            params["page"] += 1
        return tuple(data)

    def set_outdated_for_translation_entry(self, translation: "TranslationEntry", value: bool):
        encoded_value = "true" if value is True else "false"
        response = self.client.put(f"/translations/{translation.entry_id}/set-outdated-flag/{encoded_value}")
        response.raise_for_status()
        translation._outdated = value

        return translation

    def set_state_for_translation_entry(self, translation: "TranslationEntry", state: EntryState):

        response = self.client.put(f"/translations/{translation.entry_id}/set-state/{state.name.upper()}")
        response.raise_for_status()
        translation._state = state
        return response.json()

    def set_tag_for_key(self, key: "TranslationKey", tag_name: str) -> "Tag":
        response = self.client.put(f"/keys/{key.key_id}/tags", json={"name": tag_name})
        response_data = response.json()
        tag = key.project.get_or_create_tag(tag_id=response_data["id"], tag_name=response_data["name"])
        return tag

    def remove_tag_for_key(self, key: "TranslationKey", tag: "Tag") -> None:
        response = self.client.delete(f"/keys/{key.key_id}/tags/{tag.tag_id}")
        response.close()

    def refresh_key(self, key: "TranslationKey") -> None:

        params = {"filterKeyName": [key.name],
                  "languages": [language.tag for language in key.project.languages],
                  "size": 50}

        response = self.client.get("/translations", params=params)

        new_data = response.json()["_embedded"]["keys"]

        new_key_data = next((data for data in new_data if data["keyId"] == key.key_id), None)

        if new_key_data is None:
            raise RuntimeError(f"Unable to update {key!r} from {self.project!r}.")

        key._tags = frozenset([key.project.get_or_create_tag(tag_id=i["id"], tag_name=["name"]) for i in new_key_data["keyTags"]])
        key._entry_map = {}
        for language_tag, translation_data in new_key_data["translations"].items():

            if not translation_data["text"]:
                continue

            translation = TranslationEntry(entry_id=translation_data["id"],
                                           key=key,
                                           language=key.project.get_language(language_tag),
                                           text=translation_data["text"],
                                           state=translation_data["state"],
                                           outdated=translation_data["outdated"],
                                           auto=translation_data["auto"],
                                           mtProvider=translation_data["mtProvider"],
                                           commentCount=translation_data["commentCount"],
                                           unresolvedCommentCount=translation_data["unresolvedCommentCount"],
                                           fromTranslationMemory=translation_data["fromTranslationMemory"])
            key.add_entry(translation)

    def insert_translation_for_new_key(self, namespace_name: str, key_name: str, language: "LanguageLike", text: str) -> "TranslationKey":
        language = self.project.get_language(language)

        assert language.name == "Original"

        request_data = {"key": key_name,
                        "namespace": namespace_name,
                        "translations": {language.tag: text}}

        response = self.client.post("/translations", json=request_data)

        new_data = response.json()

        namespace = self.project.get_or_create_namespace(name=new_data["keyNamespace"])
        key = TranslationKey(key_id=new_data["keyId"],
                             name=new_data["keyName"],
                             namespace=namespace,
                             tags=[])
        namespace.add_key(key)

        return key

    def insert_multiple_translation_for_new_key(self, namespace_name: str, key_name: str, translations: dict["LanguageLike", str]) -> "TranslationKey":
        translations = {self.project.get_language(k).tag: v for k, v in translations.items()}

        request_data = {"key": key_name,
                        "namespace": namespace_name,
                        "translations": translations}

        response = self.client.post("/translations", json=request_data)

        new_data = response.json()

        namespace = self.project.get_or_create_namespace(name=new_data["keyNamespace"])
        key = TranslationKey(key_id=new_data["keyId"],
                             name=new_data["keyName"],
                             namespace=namespace,
                             tags=[])
        namespace.add_key(key)

        return key

    def get_namespace_id_by_name(self, namespace_name: str) -> int:
        response = self.client.get(httpx.URL(f"/namespace-by-name/{namespace_name}"), params={})

        return response.json()["id"]

    def update_namespace_for_key(self, key: "TranslationKey", new_namespace_name: str) -> None:

        old_namespace = key.namespace
        response = self.client.put(f"/keys/{key.key_id}", json={"name": key.name, "namespace": new_namespace_name})

        new_namespace = key.project.get_or_create_namespace(name=response.json()["namespace"])

        old_namespace.remove_key(key)
        new_namespace.add_key(key)
        key._namespace = new_namespace
        key.refresh()

    def connect(self, _from_enter: bool = False) -> Self:
        self.client = self._create_client()
        # self.rate_limit_spec.force_sleep(value=seconds_until_next_full_minute(max_value=15.0))

        if _from_enter is True:
            self.client.__enter__()

        self.project = Project(client=self)

        return self

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    def __enter__(self) -> Self:
        self.connect(_from_enter=True)

        return self

    def __exit__(self,
                 exc_type: Optional[type[BaseException]] = None,
                 exc_value: Optional[BaseException] = None,
                 traceback: Optional[TracebackType] = None) -> None:
        self.client.__exit__(exc_type=exc_type, exc_value=exc_value, traceback=traceback)

    def __repr__(self) -> str:

        return f'{self.__class__.__name__}(base_url={self._base_url!r})'


# region [Main_Exec]


if __name__ == '__main__':
    ...

# endregion [Main_Exec]
