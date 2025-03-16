import uuid
import shutil
from pathlib import Path
from image import Image


class Container:
    def __init__(self, status: str, cpu: float, memory: int):
        self.status = status
        self.cpu = cpu
        self.memory = memory
        self.id = None

    def to_dict(self):
        return {"status": self.status, "cpu": self.cpu, "memory": self.memory}

    def __repr__(self):
        return f"Container(status={self.status}, cpu={self.cpu}, memory={self.memory})"

    def prepare(self, container_image: Image):
        image_dir = container_image.get_image_dir()
        containers_dir = Path().home() / ".qnxtainer" / "containers"
        container_id = uuid.uuid4().hex
        container_dir = containers_dir / container_id
        shutil.copytree(image_dir, container_dir)
        self.id = container_id
        return container_id
