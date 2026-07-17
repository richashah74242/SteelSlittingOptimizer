from dataclasses import dataclass
from itertools import combinations_with_replacement


@dataclass(frozen=True)
class SlitPattern:
    """
    Represents one possible slitting pattern.
    """

    widths_mm: tuple[int, ...]

    @property
    def number_of_strips(self) -> int:
        return len(self.widths_mm)

    @property
    def total_product_width_mm(self) -> int:
        return sum(self.widths_mm)


class PatternGenerator:
    """
    Generates valid slitting patterns.

    A pattern is valid when:

        Sum(strip widths)
        +
        Kerf × (number of cuts)
        <= Coil width
    """

    def __init__(
        self,
        coil_width_mm: int,
        kerf_mm: float,
        max_knives: int,
    ):
        self.coil_width_mm = coil_width_mm
        self.kerf_mm = kerf_mm
        self.max_knives = max_knives

    def generate(
        self,
        available_widths: list[int],
    ) -> list[SlitPattern]:

        widths = sorted(
            set(available_widths)
        )

        patterns = []

        for number_of_strips in range(
            1,
            self.max_knives + 1,
        ):

            for combination in combinations_with_replacement(
                widths,
                number_of_strips,
            ):

                if self.is_valid(
                    combination
                ):
                    patterns.append(
                        SlitPattern(
                            widths_mm=combination
                        )
                    )

        return patterns

    def is_valid(
        self,
        widths: tuple[int, ...],
    ) -> bool:

        if not widths:
            return False

        number_of_cuts = len(widths) - 1

        total_width = (
            sum(widths)
            + (
                number_of_cuts
                * self.kerf_mm
            )
        )

        return (
            total_width
            <= self.coil_width_mm
        )

    def used_width(
        self,
        pattern: SlitPattern,
    ) -> float:

        number_of_cuts = (
            pattern.number_of_strips
            - 1
        )

        return (
            pattern.total_product_width_mm
            + number_of_cuts
            * self.kerf_mm
        )

    def scrap_width(
        self,
        pattern: SlitPattern,
    ) -> float:

        return (
            self.coil_width_mm
            - self.used_width(pattern)
        )