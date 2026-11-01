import json
import os
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

README_PATH = os.environ.get("README_PATH", "README.md")
START_MARKER = "<!-- LASTFM:START -->"
END_MARKER = "<!-- LASTFM:END -->"


def get_track_data():
    response_path = os.environ.get("LASTFM_RESPONSE_PATH")

    if response_path:
        with open(response_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    username = os.environ.get("LASTFM_USERNAME")
    api_key = os.environ.get("LASTFM_API_KEY")

    if not username or not api_key:
        raise RuntimeError("LASTFM_USERNAME and LASTFM_API_KEY environment variables are required.")

    params = urlencode({
        "method": "user.getRecentTracks",
        "user": username,
        "api_key": api_key,
        "limit": "1",
        "format": "json",
    })
    url = f"https://ws.audioscrobbler.com/2.0/?{params}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8")

    return json.loads(payload)


def parse_track(payload):
    recent_tracks = payload.get("recenttracks", {})
    tracks = recent_tracks.get("track")
    if not isinstance(tracks, list) or not tracks:
        raise ValueError("No recent tracks found for this Last.fm user.")

    track = tracks[0]
    artist_data = track.get("artist")
    if isinstance(artist_data, dict):
        artist = artist_data.get("#text", "Unknown artist")
    else:
        artist = str(artist_data or "Unknown artist")

    name = str(track.get("name", "Unknown track"))
    album = str(track.get("album", {}).get("#text", "")) if isinstance(track.get("album"), dict) else ""
    url = str(track.get("url", "https://www.last.fm/"))
    images = track.get("image", [])
    image_url = ""
    for image in reversed(images):
        if isinstance(image, dict) and image.get("#text"):
            image_url = image["#text"]
            break

    now_playing = False
    attr = track.get("@attr") or {}
    if str(attr.get("nowplaying", "")).lower() == "true":
        now_playing = True

    return {
        "name": name,
        "artist": artist,
        "album": album,
        "url": url,
        "image": image_url,
        "now_playing": now_playing,
    }


def build_block(track):
    status = "Now Playing" if track["now_playing"] else "Last Played"
    emoji = "🎵" if track["now_playing"] else "🕘"
    album_line = f"<br /><em>Album: {track['album']}</em>" if track.get("album") else ""
    image_tag = (
        f'<a href="{track["url"]}" target="_blank" rel="noreferrer">'
        f'<img src="{track["image"]}" alt="{track["name"]} by {track["artist"]}" width="220" /></a>'
        if track.get("image")
        else ""
    )

    return (
        f"{START_MARKER}\n"
        "<div align=\"center\">\n"
        f"  {image_tag}\n"
        "  <br />\n"
        f"  <strong>{emoji} {status}:</strong> <a href=\"{track['url']}\" target=\"_blank\" rel=\"noreferrer\">{track['name']}</a> by <b>{track['artist']}</b>\n"
        f"  {album_line}\n"
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
    payload = get_track_data()
    track = parse_track(payload)
    block = build_block(track)

    with open(README_PATH, "r", encoding="utf-8") as fh:
        content = fh.read()

    updated = update_readme(content, block)

    with open(README_PATH, "w", encoding="utf-8") as fh:
        fh.write(updated)

    print(f"Updated README using Last.fm track: {track['name']} by {track['artist']}")


if __name__ == "__main__":
    main()
