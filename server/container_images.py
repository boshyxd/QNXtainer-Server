from pathlib import Path
import tarfile
import uuid
import shutil


def get_image_dir(image_name: str, image_tag: str = "latest") -> Path:
    images_dir = Path().home() / ".qnxtainer" / "images"
    image_dir = images_dir / image_name / image_tag
    return image_dir


def unpack_image(
    image_file_name: Path, image_name: str, image_tag: str = "latest"
) -> Path:
    image_dir = get_image_dir(image_name, image_tag)
    image_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(image_file_name) as tar:
        tar.extractall(image_dir)
    return image_dir


def prep_container(image_name: str, image_tag: str = "latest") -> str:
    image_dir = get_image_dir(image_name, image_tag)
    containers_dir = Path().home() / ".qnxtainer" / "containers"
    container_id = uuid.uuid4().hex
    container_dir = containers_dir / container_id
    shutil.copytree(image_dir, container_dir)
    return container_id
