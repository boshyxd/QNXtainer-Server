from image import Image
from container import Container
import threading


class Data:
    def __init__(self):
        self.lock = threading.Lock()
        self.images = dict()
        self.containers = dict()

    def add_image(self, image: Image):
        with self.lock:
            self.images[f"{image.name}:{image.tag}"] = image
            self.images[image.id] = image

    def add_container(self, container: Container):
        with self.lock:
            self.containers[container.id] = container

    def get_image_by_name(
        self, image_name: str, image_tag: str = "latest"
    ) -> Image | None:
        with self.lock:
            return self.images.get(f"{image_name}:{image_tag}", None)

    def get_image_by_id(self, image_id: str) -> Image | None:
        with self.lock:
            return self.images.get(image_id, None)

    def get_container_by_id(self, container_id: str) -> Container | None:
        with self.lock:
            return self.containers.get(container_id, None)

    def to_json(self):
        """Convert data to a JSON-serializable dictionary"""
        unique_images = {img.id: img for img in self.images.values()}.values()

        return {
            "images": [img.to_dict() for img in unique_images],
            "containers": [ctr.to_dict() for ctr in self.containers.values()],
        }

    def __repr__(self):
        return (
            f"Data(images={len(self.images) // 2}, containers={len(self.containers)})"
        )
