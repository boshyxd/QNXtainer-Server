from image import Image
from container import Container
import json


class Data:
    def __init__(
        self,
        images: list[Image] | None = None,
        containers: list[Container] | None = None,
    ):
        self.images = images if images else []
        self.containers = containers if containers else []

    def add_image(self, image: Image):
        self.images.append(image)

    def add_container(self, container: Container):
        self.containers.append(container)

    def to_json(self):
        return json.dumps(
            {
                "images": [img.to_dict() for img in self.images],
                "containers": [ctr.to_dict() for ctr in self.containers],
            }
        )

    def __repr__(self):
        return f"Data(images={self.images}, containers={self.containers})"
