# Mangadex-dl

A Small Python utility based en python-requests and python-fire to help you download your favorite mangas from the MangaDex API.  
It's intended to be used as a CLI but could also be used as a library.

It's voluntarily synchronuous to avoid overloading MangaDex's servers.

## Installation

```bash
git clone $REPOSITORY
pip install -r requirements.txt
```

## Usage

```
NAME
    mangadex-dl - Small CLI utility to help you download Mangas from Mangadex.org and let's you compress them as a .cbz file once downloaded to read on eReaders.

SYNOPSIS
    mangadex-dl --manga_id=MANGA_ID <flags>

DESCRIPTION
    All methods have a cbz optional argument.
    If True, it'll compress the final result to a cbz file.
    By volume for "all" and "volume". By chapter for "chapter".

    Additionnal flags:
        --lang_code: Default to "gb". The lang code for the language you want
        to retrieve your manga in.

        --dl_folder: Default to "dl". The path to the folder you want your
        downloads to occur in.

        --dest_folder: Default to "dl/cbz". The path where to put the
        compressed .cbz file if cbz is set to True.

    Examples:
        Download everything:
        mangadex-dl --manga_id=35855 --download_all

        Download a volume:
        mangadex-dl --manga_id=35855 --download_volume 10

        Download a chapter:
        mangadex-dl --manga_id=35855 --download_chapter 156.5

ARGUMENTS
    MANGA_ID

FLAGS
    --lang_code=LANG_CODE
    --dl_folder=DL_FOLDER
    --dest_folder=DEST_FOLDER
```

## Known issues

- No tests
- Not enough error catching

## Issues & Contribution

All bug report, packaging requests, features requests or PR are accepted.  
I mainly created this script for my personal usage but I'll be happy yo hear about your needs.
