from collections import Counter
from dataclasses import dataclass
from typing import Optional

from .models import InputData
from .weight_engine import WeightEngine


@dataclass
class SlittingPlan:

    customer_widths: Counter
    stock_widths: Counter

    product_width_mm: int
    kerf_width_mm: int
    unused_width_mm: int

    customer_weight_kg: float
    stock_weight_kg: float

    customer_overproduction_kg: float
    scrap_weight_kg: float

    total_produced_weight_kg: float
    total_runs: int
    
    @property
    def produced_widths(self):

        result = Counter()

        result.update(
            self.customer_widths
        )

        result.update(
            self.stock_widths
        )

        return result
    
    @property
    def used_width_mm(self):

        return (
            self.product_width_mm
            + self.kerf_width_mm
        )
    @property
    def scrap_width_mm(self):

        return self.unused_width_mm

class SlittingOptimizer:

    def __init__(
        self,
        input_data: InputData,
        patterns=None,
    ):

        self.input_data = input_data

        self.coil = input_data.coil

        self.engine = WeightEngine(
            self.coil
        )

        self.orders = (
            input_data.orders
        )

        self.stock_widths = sorted(
            set(
                input_data.stock_widths_mm
            )
        )

        self.customer_widths = sorted(
            set(
                order.width_mm
                for order in self.orders
            )
        )

        self.usable_width = (
            self.coil.width_mm
            - self.coil.kerf_mm
        )

    def optimize(self) -> SlittingPlan:

        all_widths = (
            self.customer_widths
            + self.stock_widths
        )

        minimum_required_counts = (
            self._calculate_minimum_customer_counts()
        )

        maximum_customer_counts = (
            self._calculate_maximum_customer_counts()
        )

        best_plan: Optional[
            SlittingPlan
        ] = None

        counts = Counter()

        def search(
            index: int,
            current_width: int,
        ):

            nonlocal best_plan

            if index == len(all_widths):

                if not self._customer_requirements_met(
                    counts,
                    minimum_required_counts,
                ):

                    return

                plan = self._create_plan(
                    counts
                )

                if self._is_better(
                    plan,
                    best_plan,
                ):

                    best_plan = plan

                return

            width = all_widths[index]

            if width in self.customer_widths:

                max_count = (
                    maximum_customer_counts[
                        width
                    ]
                )

            else:

                max_count = (
                    self.usable_width
                    // width
                )

            for count in range(
                int(max_count) + 1
            ):

                new_width = (
                    current_width
                    + width * count
                )

                if (
                    new_width
                    > self.usable_width
                ):

                    break

                counts[width] = count

                search(
                    index + 1,
                    new_width,
                )

                counts.pop(
                    width,
                    None,
                )

        search(
            index=0,
            current_width=0,
        )

        if best_plan is None:

            raise RuntimeError(
                "No feasible slitting plan found."
            )

        return best_plan

    def _calculate_minimum_customer_counts(
        self,
    ) -> dict[int, int]:

        result = {}

        for order in self.orders:

            weight_per_strip = (
                self.engine.weight_for_width(
                    order.width_mm
                )
            )

            minimum_count = int(
                (
                    order.required_weight_kg
                    / weight_per_strip
                )
                + 0.999999
            )

            result[
                order.width_mm
            ] = minimum_count

        return result

    def _calculate_maximum_customer_counts(
        self,
    ) -> dict[int, int]:

        result = {}

        for order in self.orders:

            result[
                order.width_mm
            ] = (
                self.usable_width
                // order.width_mm
            )

        return result

    def _customer_requirements_met(
        self,
        counts: Counter,
        minimum_required_counts: dict[int, int],
    ) -> bool:

        for width, required_count in (
            minimum_required_counts.items()
        ):

            actual_count = (
                counts[width]
            )

            if (
                actual_count
                < required_count
            ):

                return False

        return True

    def _create_plan(
        self,
        counts: Counter,
    ) -> SlittingPlan:

        customer_counts = Counter()

        stock_counts = Counter()

        for width, count in counts.items():

            if count == 0:

                continue

            if width in self.customer_widths:

                customer_counts[
                    width
                ] = count

            else:

                stock_counts[
                    width
                ] = count

        product_width = sum(
            width * count
            for width, count
            in counts.items()
        )

        unused_width = (
            self.usable_width
            - product_width
        )

        customer_weight = sum(
            self.engine.weight_for_width(
                width
            )
            * count
            for width, count
            in customer_counts.items()
        )

        stock_weight = sum(
            self.engine.weight_for_width(
                width
            )
            * count
            for width, count
            in stock_counts.items()
        )

        required_customer_weight = sum(
            order.required_weight_kg
            for order in self.orders
        )

        overproduction = max(
            0,
            customer_weight
            - required_customer_weight,
        )

        scrap_weight = (
            self.engine.weight_for_width(
                unused_width
            )
        )

        total_produced = (
            customer_weight
            + stock_weight
        )

        total_runs = sum(
           counts.values()
        )
        return SlittingPlan(

            customer_widths=
                customer_counts,

            stock_widths=
                stock_counts,

            product_width_mm=
                product_width,

            kerf_width_mm=
                self.coil.kerf_mm,

            unused_width_mm=
                unused_width,

            customer_weight_kg=
                customer_weight,

            stock_weight_kg=
                stock_weight,

            customer_overproduction_kg=
                overproduction,

            scrap_weight_kg=
                scrap_weight,

            total_produced_weight_kg=
                total_produced,
            
            total_runs=
                total_runs,
        )

    def _is_better(
        self,
        candidate: SlittingPlan,
        current: Optional[
            SlittingPlan
        ],
    ) -> bool:

        if current is None:

            return True

        # PRIMARY OBJECTIVE:
        # Minimize unused width.

        if (
            candidate.unused_width_mm
            != current.unused_width_mm
        ):

            return (
                candidate.unused_width_mm
                < current.unused_width_mm
            )

        # SECONDARY OBJECTIVE:
        # Minimize customer overproduction.

        if (
            candidate.customer_overproduction_kg
            != current.customer_overproduction_kg
        ):

            return (
                candidate.customer_overproduction_kg
                < current.customer_overproduction_kg
            )

        # TERTIARY OBJECTIVE:
        # Maximize stock material.

        return (
            candidate.stock_weight_kg
            > current.stock_weight_kg
        )