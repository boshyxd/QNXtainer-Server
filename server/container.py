from datetime import date
import json

class Container:
    def __init__(self, status: str, cpu: float, memory: int):
        self.status = status
        self.cpu = cpu
        self.memory = memory
    
    def to_dict(self):
        return {
            "status": self.status,
            "cpu": self.cpu,
            "memory": self.memory
        }
    
    def __repr__(self):
        return f"Container(status={self.status}, cpu={self.cpu}, memory={self.memory})"
