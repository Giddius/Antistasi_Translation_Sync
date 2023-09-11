"""
WiP
"""


__version__ = "0.1.0"


def get_package_name() -> str:
    return __name__


def get_pretty_package_name() -> str:
    name = get_package_name()

    pretty_name = name.replace("_", " ").title()

    return pretty_name
