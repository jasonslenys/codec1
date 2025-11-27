#!/bin/bash
# Installation script for MP4 to H.264 Converter

set -e

echo "MP4 to H.264 Converter - Installation"
echo "======================================"
echo

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            echo "debian"
        elif command -v yum &> /dev/null; then
            echo "redhat"
        elif command -v pacman &> /dev/null; then
            echo "arch"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
echo "Detected OS: $OS"
echo

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PYTHON_VERSION"

# Check for FFmpeg
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -1)
    echo "FFmpeg found: $FFMPEG_VERSION"
else
    echo "FFmpeg not found. Installing..."

    case $OS in
        debian)
            echo "Installing FFmpeg via apt..."
            sudo apt-get update
            sudo apt-get install -y ffmpeg
            ;;
        redhat)
            echo "Installing FFmpeg via yum..."
            sudo yum install -y ffmpeg
            ;;
        arch)
            echo "Installing FFmpeg via pacman..."
            sudo pacman -S --noconfirm ffmpeg
            ;;
        macos)
            if command -v brew &> /dev/null; then
                echo "Installing FFmpeg via Homebrew..."
                brew install ffmpeg
            else
                echo "Error: Homebrew not found. Please install FFmpeg manually:"
                echo "  brew install ffmpeg"
                exit 1
            fi
            ;;
        *)
            echo "Error: Could not auto-install FFmpeg for your OS."
            echo "Please install FFmpeg manually from: https://ffmpeg.org/download.html"
            exit 1
            ;;
    esac

    echo "FFmpeg installed successfully!"
fi

echo

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo

# Install the package
echo "Installing mp4-h264-converter..."
pip3 install -e .

echo
echo "======================================"
echo "Installation complete!"
echo
echo "Usage:"
echo "  mp4convert input.mp4              # Convert a single file"
echo "  mp4convert input.mp4 -o out.mp4   # Specify output path"
echo "  mp4convert --batch ./videos/      # Batch convert directory"
echo
echo "For more options: mp4convert --help"
