from math import ceil

from .models import Coil, Order


class WeightEngine:
    """
    Handles all weight-related calculations.

    The basic assumption is that every slit strip runs
    through the full usable coil length.

    Therefore:

        Strip Weight =
            Strip Width / Coil Width
            × Coil Weight
    """

    def __init__(self, coil: Coil):
        self.coil = coil

    def weight_for_width(
        self,
        width_mm: int,
    ) -> float:
        """
        Calculate the weight of one full-width strip.
        """

        return (
            width_mm
            / self.coil.width_mm
            * self.coil.weight_kg
        )

    def strips_required(
        self,
        order: Order,
    ) -> int:
        """
        Calculate the minimum number of strips
        required to meet the requested weight.
        """

        strip_weight = self.weight_for_width(
            order.width_mm
        )

        return ceil(
            order.required_weight_kg
            / strip_weight
        )

    def produced_weight(
        self,
        width_mm: int,
        number_of_strips: int,
    ) -> float:
        """
        Calculate total production weight.
        """

        return (
            self.weight_for_width(width_mm)
            * number_of_strips
        )

    def overproduction_weight(
        self,
        order: Order,
        number_of_strips: int,
    ) -> float:
        """
        Calculate production above the requested weight.
        """

        produced = self.produced_weight(
            order.width_mm,
            number_of_strips,
        )

        return max(
            0.0,
            produced
            - order.required_weight_kg,
        )

    def overproduction_percent(
        self,
        order: Order,
        number_of_strips: int,
    ) -> float:
        """
        Calculate overproduction percentage.
        """

        if order.required_weight_kg == 0:
            return 0.0

        overproduction = (
            self.overproduction_weight(
                order,
                number_of_strips,
            )
        )

        return (
            overproduction
            / order.required_weight_kg
            * 100
        )