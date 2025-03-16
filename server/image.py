import tarfile
from datetime import datetime
from pathlib import Path
import uuid


class Image:
    def __init__(self, name: str, tag: str, created_at: datetime = datetime.now()):
        self.name = name
        self.tag = tag
        self.created_at = created_at
        self.id = uuid.uuid4().hex

    def to_dict(self):
        return {
            "name": self.name,
            "tag": self.tag,
            "created_at": self.created_at.isoformat(),
            "id": self.id,
        }

    def __repr__(self):
        return f"Image(name={self.name}, tag={self.tag}, created_at={self.created_at}, id={self.id})"

    def get_image_dir(self) -> Path:
        images_dir = Path().home() / ".qnxtainer" / "images"
        image_dir = images_dir / self.image_name / self.image_tag
        return image_dir

    def unpack_from(self, image_file_name: Path) -> Path:
        image_dir = self.get_image_dir()
        image_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(image_file_name) as tar:
            tar.extractall(image_dir)
        return image_dir
