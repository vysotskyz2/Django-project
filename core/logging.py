import logging
import sys
from pathlib import Path
from loguru import logger

class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
    "<level>{message}</level>"
)

FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | "
    "{name}:{function}:{line} | {message}"
)

def configure_logging(base_dir: Path, debug: bool = True) -> None:
    logger.remove()
    console_level = "DEBUG" if debug else "INFO"

    logger.add(
        sys.stderr,
        format=CONSOLE_FORMAT,
        level=console_level,
        colorize=True,
        backtrace=True,
        diagnose=debug,
    )

    log_dir = base_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        format=FILE_FORMAT,
        level="DEBUG",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=False,
        encoding="utf-8",
    )

    logger.add(
        log_dir / "errors_{time:YYYY-MM-DD}.log",
        format=FILE_FORMAT,
        level="ERROR",
        rotation="00:00",
        retention="60 days",
        compression="zip",
        backtrace=True,
        diagnose=False,
        encoding="utf-8",
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    if not debug:
        for noisy in ("urllib3", "asyncio"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    logger.info(
        "Loguru configured | console_level={} | log_dir={}",
        console_level, log_dir,
    )
