"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
import argparse
from typing import TYPE_CHECKING, Any, Union, Callable
from pathlib import Path
from collections.abc import Callable, Sequence
from . import __version__, get_description
if sys.version_info >= (3, 11):
    pass
else:
    pass
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from .configuration import Config

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


def _resolve_target_type(in_data) -> Union[Path, Callable]:
    if in_data.upper() == "AUTO_ALL":
        return in_data.upper()

    return Path(in_data)


class CommandLineParser(argparse.ArgumentParser):

    def __init__(self,
                 prog: str = None,
                 usage: str = None,
                 description: str = None,
                 epilog: str = None,
                 parents: Sequence[argparse.ArgumentParser] = None,
                 formatter_class: "argparse._FormatterClass" = argparse.HelpFormatter,
                 prefix_chars: str = '-',
                 fromfile_prefix_chars: str = None,
                 argument_default: Any = None,
                 conflict_handler: str = 'error',
                 add_help: bool = True,
                 allow_abbrev: bool = True,
                 exit_on_error: bool = True,
                 version: Union[str, None] = None) -> None:

        super().__init__(prog=prog,
                         usage=usage,
                         description=description if description is not None else get_description(),
                         epilog=epilog,
                         parents=parents or [],
                         formatter_class=formatter_class,
                         prefix_chars=prefix_chars,
                         fromfile_prefix_chars=fromfile_prefix_chars,
                         argument_default=argument_default,
                         conflict_handler=conflict_handler,
                         add_help=add_help,
                         allow_abbrev=allow_abbrev,
                         exit_on_error=exit_on_error)

        self.version = version if version is not None else __version__

    def add_meta_actions(self) -> None:
        if self.version is not None:
            self.add_argument("-v", "--version", action=argparse._VersionAction, version=self.version)

    def parse_args(self, args: list[str] = None, config: "Config" = None) -> "Config":

        return super().parse_args(args=args, namespace=config).resolve_targets()

    def parse_known_args(self, args: list[str] = None, config: "Config" = None) -> "Config":
        return super().parse_known_args(args=args, namespace=config)


def get_command_line_parser(**kwargs) -> CommandLineParser:
    parser = CommandLineParser(**kwargs)
    parser.add_meta_actions()
    parser.add_argument("--working-dir", "-wd", type=Path, dest="working_dir", metavar="", default=argparse.SUPPRESS)
    parser.add_argument("--base-url", "-u", type=str, dest="tolgee_config.base_url", metavar="", required=True)
    parser.add_argument("targets", type=_resolve_target_type, nargs="+")

    parser.add_argument("--token-suffix", "-t", type=str, dest="tolgee_config.api_project_token_suffix", metavar="", required=False, default=argparse.SUPPRESS)
    parser.add_argument("--indentation", "-i", type=int, dest="stringtable_config.indentation", metavar="", default=argparse.SUPPRESS)

    return parser


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
