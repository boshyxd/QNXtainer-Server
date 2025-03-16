import stat
import resource
import uuid
import shutil
import multiprocessing
import subprocess
from pathlib import Path
from image import Image


class Container:
    def __init__(self, status: str, cpu: float = -1, memory: int = -1):
        self.status = status
        self.cpu = cpu
        self.memory = memory
        self.image = None
        self.id = None
        self.name = None
        self.process = None
        self.container_dir = None
        self.runner = None

    def to_dict(self):
        image_info = None
        if self.image:
            image_info = {
                "id": self.image.id,
                "name": self.image.name,
                "tag": self.image.tag
            }
        
        return {
            "id": self.id,
            "name": self.name or self.id,
            "status": self.status, 
            "cpu": self.cpu, 
            "memory": self.memory,
            "image": image_info
        }

    def __repr__(self):
        return f"Container(id={self.id}, name={self.name}, status={self.status}, cpu={self.cpu}, memory={self.memory})"

    def prepare(self, container_image: Image) -> str:
        image_dir = container_image.get_image_dir() / "image"
        containers_dir = Path().home() / ".qnxtainer" / "containers"
        container_id = uuid.uuid4().hex
        self.id = container_id
        self.image = container_image
        self.container_dir = containers_dir / container_id
        
        if not image_dir.exists():
            self.container_dir.mkdir(parents=True, exist_ok=True)
            mock_runner = self.container_dir / "run.sh"
            with open(mock_runner, 'w') as f:
                f.write("#!/bin/sh\necho 'Mock container running'\nsleep 60\n")
            mock_runner.chmod(stat.S_IRWXU)
            self.runner = mock_runner
        else:
            shutil.copytree(image_dir, self.container_dir)
            container_runner = self.container_dir / "run.sh"
            container_runner.chmod(stat.S_IRWXU)
            self.runner = container_runner
        
        self.status = "prepared"
        return container_id

    def _start(self):
        soft_mem_limit, hard_mem_limit = resource.getrlimit(resource.RLIMIT_AS)
        soft_cpu_limit, hard_cpu_limit = resource.getrlimit(resource.RLIMIT_CPU)

        resource.setrlimit(resource.RLIMIT_AS, (self.memory * 1024 * 1024, hard_mem_limit))
        resource.setrlimit(resource.RLIMIT_CPU, (self.cpu, hard_cpu_limit))
        
        subprocess.run(self.runner.as_posix())

    def start(self):
        mp_context = multiprocessing.get_context("spawn")
        self.process = mp_context.Process(target=self._start)
        self.process.start()
        self.status = "running"
        print(f"Container {self.id} started")

    def stop(self):
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.kill()
        
        if self.container_dir and self.container_dir.exists():
            shutil.rmtree(self.container_dir)
        
        self.status = "stopped"
        print(f"Container {self.id} stopped")