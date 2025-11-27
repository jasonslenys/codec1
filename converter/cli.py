#!/usr/bin/env python3
"""Command-line interface for MP4 to H.264 converter."""

import argparse
import sys
from pathlib import Path

from tqdm import tqdm

from .converter import MP4Converter


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="mp4convert",
        description="Convert MP4 files to MP4 with H.264 video codec",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mp4convert input.mp4
  mp4convert input.mp4 -o output.mp4
  mp4convert input.mp4 --crf 18 --preset slow
  mp4convert --batch ./videos/ --output-dir ./converted/

Quality presets (--crf):
  18-20: Visually lossless (large files)
  21-23: High quality (recommended)
  24-28: Good quality (smaller files)

Speed presets (--preset):
  ultrafast: Fastest, largest file
  medium: Balanced (default)
  veryslow: Slowest, smallest file
        """,
    )

    parser.add_argument(
        "input",
        nargs="?",
        help="Input MP4 file path",
    )

    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: input_h264.mp4)",
    )

    parser.add_argument(
        "--crf",
        type=int,
        default=23,
        choices=range(0, 52),
        metavar="0-51",
        help="Constant Rate Factor for quality (default: 23, lower=better)",
    )

    parser.add_argument(
        "--preset",
        default="medium",
        choices=[
            "ultrafast", "superfast", "veryfast", "faster", "fast",
            "medium", "slow", "slower", "veryslow"
        ],
        help="Encoding speed preset (default: medium)",
    )

    parser.add_argument(
        "--audio-codec",
        default="aac",
        help="Audio codec (default: aac)",
    )

    parser.add_argument(
        "--audio-bitrate",
        default="128k",
        help="Audio bitrate (default: 128k)",
    )

    parser.add_argument(
        "-y", "--overwrite",
        action="store_true",
        help="Overwrite output file if it exists",
    )

    parser.add_argument(
        "--batch",
        metavar="DIR",
        help="Batch convert all MP4 files in directory",
    )

    parser.add_argument(
        "--output-dir",
        help="Output directory for batch conversion",
    )

    parser.add_argument(
        "--pattern",
        default="*.mp4",
        help="File pattern for batch conversion (default: *.mp4)",
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output",
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    return parser


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def convert_single(
    converter: MP4Converter,
    input_path: str,
    output_path: str,
    args: argparse.Namespace,
) -> None:
    """Convert a single file with progress display."""
    input_file = Path(input_path)
    input_size = input_file.stat().st_size

    print(f"Input:  {input_path}")
    print(f"Size:   {format_size(input_size)}")
    print(f"Output: {output_path}")
    print(f"CRF:    {args.crf} | Preset: {args.preset}")
    print()

    if args.quiet:
        progress_callback = None
    else:
        pbar = tqdm(
            total=100,
            unit="%",
            desc="Converting",
            bar_format="{l_bar}{bar}| {n:.1f}% [{elapsed}<{remaining}]",
        )

        def progress_callback(progress: float) -> None:
            pbar.n = progress
            pbar.refresh()

    try:
        result = converter.convert(
            input_path,
            output_path,
            crf=args.crf,
            preset=args.preset,
            audio_codec=args.audio_codec,
            audio_bitrate=args.audio_bitrate,
            overwrite=args.overwrite,
            progress_callback=progress_callback,
        )

        if not args.quiet:
            pbar.close()

        output_file = Path(result)
        output_size = output_file.stat().st_size
        ratio = (1 - output_size / input_size) * 100 if input_size > 0 else 0

        print()
        print(f"Conversion complete!")
        print(f"Output size: {format_size(output_size)} ({ratio:+.1f}%)")

    except Exception as e:
        if not args.quiet:
            pbar.close()
        raise e


def convert_batch(
    converter: MP4Converter,
    input_dir: str,
    args: argparse.Namespace,
) -> None:
    """Batch convert files in a directory."""
    input_dir = Path(input_dir)
    files = list(input_dir.glob(args.pattern))

    if not files:
        print(f"No files matching '{args.pattern}' found in {input_dir}")
        return

    print(f"Found {len(files)} file(s) to convert")
    print()

    output_dir = Path(args.output_dir) if args.output_dir else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, input_file in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {input_file.name}")

        output_file = output_dir / f"{input_file.stem}_h264.mp4"

        try:
            convert_single(
                converter,
                str(input_file),
                str(output_file),
                args,
            )
        except Exception as e:
            print(f"Error: {e}")
            continue

        print()

    print(f"Batch conversion complete! Processed {len(files)} file(s)")


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.input and not args.batch:
        parser.print_help()
        return 1

    try:
        converter = MP4Converter()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    try:
        if args.batch:
            convert_batch(converter, args.batch, args)
        else:
            output_path = args.output
            if not output_path:
                input_file = Path(args.input)
                output_path = str(input_file.parent / f"{input_file.stem}_h264.mp4")

            convert_single(converter, args.input, output_path, args)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except FileExistsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nConversion cancelled by user")
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())
