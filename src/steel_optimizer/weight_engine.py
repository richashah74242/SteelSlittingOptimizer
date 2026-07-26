from .models import Coil


STEEL_DENSITY_KG_PER_M3 = 7850.0


class WeightEngine:

    def __init__(
        self,
        coil: Coil,
    ):

        self.coil = coil

    def weight_per_meter(
        self,
        width_mm: int,
    ) -> float:

        width_m = (
            width_mm
            / 1000.0
        )

        thickness_m = (
            self.coil.thickness_mm
            / 1000.0
        )

        return (
            width_m
            * thickness_m
            * STEEL_DENSITY_KG_PER_M3
        )

    def weight_for_width(
        self,
        width_mm: int,
        length_m: float,
    ) -> float:

        return (
            self.weight_per_meter(
                width_mm
            )
            * length_m
        )