#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###################################################
#
# make_package.py
#
# In order to facilitate easy packaging and deployment of readalongs,
# the make_package module takes a standard output directory from `readalongs align`
# and outputs a single html file with assets enceded using base64 in-line in the html.
#
# Note, this is not the optimal deployment. The ReadAlongs-WebComponent is already very portable
# and should be used directly as a webcomponent. However, in some situations a single-file
# is preferred as a low-cost, portable implementation.
#
#
###################################################

import os
from base64 import b64encode
from mimetypes import guess_type

import requests
from lxml import etree

from readalongs.log import LOGGER

BASIC_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=5.0">
  <title>{title}</title>
  <script type="module" src="https://unpkg.com/@roedoejet/readalong/dist/read-along/read-along.esm.js"></script>
  <script nomodule src="https://unpkg.com/@roedoejet/readalong/dist/read-along/read-along.js"></script>
  <link href="https://fonts.googleapis.com/css?family=Lato|Material+Icons|Material+Icons+Outlined" rel="stylesheet">
</head>
<body>
    <read-along text="{text}" alignment="{alignment}" audio="{audio}" theme="{theme}" useAssetsFolder="false">
        <span slot='read-along-header'>{header}</span>
        <span slot='read-along-subheader'>{subheader}</span>
    </read-along>
</body>
</html>
"""


def encode_from_path(path: str) -> str:
    """Encode file from bytes to b64 string with data and mime signature

    Args:
        path (str): path to file

    Returns:
        str: base64 string with data and mime signature
    """
    with open(path, "rb") as f:
        path_bytes = f.read()
    if path.endswith("xml"):
        root = etree.fromstring(path_bytes)
        for img in root.xpath("//graphic"):
            url = img.get("url")
            res = requests.get(url) if url.startswith("http") else None
            mime = guess_type(url)
            if os.path.exists(url):
                with open(url, "rb") as f:
                    img_bytes = f.read()
                img_b64 = str(b64encode(img_bytes), encoding="utf8")
            elif res and res.status_code == 200:
                img_b64 = str(b64encode(res.content), encoding="utf8")
            else:
                LOGGER.warn(
                    f"The image declared at {url} could not be found. Please check that it exists."
                )
                continue
            img.attrib["url"] = f"data:{mime[0]};base64,{img_b64}"
        path_bytes = etree.tostring(root)
    b64 = str(b64encode(path_bytes), encoding="utf8")
    mime = guess_type(path)
    if path.endswith(
        ".m4a"
    ):  # hack to get around guess_type choosing the wrong mime type for .m4a files
        # TODO: Check other popular audio formats, .wav, .mp3, .ogg, etc...
        mime = ("audio/mp4", None)
    return f"data:{mime[0]};base64,{b64}"


def create_web_component_html(
    text_path: str,
    alignment_path: str,
    audio_path: str,
    title="Title goes here",
    header="Header goes here",
    subheader="Subheader goes here",
    theme="light",
) -> str:
    return BASIC_HTML.format(
        text=encode_from_path(text_path),
        alignment=encode_from_path(alignment_path),
        audio=encode_from_path(audio_path),
        title=title,
        header=header,
        subheader=subheader,
        theme=theme,
    )
