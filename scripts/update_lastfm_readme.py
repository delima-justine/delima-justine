import json
import os
import re
from urllib.request import Request, urlopen

README_PATH = os.environ.get("README_PATH", "README.md")
START_MARKER = "<!-- DEEZER:START -->"
END_MARKER = "<!-- DEEZER:END -->"


def get_track_data():
    track_id = os.environ.get("DEEZER_TRACK_ID")
    if not track_id:
        raise RuntimeError("DEEZER_TRACK_ID environment variable is required.")

    url = f"https://api.deezer.com/track/{track_id}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8")

    data = json.loads(payload)
    if "error" in data:
        raise RuntimeError(f"Deezer API error: {data['error']['message']}")

    return data


def build_block(track):
    title = track.get("title", "Unknown Track")
    artist = track.get("artist", {}).get("name", "Unknown Artist")
    album = track.get("album", {}).get("title", "")
    image = track.get("album", {}).get("cover_medium") or track.get("album", {}).get("cover_big") or ""
    link = track.get("link", "https://www.deezer.com/")
    preview = track.get("preview") or ""

    album_line = f"<br /><em>Album: {album}</em>" if album else ""
    image_tag = (
        f'<a href="{link}" target="_blank" rel="noreferrer">'
        f'<img src="{image}" alt="{title} by {artist}" width="220" /></a>'
        if image
        else ""
    )
    preview_button = (
        f'<audio controls preload="none" style="width:100%; margin-top:10px;">'
        f'<source src="{preview}" type="audio/mpeg" />'
        "Your browser does not support the audio element."
        f'</audio>'
        if preview
        else ""
    )

    return (
        f"{START_MARKER}\n"
        "<div align=\"center\">\n"
        f"  {image_tag}\n"
        "  <br />\n"
        f"  <strong>🎵 On Repeat:</strong> <a href=\"{link}\" target=\"_blank\" rel=\"noreferrer\">{title}</a> by <b>{artist}</b>\n"
        f"  {album_line}\n"
        f"  {preview_button}\n"
        "</div>\n"
        f"{END_MARKER}"
    )


def update_readme(content, block):
    pattern = re.compile(rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}\s*", re.DOTALL)
    if pattern.search(content):
        return pattern.sub(block + "\n", content, count=1)

    title = "# 👋 Hello, I'm Justine!\n"
    if title in content:
        return content.replace(title, title + "\n" + block + "\n", 1)

    return content.rstrip() + "\n\n" + block + "\n"


def main():
    track = get_track_data()
    block = build_block(track)

    with open(README_PATH, "r", encoding="utf-8") as fh:
        content = fh.read()

    updated = update_readme(content, block)

    with open(README_PATH, "w", encoding="utf-8") as fh:
        fh.write(updated)

    print(f"Updated README using Deezer track: {track['title']} by {track['artist']['name']}")


if __name__ == "__main__":
    main()
