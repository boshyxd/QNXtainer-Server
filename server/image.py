from datetime import date
import json

class Image:
    def __init__(self, name: str, tag: str, created_at: date, description: str):
        self.name = name
        self.tag = tag
        self.created_at = created_at
        self.description = description
    
    def to_dict(self):
        return {
            "name": self.name,
            "tag": self.tag,
            "created_at": self.created_at.isoformat(),
            "description": self.description
        }
    
    def __repr__(self):
        return f"Image(name={self.name}, tag={self.tag}, created_at={self.created_at}, description={self.description})"
