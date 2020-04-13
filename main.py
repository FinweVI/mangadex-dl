#!/usr/bin/python3

import unicodedata
from functools import lru_cache
from os import rename
from pathlib import Path, PurePath
from shutil import make_archive

import requests

URL = "https://mangadex.org"
DEFAULT_LANG_CODE = "gb"

# TODO: CLI
# TODO: Download Folder
# TODO: config file


def _to_zeroed_number(number: int):
    try:
        return f"{int(number):02d}"
    except ValueError:
        return f"0{number}"


@lru_cache(maxsize=128)
def get_manga_info(manga_id: int):
    params = {"type": "manga", "id": manga_id}
    url = f"{URL}/api"

    return requests.get(url, params=params).json()


def get_manga_title(manga_id: int):
    info = get_manga_info(manga_id)
    return (
        unicodedata.normalize("NFKD", info["manga"]["title"])
        .encode("ascii", "ignore")
        .decode("utf-8")
    )


def get_chapters_list(manga_id: int, volume_num: int = -1):
    full_list = get_manga_info(manga_id)["chapter"]
    if volume_num == -1:
        return [
            {chapter_id: details}
            for chapter_id, details in full_list.items()
            if details["lang_code"] == DEFAULT_LANG_CODE
        ]
    else:
        return [
            {chapter_id: details}
            for chapter_id, details in full_list.items()
            if details["lang_code"] == DEFAULT_LANG_CODE
            and int(details["volume"]) == volume_num
        ]


def downloading_all(manga_id: int, cbz=True):
    volumes = sorted(
        {
            _to_zeroed_number(details["volume"])
            for details in get_manga_info(manga_id)["chapter"].values()
            if details["volume"]
        }
    )
    print(
        f"Will download the following volumes for the manga {get_manga_title(manga_id)}: {', '.join(volumes)}"
    )
    for volume in volumes:
        downloading_volume(manga_id, int(volume), cbz)


def downloading_volume(manga_id: int, volume_num: int, cbz=True):
    manga_title = get_manga_title(manga_id)
    for chapters in get_chapters_list(manga_id, volume_num):
        for chapter_id in chapters.keys():
            downloading_chapter(chapter_id)
    if cbz:
        volume_num = _to_zeroed_number(volume_num)
        volume_path = Path(f"{manga_title}/Volume {volume_num}")
        to_cbz(f"{manga_title} - Volume {volume_num}", volume_path)


def downloading_chapter(chapter_id, cbz=False):
    params = {"server": "null", "type": "chapter", "id": chapter_id}
    data = requests.get(f"{URL}/api", params=params)
    json = data.json()

    manga_hash = json["hash"]
    server = json["server"]
    files = json["page_array"]
    volume = _to_zeroed_number(json["volume"])
    chapter = _to_zeroed_number(json["chapter"])
    title = (
        unicodedata.normalize("NFKD", json["title"])
        .encode("ascii", "ignore")
        .decode("utf-8")
    )
    manga_title = get_manga_title(json["manga_id"])

    print(f"Downloading Volume {volume}, Chapter {chapter}: {title}")

    chapter_path = Path(f"{manga_title}/Volume {volume}/Chapter {chapter}")
    chapter_path.mkdir(parents=True, exist_ok=True)

    for image in files:
        file_url = f"{server}/{manga_hash}/{image}"
        image_content = requests.get(file_url)
        filename = PurePath(image)
        img_name = filename.stem
        ext = filename.suffix
        img_num = int(img_name.split("x")[1])
        final_name = f"x{img_num:02d}{ext}"
        with open(f"{chapter_path}/{final_name}", "wb") as manga_file:
            manga_file.write(image_content.content)

    if cbz:
        to_cbz(f"{manga_title} - Chapter {chapter} - {title}", chapter_path)


def to_cbz(name: str, path: Path):
    make_archive(name, "zip", path)
    rename(f"{name}.zip", f"{name}.cbz")
    print(f"Created the CBZ file: {name}.cbz")


def main():
    downloading_volume(51, 2)


if __name__ == "__main__":
    main()
