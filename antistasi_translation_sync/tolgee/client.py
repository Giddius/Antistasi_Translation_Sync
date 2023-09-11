"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from typing import TYPE_CHECKING, Union, Optional
from pathlib import Path
from datetime import datetime, timezone

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

# * Standard Library Imports ---------------------------------------------------------------------------->
from types import TracebackType

# * Third Party Imports --------------------------------------------------------------------------------->
import httpx

from .models import Tag, Project, Language, ProjectInfo, TranslationKey, TranslationEntry, GeneralProjectData, TranslationNamespace, MachineTranslationProvider, EntryState
from .rate_limiter import RateLimit, get_rate_limiter

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

# endregion [Constants]


def get_all_projects_data_from_access_token(in_base_url: Union[str, httpx.URL], access_token: str) -> tuple["GeneralProjectData"]:
    TO_REMOVE_PROJECT_DATA_KEYS = {"organizationOwner", "organizationRole", "directPermission", "computedPermission", "baseLanguage"}

    full_url = httpx.URL(in_base_url).join("v2/projects")

    params = {"page": 0}
    headers = {"X-API-Key": access_token}

    raw_projects_data = []

    while True:
        response = httpx.get(full_url, headers=headers, params=params)
        response.raise_for_status()

        response_data = response.json()
        for _project_data in response_data["_embedded"]["projects"]:
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
                                                        avatar_thumbnail_url=_avatar_thumbnail_url))

        max_pages = response_data["page"]["totalPages"]
        current_page = response_data["page"]["number"]

        params["page"] += 1

        if params["page"] >= max_pages:
            break

    return raw_projects_data


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
            print(f"{response.text=}", flush=True)
            print(f"{response.url=}", flush=True)

            raise e

    def on_request(self, request: httpx.Request):
        # print(f"{request.url.raw=}")

        self.rate_limit_spec.consume()

    def _create_client(self) -> httpx.Client:
        client = httpx.Client(base_url=self._base_url,
                              headers={"X-API-Key": self._api_key},
                              event_hooks={'response': [self.on_response],
                                           "request": [self.on_request]},
                              timeout=httpx.Timeout(timeout=30.0),
                              limits=httpx.Limits(max_connections=1, max_keepalive_connections=1))
        return client

    def _get_project_info(self) -> "ProjectInfo":
        stats_unwanted_keys = {"languageStats"}
        stats_response = self.client.get("/stats", params={})

        stats_data = {k: v for k, v in stats_response.json().items() if k not in stats_unwanted_keys}

        info_unwanted_keys = {"userFullName", "id", "scopes", "expiresAt", "username", "description", "permittedLanguageIds"}
        info_request = self.client.build_request("GET", str(self._base_url).removesuffix("/").removesuffix("/projects") + "/api-keys/current")

        info_response = self.client.send(info_request)

        info_data = {k: v for k, v in info_response.json().items() if k not in info_unwanted_keys}
        info_data["lastUsedAt"] = datetime.fromtimestamp(info_data["lastUsedAt"] / 1000, tz=timezone.utc)
        return ProjectInfo(**(stats_data | info_data))

    def _build_project_tree(self, project: "Project") -> None:

        params = {"languages": [l.tag for l in project.language_map.values()],
                  "size": 75
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
                                     tags=[project.get_or_create_tag(tag_id=i["id"], tag_name=i["name"]) for i in data["keyTags"]],
                                     client=self)
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
                                                   fromTranslationMemory=translation_data["fromTranslationMemory"],
                                                   client=self)
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
            data += [Language.from_response_data(client=self, **i) for i in response.json()["_embedded"]["languages"]]

            curr_page = response_data["page"]["number"]
            total_pages = response_data["page"]["totalPages"]

            if (curr_page + 1) == total_pages:
                break

            params["page"] += 1
        return tuple(data)

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
                                           fromTranslationMemory=translation_data["fromTranslationMemory"],
                                           client=self)
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
                             tags=[],
                             client=self)
        namespace.add_key(key)

        return key

    def get_namespace_id_by_name(self, namespace_name: str) -> int:
        response = self.client.get(f"/namespace-by-name/{namespace_name}")

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
