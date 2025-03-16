import logging
import tarfile
import os
from datetime import datetime
from pathlib import Path
import uuid


class Image:
    """
    Image class for QNXtainer.
    Represents a container image with name, tag, and associated files.
    """

    def __init__(self, name: str, tag: str, created_at: datetime = datetime.now()):
        self.name = name
        self.tag = tag
        self.created_at = created_at
        self.id = uuid.uuid4().hex

    def to_dict(self):
        """Convert image to a JSON-serializable dictionary"""
        return {
            "name": self.name,
            "tag": self.tag,
            "created_at": self.created_at.isoformat(),
            "id": self.id,
        }

    def __repr__(self):
        """String representation of the Image object"""
        return f"Image(name={self.name}, tag={self.tag}, id={self.id})"

    def get_image_dir(self) -> Path:
        """Get the directory where the image files are stored"""
        images_dir = Path().home() / ".qnxtainer" / "images"
        image_dir = images_dir / self.name / self.tag
        return image_dir

    def unpack_from(self, image_file_name: Path) -> Path:
        """Unpack a tarball into the image directory"""
        image_dir = self.get_image_dir()
        image_dir.mkdir(parents=True, exist_ok=True)

        try:
            with tarfile.open(image_file_name) as tar:
                tar.extractall(image_dir)
                logging.info(os.listdir(image_dir))

                run_script = image_dir / "image" / "run.sh"
                if run_script.exists():
                    os.chmod(run_script, 0o755)

            return image_dir
        except Exception as e:
            print(f"Error unpacking image: {e}")
            if image_dir.exists():
                import shutil

                shutil.rmtree(image_dir)
            raise
