# MP4 to H.264 Converter

A Python CLI tool to convert MP4 files of any size to MP4 with H.264 video codec.

## Features

- Convert any MP4 file to H.264 codec
- Handles files of any size with streaming conversion
- Real-time progress tracking
- Batch conversion for multiple files
- Configurable quality and encoding speed
- Cross-platform support (Linux, macOS, Windows)

## Requirements

- Python 3.8+
- FFmpeg

## Installation

### Quick Install (Linux/macOS)

```bash
./install.sh
```

### Manual Installation

1. Install FFmpeg:
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg

   # macOS
   brew install ffmpeg

   # Windows - Download from https://ffmpeg.org/download.html
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

## Usage

### Basic Conversion

```bash
# Convert a single file (output: input_h264.mp4)
mp4convert video.mp4

# Specify output path
mp4convert video.mp4 -o converted.mp4
```

### Quality Settings

```bash
# Higher quality (larger file)
mp4convert video.mp4 --crf 18

# Lower quality (smaller file)
mp4convert video.mp4 --crf 28

# Default is CRF 23 (good balance)
```

**CRF Values:**
- 0: Lossless
- 18-20: Visually lossless (large files)
- 21-23: High quality (recommended)
- 24-28: Good quality (smaller files)
- 29-51: Low quality (not recommended)

### Encoding Speed

```bash
# Faster encoding (larger file)
mp4convert video.mp4 --preset fast

# Slower encoding (smaller file, better compression)
mp4convert video.mp4 --preset slow
```

**Presets:** ultrafast, superfast, veryfast, faster, fast, medium (default), slow, slower, veryslow

### Batch Conversion

```bash
# Convert all MP4 files in a directory
mp4convert --batch ./videos/

# Specify output directory
mp4convert --batch ./videos/ --output-dir ./converted/

# Custom file pattern
mp4convert --batch ./videos/ --pattern "*.mov"
```

### Additional Options

```bash
# Overwrite existing files
mp4convert video.mp4 -y

# Quiet mode (no progress bar)
mp4convert video.mp4 -q

# Custom audio settings
mp4convert video.mp4 --audio-codec aac --audio-bitrate 192k
```

### All Options

```
usage: mp4convert [-h] [-o OUTPUT] [--crf 0-51] [--preset PRESET]
                  [--audio-codec AUDIO_CODEC] [--audio-bitrate AUDIO_BITRATE]
                  [-y] [--batch DIR] [--output-dir OUTPUT_DIR]
                  [--pattern PATTERN] [-q] [-v]
                  [input]

positional arguments:
  input                 Input MP4 file path

options:
  -h, --help            Show this help message and exit
  -o, --output OUTPUT   Output file path
  --crf 0-51            Constant Rate Factor (default: 23)
  --preset PRESET       Encoding speed preset (default: medium)
  --audio-codec         Audio codec (default: aac)
  --audio-bitrate       Audio bitrate (default: 128k)
  -y, --overwrite       Overwrite output file if exists
  --batch DIR           Batch convert directory
  --output-dir          Output directory for batch conversion
  --pattern             File pattern for batch (default: *.mp4)
  -q, --quiet           Suppress progress output
  -v, --version         Show version
```

## Python API

You can also use the converter as a Python library:

```python
from converter import MP4Converter

# Initialize converter
converter = MP4Converter()

# Convert a file
output_path = converter.convert(
    "input.mp4",
    "output.mp4",
    crf=23,
    preset="medium",
    overwrite=True,
    progress_callback=lambda p: print(f"Progress: {p:.1f}%")
)

# Get video information
info = converter.get_video_info("input.mp4")
print(f"Duration: {converter.get_duration('input.mp4')} seconds")

# Batch convert
output_files = converter.batch_convert(
    "./videos/",
    output_dir="./converted/",
    crf=23,
    preset="medium"
)
```

## License

MIT License
