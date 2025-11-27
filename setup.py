from setuptools import setup, find_packages

setup(
    name="mp4-h264-converter",
    version="1.0.0",
    description="Convert MP4 files to MP4 with H.264 video codec",
    packages=find_packages(),
    install_requires=[
        "ffmpeg-python>=0.2.0",
        "tqdm>=4.65.0",
    ],
    entry_points={
        "console_scripts": [
            "mp4convert=converter.cli:main",
        ],
    },
    python_requires=">=3.8",
)
