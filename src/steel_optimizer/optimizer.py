from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import product
from typing import Iterable

from .models import (
    Coil,
    InputData,
    Order,
    Settings,
)
from .pattern_generator import SlitPattern


@dataclass
class SlittingPlan:

    customer_widths: Counter[int]
    stock_widths: Counter[int]

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
    def used_width_mm(self) -> int:
        return (
            self.product_width_mm
            + self.kerf_width_mm
        )

    @property
    def scrap_width_mm(self) -> int:
        return self.unused_width_mm

    @property
    def produced_widths(self) -> Counter[int]:

        result = Counter()

        result.update(
            self.customer_widths
        )

        result.update(
            self.stock_widths
        )

        return result


class SlittingOptimizer:

    def __init__(
        self,
        input_data: InputData,
        patterns: Iterable[SlitPattern] | None = None,
    ):

        self.input_data = input_data
        self.coil = input_data.coil
        self.orders = input_data.orders
        self.stock_widths = input_data.stock_widths_mm
        self.settings = input_data.settings

        self.patterns = (
            list(patterns)
            if patterns is not None
            else []
        )

        self.customer_widths = [
            order.width_mm
            for order in self.orders
        ]

        self.width_to_weight = (
            self.coil.weight_kg
            / self.coil.width_mm
        )

    def optimize(self) -> SlittingPlan:

        customer_count_options = (
            self._customer_count_options()
        )

        best_plan = None
        best_score = None

        for customer_counts in product(
            *customer_count_options
        ):

            customer_counts = dict(
                zip(
                    self.customer_widths,
                    customer_counts,
                )
            )

            if not self._meets_customer_demand(
                customer_counts
            ):
                continue

            customer_width = sum(
                width * count
                for width, count
                in customer_counts.items()
            )
            customer_produced_width = sum(
                order.width_mm * count
                for order, count in zip(
                    self.orders,
                    customer_counts,
                )
            )
            remaining_width = (
                self.coil.width_mm
                - self.coil.kerf_mm
                - customer_width
            )

            if remaining_width < 0:
                continue

            stock_counts = (
                self._best_stock_combination(
                    remaining_width
                )
            )

            if stock_counts is None:
                continue
            
            stock_produced_width = sum(
                width * count
                for width, count in stock_counts.items()
            )
            product_width = (
                customer_width
                + sum(
                    width * count
                    for width, count
                    in stock_counts.items()
                )
            )

            unused_width = (
                self.coil.width_mm
                - self.coil.kerf_mm
                - product_width
            )

            customer_overproduction = (
                self._customer_overproduction(
                    customer_counts
                )
            )

            distinct_stock_sizes = sum(
                1
                for count in stock_counts.values()
                if count > 0
            )

            stock_width = sum(
                width * count
                for width, count in stock_counts.items()
            )

            score = (
                unused_width,
                distinct_stock_sizes,
                -customer_produced_width,
                stock_produced_width,
            )

            if (
                best_score is None
                or score < best_score
            ):

                best_score = score

                best_plan = (
                    self._build_plan(
                        customer_counts,
                        stock_counts,
                        unused_width,
                    )
                )

        if best_plan is None:

            raise RuntimeError(
                "No feasible slitting plan found."
            )

        return best_plan

    def _customer_count_options(
        self,
    ) -> list[list[int]]:

        options = []

        for order in self.orders:

            minimum_count = (
                self._minimum_strips_required(
                    order
                )
            )

            maximum_count = (
                self._maximum_strips_possible(
                    order.width_mm
                )
            )

            options.append(
                list(
                    range(
                        minimum_count,
                        maximum_count + 1,
                    )
                )
            )

        return options


    def _minimum_strips_required(
        self,
        order: Order,
    ) -> int:

        weight_per_strip = (
            order.width_mm
            * self.width_to_weight
        )

        return int(
            max(
                1,
                (
                    order.required_weight_kg
                    / weight_per_strip
                )
                + 0.999999,
            )
        )
    
    def _maximum_strips_possible(
        self,
        width_mm: int,
    ) -> int:

        available_width = int(
            self.coil.width_mm
            - self.coil.kerf_mm
        )

        return int(
            available_width
            // width_mm
        )
    def _meets_customer_demand(
        self,
        customer_counts: dict[int, int],
    ) -> bool:

        for order in self.orders:

            produced_weight = (
                customer_counts[
                    order.width_mm
                ]
                * order.width_mm
                * self.width_to_weight
            )

            if (
                produced_weight
                < order.required_weight_kg
            ):

                return False

        return True

    def _customer_overproduction(
        self,
        customer_counts: dict[int, int],
    ) -> float:

        total_overproduction = 0.0

        for order in self.orders:

            produced_weight = (
                customer_counts[
                    order.width_mm
                ]
                * order.width_mm
                * self.width_to_weight
            )

            total_overproduction += max(
                0.0,
                produced_weight
                - order.required_weight_kg,
            )

        return total_overproduction

    def _best_stock_combination(
        self,
        available_width: int,
    ) -> Counter[int] | None:

        if (
            not self.settings.allow_stock_production
            or not self.stock_widths
        ):

            return Counter()

        stock_widths = sorted(
            set(
                self.stock_widths
            )
        )
        
        available_width = int(
            available_width
        )
        best_counts = None
        best_score = None

        counts = [0] * len(
            stock_widths
        )

        def search(
            index: int,
            remaining: int,
        ):
            remaining = int(
                remaining
            )

            nonlocal best_counts
            nonlocal best_score

            if index == len(
                stock_widths
            ):

                used = (
                    available_width
                    - remaining
                )

                distinct_sizes = sum(
                    1
                    for count in counts
                    if count > 0
                )

                score = (
                    # Maximize stock width
                    -used,

                    # Then fewer stock sizes
                    distinct_sizes,
                )

                if (
                    best_score is None
                    or score < best_score
                ):

                    best_score = score

                    best_counts = Counter(
                        {
                            width: count
                            for width, count in zip(
                                stock_widths,
                                counts,
                            )
                            if count > 0
                        }
                    )

                return

            width = stock_widths[index]

            max_count = int(
                remaining
                // width
            )

            for count in range(
                max_count + 1
            ):

                counts[index] = count

                search(
                    index + 1,
                    remaining
                    - (
                        count
                        * width
                    ),
                )

            counts[index] = 0

        search(
            0,
            available_width,
        )

        return best_counts

    def _build_plan(
        self,
        customer_counts: dict[int, int],
        stock_counts: Counter[int],
        unused_width: int,
    ) -> SlittingPlan:

        customer_width = sum(
            width * count
            for width, count in customer_counts.items()
        )

        stock_width = sum(
            width * count
            for width, count in stock_counts.items()
        )

        customer_weight = (
            customer_width
            * self.width_to_weight
        )

        stock_weight = (
            stock_width
            * self.width_to_weight
        )

        required_weight = sum(
            order.required_weight_kg
            for order in self.orders
        )

        customer_overproduction = max(
            0.0,
            customer_weight
            - required_weight,
        )

        total_produced_weight = (
            customer_weight
            + stock_weight
        )

        return SlittingPlan(

            customer_widths=Counter(
                customer_counts
            ),

            stock_widths=Counter(
                stock_counts
            ),

            product_width_mm=(
                customer_width
                + stock_width
            ),

            kerf_width_mm=(
                self.coil.kerf_mm
            ),

            unused_width_mm=(
                unused_width
            ),

            customer_weight_kg=(
                customer_weight
            ),

            stock_weight_kg=(
                stock_weight
            ),

            customer_overproduction_kg=(
                customer_overproduction
            ),

            scrap_weight_kg=(
                unused_width
                * self.width_to_weight
            ),

            total_produced_weight_kg=(
                total_produced_weight
            ),

            total_runs=1,
        )