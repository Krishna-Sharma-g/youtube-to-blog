import subprocess, json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple

def download_best_audio(url: str) -> Tuple[Path, str]:
    """
    Use yt-dlp to fetch the highest-quality audio only.
    Returns (path_to_file, title).
    """
    with TemporaryDirectory() as tmp:
        json_path = Path(tmp) / "meta.json"
        # --print-json dumps video metadata
        cmd = [
            "yt-dlp",
            "-f", "bestaudio",
            "-o", f"{tmp}/audio.%(ext)s",
            "--print-json",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        meta   = json.loads(result.stdout.splitlines()[0])
        title  = meta["title"]
        # yt-dlp already saved the file; find it
        audio_file = next(Path(tmp).glob("audio.*"))
        # move to project cache
        cache_dir = Path(".cache/audio")
        cache_dir.mkdir(parents=True, exist_ok=True)
        final_path = cache_dir / f"{meta['id']}{audio_file.suffix}"
        audio_file.rename(final_path)
        return final_path, title
