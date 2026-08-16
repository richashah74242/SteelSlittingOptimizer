from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .models import InputData
from .weight_engine import WeightEngine


@dataclass
class SlittingPlan:

    customer_widths: Counter[int]

    stock_widths: Counter[int]

    product_width_mm: int

    kerf_width_mm: int

    unused_width_mm: int

    running_length_m: float

    customer_weight_kg: float

    stock_weight_kg: float

    customer_overproduction_kg: float

    scrap_weight_kg: float

    total_produced_weight_kg: float

    total_raw_material_weight_kg: float

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
    def distinct_stock_sizes(self) -> int:

        return len(
            self.stock_widths
        )


class SlittingOptimizer:

    def __init__(
        self,
        input_data: InputData,
    ):

        self.input_data = input_data

        self.coil = input_data.coil

        self.orders = input_data.orders

        self.stock_widths = sorted(
            set(
                input_data.stock_widths_mm
            )
        )

        self.weight_engine = WeightEngine(
            self.coil
        )

        self.has_fixed_coil_width = (
            self.coil.width_mm > 0
        )

        if self.has_fixed_coil_width:

            self.usable_width = int(
                self.coil.width_mm
                - self.coil.kerf_mm
            )

        else:

            self.usable_width = None

    def optimize(
        self,
        top_n: int = 10,
    ) -> list[SlittingPlan]:

        if not self.orders:

            raise RuntimeError(
                "No customer orders found."
            )

        if self.has_fixed_coil_width:

            plans = (
                self._optimize_fixed_width()
            )

        else:

            plans = (
                self._optimize_without_fixed_width()
            )

        if not plans:

            raise RuntimeError(
                "No feasible plan found."
            )

        plans.sort(
            key=self._score_plan
        )

        return plans[:top_n]

    # =========================================================
    # FIXED COIL WIDTH
    # =========================================================

    def _optimize_fixed_width(
        self,
    ) -> list[SlittingPlan]:

        customer_options = (
            self._generate_customer_options_fixed_width()
        )

        plans = []

        for customer_counts in (
            customer_options
        ):

            customer_width = sum(
                width * count
                for width, count
                in customer_counts.items()
            )

            if (
                customer_width
                > self.usable_width
            ):

                continue

            remaining_width = (
                self.usable_width
                - customer_width
            )

            stock_options = (
                self._generate_stock_options(
                    remaining_width
                )
            )

            for stock_counts in stock_options:

                plans.append(
                    self._create_plan(
                        customer_counts,
                        stock_counts,
                    )
                )

        return plans

    def _generate_customer_options_fixed_width(
        self,
    ) -> list[Counter[int]]:

        results = []

        counts = Counter()

        def search(
            index: int,
        ):

            if (
                index
                == len(self.orders)
            ):

                results.append(
                    Counter(counts)
                )

                return

            order = (
                self.orders[index]
            )

            minimum_count = 1

            maximum_count = (
                self.usable_width
                // order.width_mm
            )

            for count in range(
                minimum_count,
                maximum_count + 1,
            ):

                counts[
                    order.width_mm
                ] = count

                search(
                    index + 1
                )

                del counts[
                    order.width_mm
                ]

        search(0)

        return results

    # =========================================================
    # NO FIXED COIL WIDTH
    # =========================================================

    def _optimize_without_fixed_width(
        self,
    ) -> list[SlittingPlan]:

        customer_options = (
            self._generate_customer_options_without_width()
        )

        plans = []

        for customer_counts in (
            customer_options
        ):

            customer_width = sum(
                width * count
                for width, count
                in customer_counts.items()
            )

            stock_options = (
                self._generate_stock_options_without_width(
                    customer_width
                )
            )

            for stock_counts in stock_options:

                plans.append(
                    self._create_plan(
                        customer_counts,
                        stock_counts,
                    )
                )

        return plans

    def _generate_customer_options_without_width(
        self,
    ) -> list[Counter[int]]:

        results = []

        counts = Counter()

        # We limit the number of strips
        # to a practical range.
        #
        # This is not the coil width.
        # It is only a search boundary.

        MAX_STRIPS_PER_ORDER = 15

        def search(
            index: int,
        ):

            if (
                index
                == len(self.orders)
            ):

                results.append(
                    Counter(counts)
                )

                return

            order = (
                self.orders[index]
            )

            minimum_count = (
                self._minimum_count_without_width(
                    order
                )
            )

            for count in range(
                minimum_count,
                MAX_STRIPS_PER_ORDER + 1,
            ):

                counts[
                    order.width_mm
                ] = count

                search(
                    index + 1
                )

                del counts[
                    order.width_mm
                ]

        search(0)

        return results

    def _minimum_count_without_width(
        self,
        order,
    ) -> int:

        # At least one strip is required.

        return 1

    def _generate_stock_options_without_width(
        self,
        customer_width: int,
    ) -> list[Counter[int]]:

        results = []

        counts = Counter()

        # We only need to explore a reasonable
        # number of stock strips.

        MAX_STOCK_STRIPS = 3

        def search(
            index: int,
            total_stock_width: int,
        ):

            if (
                index
                == len(self.stock_widths)
            ):

                results.append(
                    Counter(counts)
                )

                return

            width = (
                self.stock_widths[index]
            )

            for count in range(
                0,
                MAX_STOCK_STRIPS + 1,
            ):

                counts[
                    width
                ] = count

                search(
                    index + 1,
                    total_stock_width
                    + width * count,
                )

                counts.pop(
                    width,
                    None,
                )

        search(
            0,
            0,
        )

        return results

    # =========================================================
    # COMMON CALCULATIONS
    # =========================================================

    def _minimum_count(
        self,
        width_mm: int,
        required_weight_kg: float,
    ) -> int:

        if (
            self.coil.weight_kg
            and self.coil.weight_kg > 0
            and self.coil.width_mm > 0
        ):

            strip_weight = (
                self.coil.weight_kg
                * width_mm
                / self.coil.width_mm
            )

            required_count = (
                required_weight_kg
                / strip_weight
            )

            return max(
                1,
                int(
                    required_count
                    + 0.999999
                ),
            )

        return 1

    def _generate_stock_options(
        self,
        remaining_width: int,
    ) -> list[Counter[int]]:

        results = []

        counts = Counter()

        stock_widths = (
            self.stock_widths
        )

        def search(
            index: int,
            remaining: int,
        ):

            if (
                index
                == len(stock_widths)
            ):

                results.append(
                    Counter(counts)
                )

                return

            width = (
                stock_widths[index]
            )

            max_count = (
                remaining
                // width
            )

            for count in range(
                max_count + 1
            ):

                if count > 0:

                    counts[
                        width
                    ] = count

                search(
                    index + 1,
                    remaining
                    - width * count,
                )

                counts.pop(
                    width,
                    None,
                )

        search(
            0,
            remaining_width,
        )

        return results

    def _calculate_running_length(
        self,
        customer_counts: Counter[int],
    ) -> float:

        candidate_lengths = []

        for order in self.orders:

            count = (
                customer_counts[
                    order.width_mm
                ]
            )

            if count <= 0:
                continue

            weight_per_meter = (
                self.weight_engine.weight_per_meter(
                    order.width_mm
                )
            )

            if weight_per_meter <= 0:
                continue

            # Length required to produce exactly
            # the customer's requested weight.
            exact_length = (
                order.required_weight_kg
                / (
                    count
                    * weight_per_meter
                )
            )

            candidate_lengths.append(
                exact_length
            )

        if not candidate_lengths:
            return 0.0

        # Test the lengths that would make each
        # customer individually reach its target.
        #
        # The final scoring function decides which
        # one is best.
        best_length = candidate_lengths[0]
        best_score = float("inf")

        for candidate_length in candidate_lengths:

            score = 0.0

            for order in self.orders:

                count = (
                    customer_counts[
                        order.width_mm
                    ]
                )

                if count <= 0:
                    continue

                weight_per_meter = (
                    self.weight_engine.weight_per_meter(
                        order.width_mm
                    )
                )

                produced_weight = (
                    weight_per_meter
                    * count
                    * candidate_length
                )

                difference = abs(
                    produced_weight
                    - order.required_weight_kg
                )

                # Give preference to practical
                # 250 kg steps.
                score += (
                    round(
                        difference / 250
                    )
                    * 250
                )

            if score < best_score:

                best_score = score
                best_length = candidate_length

        return best_length

    def _calculate_customer_weights(
        self,
        customer_counts: Counter[int],
        running_length: float,
    ) -> dict[int, float]:

        customer_weights = {}

        for width, count in customer_counts.items():

            weight_per_meter = (
                self.weight_engine.weight_per_meter(
                    width
                )
            )

            customer_weights[width] = (
                weight_per_meter
                * count
                * running_length
            )

        return customer_weights
    def _customer_weight_deviation(
        self,
        plan: SlittingPlan,
    ) -> float:

        customer_weights = (
            self._calculate_customer_weights(
                plan.customer_widths,
                plan.running_length_m,
            )
        )

        total_deviation = 0.0

        for order in self.orders:

            required_weight = (
                order.required_weight_kg
            )

            produced_weight = (
                customer_weights.get(
                    order.width_mm,
                    0.0,
                )
            )

            difference = abs(
                produced_weight
                - required_weight
            )

            # Treat 250 kg as the first practical
            # tolerance step.
            rounded_difference = (
                round(
                    difference / 250
                )
                * 250
            )

            total_deviation += (
                rounded_difference
            )

        return total_deviation
    
    def _create_plan(
        self,
        customer_counts: Counter[int],
        stock_counts: Counter[int],
    ) -> SlittingPlan:

        # =========================================================
        # 1. CALCULATE WIDTHS
        # =========================================================

        customer_width = sum(
            width * count
            for width, count in customer_counts.items()
        )

        stock_width = sum(
            width * count
            for width, count in stock_counts.items()
        )

        product_width = (
            customer_width
            + stock_width
        )

        # =========================================================
        # 2. COIL WIDTH / SCRAP WIDTH
        # =========================================================

        if self.has_fixed_coil_width:

            raw_coil_width = int(
                self.coil.width_mm
            )

            # Kerf/scrap is part of the coil.
            #
            # Example:
            # Coil width = 1250
            # Kerf/scrap = 10
            # Usable width = 1240
            #
            # IMPORTANT:
            # The frontend/backend currently uses 5 mm kerf.
            # If your actual cutting loss is 10 mm,
            # change kerf_mm in backend/main.py to 10.

            unused_width = (
                raw_coil_width
                - product_width
            )

            if unused_width < 0:
                unused_width = 0

            # Width actually available for produced material.
            #
            # This is the denominator used for calculating
            # individual strip weights.
            total_width_used = (
                raw_coil_width
                - self.coil.kerf_mm
            )

        else:

            raw_coil_width = (
                product_width
                + self.coil.kerf_mm
            )

            unused_width = 0

            total_width_used = (
                product_width
            )

        # =========================================================
        # 3. RUNNING LENGTH
        # =========================================================

        running_length = (
            self._calculate_running_length(
                customer_counts
            )
        )

        # =========================================================
        # 4. RAW COIL WEIGHT
        # =========================================================

        raw_material_weight = (
            self.weight_engine.weight_per_meter(
                raw_coil_width
            )
            * running_length
        )

        # =========================================================
        # 5. SCRAP WEIGHT
        # =========================================================

        scrap_weight = (
            self.weight_engine.weight_per_meter(
                unused_width
            )
            * running_length
        )

        # =========================================================
        # 6. TOTAL PRODUCED WEIGHT
        # =========================================================
        #
        # Scrap is part of the raw coil.
        #
        # Therefore:
        #
        # Total Produced
        # =
        # Raw Coil Weight - Scrap Weight
        #
        # This is the weight available for customer + stock.
        # =========================================================

        total_produced_weight = (
            raw_material_weight
            - scrap_weight
        )

        # =========================================================
        # 7. CUSTOMER WEIGHT
        # =========================================================
        #
        # IMPORTANT:
        #
        # Do NOT calculate:
        #
        # weight_per_meter(width)
        # × strips
        # × running_length
        #
        # because that effectively uses the full 1250 mm
        # coil width as the denominator.
        #
        # Instead:
        #
        # individual_weight =
        # total_produced_weight
        # ×
        # (width × strips)
        # /
        # total_width_used
        #
        # Example:
        #
        # 40 × 3 = 120 mm
        #
        # total_width_used = 1240 mm
        #
        # total produced = 25833.33 kg
        #
        # 25833.33 × 120 / 1240
        # = 2500 kg
        # =========================================================

        customer_weight = 0.0

        if total_width_used > 0:

            for width, count in (
                customer_counts.items()
            ):

                strip_width = (
                    width * count
                )

                strip_weight = (
                    total_produced_weight
                    * strip_width
                    / total_width_used
                )

                customer_weight += (
                    strip_weight
                )

        # =========================================================
        # 8. STOCK WEIGHT
        # =========================================================

        stock_weight = 0.0

        if total_width_used > 0:

            for width, count in (
                stock_counts.items()
            ):

                strip_width = (
                    width * count
                )

                strip_weight = (
                    total_produced_weight
                    * strip_width
                    / total_width_used
                )

                stock_weight += (
                    strip_weight
                )

        # =========================================================
        # 9. CUSTOMER OVERPRODUCTION
        # =========================================================

        required_customer_weight = sum(
            order.required_weight_kg
            for order in self.orders
        )

        overproduction = max(
            0.0,
            customer_weight
            - required_customer_weight,
        )

        # =========================================================
        # 10. FINAL TOTAL
        # =========================================================
        #
        # Customer + Stock should equal the produced portion
        # of the coil.
        # =========================================================

        total_produced = (
            customer_weight
            + stock_weight
        )

        # =========================================================
        # 11. RETURN PLAN
        # =========================================================

        return SlittingPlan(

            customer_widths=Counter(
                customer_counts
            ),

            stock_widths=Counter(
                stock_counts
            ),

            product_width_mm=int(
                product_width
            ),

            kerf_width_mm=int(
                self.coil.kerf_mm
            ),

            unused_width_mm=int(
                unused_width
            ),

            running_length_m=(
                running_length
            ),

            customer_weight_kg=(
                customer_weight
            ),

            stock_weight_kg=(
                stock_weight
            ),

            customer_overproduction_kg=(
                overproduction
            ),

            scrap_weight_kg=(
                scrap_weight
            ),

            total_produced_weight_kg=(
                total_produced
            ),

            total_raw_material_weight_kg=(
                raw_material_weight
            ),

            total_runs=1,
        )
    def _score_plan(
        self,
        plan: SlittingPlan,
    ) -> tuple:

        customer_deviation = (
            self._customer_weight_deviation(
                plan
            )
        )

        return (

            # 1. Keep each customer's production
            # as close as possible to its requirement.
            customer_deviation,

            # 2. Minimize total customer
            # overproduction.
            plan.customer_overproduction_kg,

            # 3. Minimize raw material weight.
            plan.total_raw_material_weight_kg,

            # 4. Minimize unused width.
            plan.unused_width_mm,

            # 5. Prefer fewer stock sizes.
            plan.distinct_stock_sizes,

            # 6. Prefer more stock material.
            -plan.stock_weight_kg,
        )