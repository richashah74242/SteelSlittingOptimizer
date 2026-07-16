from dataclasses import dataclass
from typing import List


@dataclass
class Coil:
    thickness_mm: float
    width_mm: int
    weight_kg: float
    kerf_mm: float


@dataclass
class Order:
    width_mm: int
    required_weight_kg: float


@dataclass
class Settings:
    allow_overproduction: bool
    max_overproduction_percent: float
    max_knives: int
    allow_stock_production: bool


@dataclass
class InputData:
    coil: Coil
    orders: List[Order]
    stock_widths_mm: List[int]
    settings: Settings