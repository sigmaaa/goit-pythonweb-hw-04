import argparse
import asyncio

import aioshutil
from aiopath import AsyncPath
from logger import logger


async def get_unique_dest(dest: AsyncPath) -> AsyncPath:
    """Generate a unique destination path if the file already exists."""
    counter = 1
    new_dest = dest
    while await new_dest.exists():
        new_dest = dest.with_name(f"{dest.stem}_{counter}{dest.suffix}")
        counter += 1
    return new_dest


async def copy_file(source: AsyncPath, dest: AsyncPath):
    """Copy a single file into the destination folder by extension."""
    file_extension = source.suffix.lstrip(".") or "no_extension"
    final_dest_folder = dest / file_extension
    await final_dest_folder.mkdir(parents=True, exist_ok=True)

    final_dest = await get_unique_dest(final_dest_folder / source.name)
    await aioshutil.copy2(source, final_dest)

    logger.info(f"{source} copied to {final_dest}")


async def read_folder(source: AsyncPath, dest: AsyncPath):
    """Recursively read source folder and copy files to destination by extension."""
    tasks = []

    async for entry in source.iterdir():
        if await entry.is_file():
            tasks.append(copy_file(entry, dest))
        elif await entry.is_dir():
            tasks.append(read_folder(entry, dest))

    if tasks:
        await asyncio.gather(*tasks)


async def main_async():
    parser = argparse.ArgumentParser(
        prog="FileSorter",
        description="Sort files from source folder into destination folder by extension",
        epilog="Example: python file_util.py /Path/to/source /Path/to/dest",
    )

    parser.add_argument("source_folder", type=str, help="Folder with input files")
    parser.add_argument("dest_folder", type=str, help="Folder to save sorted files")
    args = parser.parse_args()

    source = AsyncPath(args.source_folder)
    dest = AsyncPath(args.dest_folder)

    if not await source.exists() or not await source.is_dir():
        logger.info("Source folder does not exist or is not a directory.")
        return

    await dest.mkdir(parents=True, exist_ok=True)
    logger.info(f"Sorting files from {source} into {dest}...")

    await read_folder(source, dest)
    logger.info("Sorting completed!")


if __name__ == "__main__":
    asyncio.run(main_async())
