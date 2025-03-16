import stat
import uuid
import shutil
import multiprocessing
import subprocess
from pathlib import Path
from image import Image


class Container:
    def __init__(self, status: str, cpu: float, memory: int):
        self.status = status
        self.cpu = cpu
        self.memory = memory
        self.image = None
        self.id = None
        self.process = None
        self.container_dir = None
        self.runner = None

    def to_dict(self):
        return {"status": self.status, "cpu": self.cpu, "memory": self.memory}

    def __repr__(self):
        return f"Container(status={self.status}, cpu={self.cpu}, memory={self.memory})"

    def prepare(self, container_image: Image) -> str:
        image_dir = container_image.get_image_dir() / "image"
        containers_dir = Path().home() / ".qnxtainer" / "containers"
        container_id = uuid.uuid4().hex
        self.id = container_id
        self.image = container_image
        self.container_dir = containers_dir / container_id
        shutil.copytree(image_dir, self.container_dir)
        container_runner = self.container_dir / "run.sh"
        container_runner.chmod(stat.S_IRWXU)
        self.runner = container_runner
        return container_id

    def _start(self):
        subprocess.run(str(self.runner))

    def start(self):
        mp_context = multiprocessing.get_context("spawn")
        self.process = mp_context.Process(target=self._start)
        self.process.start()

    def stop(self):
        self.process.terminate()
        shutil.rmtree(self.container_dir)
