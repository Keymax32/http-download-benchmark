"""Measure a series of sequential HTTP downloads."""

import argparse
from http.client import HTTPException
import sys
from time import perf_counter
from urllib.parse import urlsplit
from urllib.request import urlopen


REQUEST_COUNT = 10
CHUNK_SIZE = 64 * 1024
TIMEOUT_SECONDS = 30
BYTES_PER_MIB = 1024 ** 2


def measure_download(url: str) -> tuple[float, int]:
    start = perf_counter()
    downloaded = 0

    with urlopen(url, timeout=TIMEOUT_SECONDS) as response:
        while chunk := response.read(CHUNK_SIZE):
            downloaded += len(chunk)

        # A bounded read can reach EOF before the declared body length.
        if response.length:
            raise OSError(f"Ответ оборвался: не получено {response.length} байт")

    return perf_counter() - start, downloaded


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Измеряет скорость скачивания по 10 последовательным HTTP-запросам."
    )
    parser.add_argument("url", metavar="URL", help="Адрес ресурса (http:// или https://)")
    args = parser.parse_args()

    try:
        target = urlsplit(args.url)
        if target.scheme not in ("http", "https") or not target.hostname:
            raise ValueError("нужен полный адрес, начинающийся с http:// или https://")
    except ValueError as error:
        parser.error(f"Некорректный URL: {error}")

    total_seconds = 0.0
    total_bytes = 0
    for request_number in range(1, REQUEST_COUNT + 1):
        try:
            seconds, downloaded = measure_download(args.url)
        except (OSError, HTTPException, ValueError) as error:
            print(f"Запрос {request_number}/{REQUEST_COUNT}: {error}", file=sys.stderr)
            return 1

        total_seconds += seconds
        total_bytes += downloaded

    print(f"Среднее время запроса: {total_seconds / REQUEST_COUNT:.4f} с")
    print(f"Общий объём скачанных данных: {total_bytes} байт")
    print(f"Скорость скачивания: {total_bytes / total_seconds / BYTES_PER_MIB:.4f} МиБ/с")
    return 0


if __name__ == "__main__":
    sys.exit(main())
