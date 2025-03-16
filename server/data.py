from image import Image
from container import Container
import json


class Data:
    def __init__(
        self,
    ):
        self.images = dict()
        self.containers = dict()

    def add_image(self, image: Image):
        self.images[f"{image.name}:{image.tag}"] = image
        self.images[image.id] = image

    def add_container(self, container: Container):
        self.containers[container.id] = container

    def get_image_by_name(
        self, image_name: str, image_tag: str = "latest"
    ) -> Image | None:
        return self.images.get(f"{image_name}:{image_tag}", None)

    def get_image_by_id(self, image_id: str) -> Image | None:
        return self.images.get(image_id, None)

    def to_json(self):
        """Convert data to a JSON-serializable dictionary"""
        return {
            "images": [img.to_dict() for img in self.images.values()],
            "containers": [ctr.to_dict() for ctr in self.containers.values()],
        }

    def __repr__(self):
        return f"Data(images={self.images}, containers={self.containers})"
