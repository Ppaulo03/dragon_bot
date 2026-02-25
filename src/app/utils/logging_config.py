import sys
from pathlib import Path
from loguru import logger


def setup_logging():

    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    logger.remove()

    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
        "| <level>{level: <8}</level> "
        "| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
        "- <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    logger.add(
        log_path / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} "
        "| {level: <8} "
        "| {name}:{function}:{line} "
        "- {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )

    logger.add(
        log_path / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO",
        rotation="00:00",
        retention="7 days",
        backtrace=True,
        diagnose=True,
    )
    logger.info("Sistema de Logging configurado com sucesso.")
