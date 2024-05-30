"""
WiP
"""


__version__ = "0.5.0"


def get_package_name() -> str:
    return __name__


def get_pretty_package_name() -> str:
    name = get_package_name()

    pretty_name = name.replace("_", " ").title()

    return pretty_name


def get_description() -> str:
    return __doc__


def add_file_logging_handler(root_logger):
    import logging
    import time
    from datetime import datetime, timezone, timedelta
    from pathlib import Path

    root_logger: logging.Logger

    this_file_dir = Path(__file__).parent.absolute()

    log_file = this_file_dir.joinpath("logs", datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S") + ".log")
    log_file.parent.mkdir(exist_ok=True, parents=True)
    handler_2 = logging.FileHandler(log_file)
    handler_3 = logging.FileHandler(log_file.with_stem(f"{log_file.stem}_INFO"))
    handler_2.setFormatter(root_logger.handlers[0].formatter)
    handler_3.setFormatter(root_logger.handlers[0].formatter)

    handler_3.setLevel(logging.INFO)
    root_logger.addHandler(handler_2)
    root_logger.addHandler(handler_3)


def setup_logging():
    import logging
    import time
    from datetime import datetime, timezone, timedelta

    def _time_converter(secs: float) -> time.struct_time:
        utc_datetime: datetime = datetime.fromtimestamp(secs, tz=timezone.utc)

        return utc_datetime.timetuple()

    base_logger = logging.getLogger(get_package_name())
    handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt="%(asctime)s | %(lineno)d | %(levelname)s | %(name)s | %(funcName)s ||-> %(message)s")
    formatter.default_msec_format = "%s.%03d UTC"

    formatter.converter = _time_converter
    handler.setFormatter(formatter)
    base_logger.addHandler(handler)
    base_logger.setLevel(logging.DEBUG)
    # base_logger.setLevel(logging.INFO)


setup_logging()
