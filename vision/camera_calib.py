
import yaml
from dataclasses import dataclass

@dataclass
class CameraCalib:
    camera_matrix: list | None = None
    dist_coeffs: list | None = None

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump({"camera_matrix": self.camera_matrix, "dist_coeffs": self.dist_coeffs}, f)

    @classmethod
    def load(cls, path: str):
        with open(path, "r", encoding="utf-8") as f:
            d = yaml.safe_load(f) or {}
        return cls(camera_matrix=d.get("camera_matrix"), dist_coeffs=d.get("dist_coeffs"))
