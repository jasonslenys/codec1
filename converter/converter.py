"""Core converter module for MP4 to H.264 conversion."""

import os
import subprocess
import shutil
import re
from pathlib import Path
from typing import Optional, Callable


class MP4Converter:
    """Converts MP4 files to MP4 with H.264 video codec."""

    def __init__(self, ffmpeg_path: Optional[str] = None):
        """
        Initialize the converter.

        Args:
            ffmpeg_path: Optional path to FFmpeg binary. If not provided,
                        will search in PATH.
        """
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg()
        if not self.ffmpeg_path:
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg:\n"
                "  Ubuntu/Debian: sudo apt install ffmpeg\n"
                "  macOS: brew install ffmpeg\n"
                "  Windows: Download from https://ffmpeg.org/download.html"
            )

    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg in system PATH."""
        return shutil.which("ffmpeg")

    def get_video_info(self, input_path: str) -> dict:
        """
        Get information about the input video file.

        Args:
            input_path: Path to the input video file.

        Returns:
            Dictionary containing video information.
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(input_path)
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            import json
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get video info: {e.stderr}")
        except Exception as e:
            raise RuntimeError(f"Failed to parse video info: {e}")

    def get_duration(self, input_path: str) -> float:
        """
        Get the duration of the video in seconds.

        Args:
            input_path: Path to the input video file.

        Returns:
            Duration in seconds.
        """
        info = self.get_video_info(input_path)
        try:
            return float(info.get("format", {}).get("duration", 0))
        except (ValueError, TypeError):
            return 0

    def convert(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        crf: int = 23,
        preset: str = "medium",
        audio_codec: str = "aac",
        audio_bitrate: str = "128k",
        overwrite: bool = False,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> str:
        """
        Convert an MP4 file to MP4 with H.264 video codec.

        Args:
            input_path: Path to the input MP4 file.
            output_path: Path for the output file. If not provided,
                        will append '_h264' to the input filename.
            crf: Constant Rate Factor (0-51). Lower = better quality, larger file.
                 Default 23 is a good balance. Range: 18-28 recommended.
            preset: Encoding speed preset. Slower = better compression.
                   Options: ultrafast, superfast, veryfast, faster, fast,
                           medium, slow, slower, veryslow
            audio_codec: Audio codec to use. Default 'aac'.
            audio_bitrate: Audio bitrate. Default '128k'.
            overwrite: Whether to overwrite existing output file.
            progress_callback: Optional callback function that receives
                              progress percentage (0-100).

        Returns:
            Path to the output file.
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_h264.mp4"
        output_path = Path(output_path)

        if output_path.exists() and not overwrite:
            raise FileExistsError(
                f"Output file already exists: {output_path}. "
                "Use overwrite=True to replace."
            )

        duration = self.get_duration(str(input_path))

        cmd = [
            self.ffmpeg_path,
            "-i", str(input_path),
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", preset,
            "-c:a", audio_codec,
            "-b:a", audio_bitrate,
            "-movflags", "+faststart",
            "-progress", "pipe:1",
            "-nostats",
        ]

        if overwrite:
            cmd.append("-y")
        else:
            cmd.append("-n")

        cmd.append(str(output_path))

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        time_pattern = re.compile(r"out_time_ms=(\d+)")

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break

            match = time_pattern.search(line)
            if match and duration > 0 and progress_callback:
                current_time = int(match.group(1)) / 1_000_000
                progress = min(100, (current_time / duration) * 100)
                progress_callback(progress)

        return_code = process.wait()

        if return_code != 0:
            stderr = process.stderr.read()
            raise RuntimeError(f"FFmpeg conversion failed: {stderr}")

        if progress_callback:
            progress_callback(100)

        return str(output_path)

    def batch_convert(
        self,
        input_dir: str,
        output_dir: Optional[str] = None,
        pattern: str = "*.mp4",
        **kwargs,
    ) -> list:
        """
        Convert all MP4 files in a directory.

        Args:
            input_dir: Directory containing input files.
            output_dir: Directory for output files. If not provided,
                       files will be saved in the input directory.
            pattern: Glob pattern for input files. Default '*.mp4'.
            **kwargs: Additional arguments passed to convert().

        Returns:
            List of output file paths.
        """
        input_dir = Path(input_dir)
        if not input_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {input_dir}")

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = input_dir

        input_files = list(input_dir.glob(pattern))
        if not input_files:
            return []

        output_files = []
        for input_file in input_files:
            output_file = output_dir / f"{input_file.stem}_h264.mp4"
            result = self.convert(
                str(input_file),
                str(output_file),
                **kwargs,
            )
            output_files.append(result)

        return output_files
