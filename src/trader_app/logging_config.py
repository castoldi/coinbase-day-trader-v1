import gzip
import logging
import shutil
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class CompressingTimedRotatingFileHandler(TimedRotatingFileHandler):
    def rotate(self, source: str, dest: str) -> None:
        super().rotate(source, dest)
        source_path = Path(dest)
        gzip_path = source_path.with_suffix(source_path.suffix + ".gz")
        with source_path.open("rb") as src, gzip_path.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb") as gz:
                shutil.copyfileobj(src, gz)
        source_path.unlink(missing_ok=True)


def configure_daily_logger(name: str, log_dir: str | Path = "logs") -> logging.Logger:
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = CompressingTimedRotatingFileHandler(
        path / f"{name}.log",
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
