#!/usr/bin/env python3

import re
import unicodedata
from contextlib import contextmanager
from functools import lru_cache
from os import chdir, rename
from pathlib import Path
from shutil import make_archive

import requests

import fire


@contextmanager
def workdir(path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    chdir(path)
    try:
        yield
    finally:
        chdir(prev_cwd)


def _to_zeroed_number(number: int):
    try:
        return f"{int(number):02d}"
    except ValueError:
        if len(str(number)) == 3:
            return f"0{number}"
        return str(number)


def asciify(data):
    return (
        unicodedata.normalize("NFKD", data).encode("ascii", "ignore").decode()
    )


class MangaDex:
    def __init__(
        self,
        manga_id: int,
        lang_code: str = "gb",
        dl_folder="dl",
        dest_folder="dl/cbz",
    ):
        self._api_url = "https://mangadex.org/api"
        self._default_lang_code = lang_code
        self._dl_folder = Path(dl_folder)
        self._cbz_path = Path(dest_folder)
        self._manga_id = manga_id
        self._manga_title = self._get_manga_title()

        self._dl_folder.mkdir(parents=True, exist_ok=True)
        self._cbz_path.mkdir(parents=True, exist_ok=True)
        print(f'Will download "{self._manga_title}"')

    @lru_cache(maxsize=1)
    def _get_manga_info(self):
        params = {"type": "manga", "id": self._manga_id}
        return requests.get(self._api_url, params=params).json()

    def _get_manga_title(self):
        info = self._get_manga_info()
        return asciify(info["manga"]["title"])

    def _get_chapters_list(self):
        full_chapters_list = self._get_manga_info()["chapter"]
        return [
            {chapter_id: details}
            for chapter_id, details in full_chapters_list.items()
            if details["lang_code"] == self._default_lang_code
        ]

    def _to_cbz(self, name: str, path: Path):
        make_archive(
            f"{self._cbz_path}/{name}", "zip", f"{self._dl_folder}/{path}"
        )
        with workdir(self._cbz_path):
            rename(f"{name}.zip", f"{name}.cbz")
            print(f"Created the CBZ file: {name}.cbz")

    def _download_chapter_id(self, chapter_id: int, cbz=False):
        params = {"server": "null", "type": "chapter", "id": chapter_id}
        data = requests.get(self._api_url, params=params)
        json = data.json()

        manga_hash = json["hash"]
        server = json["server"]
        files = json["page_array"]
        volume = _to_zeroed_number(json["volume"]) or "01"
        chapter = _to_zeroed_number(json["chapter"])
        title = (
            asciify(json["title"]) or "No title available for this chapter."
        )

        print(f"Downloading Volume {volume}, Chapter {chapter}: {title}")

        chapter_path = Path(
            f"{self._manga_title}/Volume {volume}/Chapter {chapter}"
        )

        for image in files:
            search = re.search(r"(\d+)\.(\w+)", image)
            if not search:
                print(
                    f"Oops, unable to process image {image} in chapter {chapter}!"
                )
                continue
            img_num = _to_zeroed_number(search.group(1))
            img_ext = search.group(2)
            final_name = f"x{img_num}.{img_ext}"
            file_url = f"{server}/{manga_hash}/{image}"
            image_content = requests.get(file_url)
            with workdir(self._dl_folder):
                chapter_path.mkdir(parents=True, exist_ok=True)
                with open(f"{chapter_path}/{final_name}", "wb") as chapter_img:
                    chapter_img.write(image_content.content)

        if cbz:
            if json["title"]:
                chapter_name = (
                    f"{self._manga_title} - Chapter {chapter} - {title}"
                )
            else:
                chapter_name = f"{self._manga_title} - Chapter {chapter}"
            self._to_cbz(chapter_name, chapter_path)

    def download_all(self, cbz=True):
        chapters = [
            chapter_id
            for chapters_list in self._get_chapters_list()
            for chapter_id in chapters_list.keys()
        ]
        for chapter_id in chapters:
            self._download_chapter_id(chapter_id)

        if not cbz:
            return

        folders = []
        with workdir(self._dl_folder):
            for item in Path(self._manga_title).iterdir():
                if item.is_dir():
                    folders.append(Path(item))

        for folder in folders:
            self._to_cbz(
                f"{self._manga_title} - {str(item).split('/')[1]}", folder
            )

    def download_volume(self, volume: int, cbz=True):
        for chapters in self._get_chapters_list():
            for chapter_id, chapter_details in chapters.items():
                if int(chapter_details["volume"]) == volume:
                    self._download_chapter_id(chapter_id)
        if cbz:
            volume_num = _to_zeroed_number(volume)
            volume_path = Path(f"{self._manga_title}/Volume {volume_num}")
            self._to_cbz(
                f"{self._manga_title} - Volume {volume_num}", volume_path
            )

    def download_chapter(self, chapter: int, cbz=False):
        for chapter_item in self._get_chapters_list():
            for chapter_id, chapter_details in chapter_item.items():
                try:
                    if int(chapter_details["chapter"]) == chapter:
                        return self._download_chapter_id(chapter_id, cbz)
                except ValueError:
                    if chapter_details["chapter"] == str(chapter):
                        return self._download_chapter_id(chapter_id, cbz)

        print(f"Unable to find the chapter {chapter}!")


if __name__ == "__main__":
    fire.Fire(MangaDex)
