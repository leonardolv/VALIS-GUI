from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Config:
    project_name: str = "New Project"
    rigid_registration: bool = True
    non_rigid_registration: bool = True
    max_image_size: int = 2048
    match_threshold: float = 0.35
    use_gpu: bool = False
