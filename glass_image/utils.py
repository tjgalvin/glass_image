"""Utility functions to help with processing
"""
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from glass_image.logging import logger

def zip_folder(in_path: Path, out_zip: Optional[Path] = None) -> None:
    """Zip a directory and remove the original. 

    Args:
        in_path (Path): The path that will be zipped up.
        out_zip (Path, optional): Name of the output file. A zip extension will be added. Defaults to None.
    """

    out_zip = in_path if out_zip is None else out_zip
    out_zip = Path('.') / out_zip.name

    logger.info(f"Zipping {in_path}.")
    shutil.make_archive(
        str(out_zip),
        'zip',
        base_dir=str(in_path)
    )
    remove_files_folders([in_path])


def ensure_dir_exists(target_dir: Path) -> None:
    """Check to ensure that a directory exists. is intended for
    confirming output directories are in placce. 

    Args:
        target_dir (Path): Directory that needs to exist

    Raises:
        FileNotFoundError: Raised when no file or folder is found
        ValueError: Raised when a file is found and it not a directory
    """
    if not target_dir.exists():
        raise FileNotFoundError(f"Miriad file {target_dir} not found. ")

    if not target_dir.is_dir():
        raise ValueError(f"Although {target_dir} exists, it does not appear to be a miriad directory. ")


def remove_files_folders(paths_to_remove: List[Path]) -> List[Path]:
    """Will remove a set of paths from the file system. If a Path points
    to a folder, it will be recursively removed. Otherwise it is simply
    unlinked. 

    Args:
        paths_to_remove (List[Path]): Set of Paths that will be removed

    Returns:
        List[Path]: Set of Paths that were removed
    """
    
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
