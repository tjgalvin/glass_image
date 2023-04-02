"""Utility functions to help with processing
"""
import shutil
import subprocess
from pathlib import Path
from typing import List

from glass_image.logging import logger

def zip_folder(in_path: Path, out_zip: Path) -> None:

            logger.info(f"Zipping {in_path}.")
            shutil.make_archive(
                str(out_zip),
                'zip',
                str(in_path)
            )
            shutil.rmtree(in_path)


def ensure_dir_exists(target_dir: Path) -> None:
    if not target_dir.exists():
        raise FileNotFoundError(f"Miriad file {target_dir} not found. ")

    if not target_dir.is_dir():
        raise ValueError(f"Although {target_dir} exists, it does not appear to be a miriad directory. ")


def remove_files_folders(paths_to_remove: List[Path]) -> List[Path]:
    
    files_removed = []
    
    file: Path
    for file in paths_to_remove:
        file = Path(file)
        if not file.exists():
            logger.debug(f"{file} does not exist. Skipping, ")
            continue
        
        if file.is_dir():
            logger.info(f"Removing folder {str(file)}")
            shutil.rmtree(file)
        else:
            logger.info(f"Removing file {file}.")
            file.unlink()

        files_removed.append(file)
        
    return files_removed

    
def call(*args, **kwargs):
    """Wrapper for subprocess.Popen to log the command and output
    All arguments are passed to subprocess.Popen
    """
    # Call a subprocess, print the command to stdout
    logger.info(" ".join(args[0]))
    process = subprocess.Popen(
        *args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs
    )

    with process.stdout:
        try:
            for line in iter(process.stdout.readline, b""):
                logger.info(line.decode("utf-8").strip())

        except subprocess.CalledProcessError as e:
            logger.error(f"{str(e)}")
