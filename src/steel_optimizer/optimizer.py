from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Optional

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
        return (
            self.unused_width_mm
            + self.kerf_width_mm
        )

    @property
    def distinct_stock_sizes(self) -> int:
        return len(
            [
                width
                for width, count
                in self.stock_widths.items()
                if count > 0
            ]
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

        # A fixed coil width is always available in your
        # application. This check is kept for safety.
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

    # =========================================================
    # MAIN OPTIMIZATION
    # =========================================================

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

        plans: list[SlittingPlan] = []

        for customer_counts in customer_options:

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

                stock_width = sum(
                    width * count
                    for width, count
                    in stock_counts.items()
                )

                product_width = (
                    customer_width
                    + stock_width
                )

                if (
                    product_width
                    > self.usable_width
                ):
                    continue

                plan = self._create_plan(
                    customer_counts,
                    stock_counts,
                )

                # A plan must actually produce something.
                if plan.running_length_m <= 0:
                    continue

                plans.append(plan)

        return plans

    # =========================================================
    # CUSTOMER OPTIONS - FIXED WIDTH
    # =========================================================

    def _generate_customer_options_fixed_width(
        self,
    ) -> list[Counter[int]]:

        results: list[Counter[int]] = []

        counts = Counter()

        def search(index: int):

            if index == len(self.orders):

                results.append(
                    Counter(counts)
                )

                return

            order = self.orders[index]

            # IMPORTANT:
            #
            # Do NOT calculate the minimum strip count
            # from the customer's required weight.
            #
            # Running length is common to all customer strips.
            #
            # Therefore even one strip can satisfy a large
            # weight requirement by increasing running length.
            #
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
    # NO FIXED COIL WEIGHT
    # =========================================================

    def _optimize_without_fixed_width(
        self,
    ) -> list[SlittingPlan]:

        customer_options = (
            self._generate_customer_options_fixed_width()
        )

        plans: list[SlittingPlan] = []

        for customer_counts in customer_options:

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

                plan = self._create_plan(
                    customer_counts,
                    stock_counts,
                )

                if plan.running_length_m <= 0:
                    continue

                plans.append(plan)

        return plans

    # =========================================================
    # STOCK OPTIONS
    # =========================================================

    def _generate_stock_options(
        self,
        remaining_width: int,
    ) -> list[Counter[int]]:

        results: list[Counter[int]] = []

        counts = Counter()

        stock_widths = self.stock_widths

        def search(
            index: int,
            remaining: int,
        ):

            if index == len(stock_widths):

                results.append(
                    Counter(counts)
                )

                return

            width = stock_widths[index]

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

    # =========================================================
    # RUNNING LENGTH
    # =========================================================

    def _calculate_running_length(
        self,
        customer_counts: Counter[int],
    ) -> float:

        # =====================================================
        # CASE 1:
        # FIXED COIL WEIGHT
        # =====================================================
        #
        # Example 3:
        #
        # Coil width  = 1250 mm
        # Coil weight = 3000 kg
        #
        # Running length is determined by the physical coil.
        #

        if (
            self.coil.weight_kg is not None
            and self.coil.weight_kg > 0
        ):

            raw_weight_per_meter = (
                self.weight_engine.weight_per_meter(
                    self.coil.width_mm
                )
            )

            if raw_weight_per_meter <= 0:

                return 0.0

            return (
                self.coil.weight_kg
                / raw_weight_per_meter
            )

        # =====================================================
        # CASE 2:
        # NO FIXED COIL WEIGHT
        # =====================================================
        #
        # Examples 1 and 2.
        #
        # Running length is flexible.
        #
        # We calculate the length needed to produce the total
        # customer demand from the selected customer widths.
        #
        # This allows the optimizer to compare different
        # combinations instead of forcing every individual
        # width to be satisfied independently.
        #

        total_required_weight = sum(
            order.required_weight_kg
            for order in self.orders
        )

        total_customer_width = sum(
            width * count
            for width, count
            in customer_counts.items()
        )

        if (
            total_required_weight <= 0
            or total_customer_width <= 0
        ):

            return 0.0

        customer_weight_per_meter = (
            self.weight_engine.weight_per_meter(
                total_customer_width
            )
        )

        if customer_weight_per_meter <= 0:

            return 0.0

        return (
            total_required_weight
            / customer_weight_per_meter
        )

    # =========================================================
    # CUSTOMER WEIGHTS
    # =========================================================

    def _calculate_customer_weights(
        self,
        customer_counts: Counter[int],
        running_length: float,
    ) -> dict[int, float]:

        customer_weights: dict[int, float] = {}

        for width, count in (
            customer_counts.items()
        ):

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

    # =========================================================
    # CREATE PLAN
    # =========================================================

    def _create_plan(
        self,
        customer_counts: Counter[int],
        stock_counts: Counter[int],
    ) -> SlittingPlan:

        # =====================================================
        # WIDTH CALCULATION
        # =====================================================

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

        # =====================================================
        # COIL / KERF / SCRAP WIDTH
        # =====================================================

        raw_coil_width = int(
            self.coil.width_mm
        )

        kerf_width = int(
            self.coil.kerf_mm
        )

        # Physical relationship:
        #
        # COIL WIDTH
        #     =
        # PRODUCT WIDTH
        #     + KERF
        #     + UNUSED WIDTH
        #
        # Example:
        #
        # 1250 = 1244 + 5 + 1
        #
        unused_width = (
            raw_coil_width
            - product_width
            - kerf_width
        )

        if unused_width < 0:
            unused_width = 0

        # =====================================================
        # RUNNING LENGTH
        # =====================================================

        running_length = (
            self._calculate_running_length(
                customer_counts
            )
        )

        if running_length <= 0:

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
                kerf_width_mm=kerf_width,
                unused_width_mm=int(
                    unused_width
                ),
                running_length_m=0.0,
                customer_weight_kg=0.0,
                stock_weight_kg=0.0,
                customer_overproduction_kg=0.0,
                scrap_weight_kg=0.0,
                total_produced_weight_kg=0.0,
                total_raw_material_weight_kg=0.0,
                total_runs=1,
            )

        # =====================================================
        # RAW COIL WEIGHT
        # =====================================================

        raw_material_weight = (
            self.weight_engine.weight_per_meter(
                raw_coil_width
            )
            * running_length
        )

        # =====================================================
        # SCRAP
        # =====================================================
        #
        # IMPORTANT:
        #
        # Scrap consists of:
        #
        #     UNUSED WIDTH + KERF
        #
        # So kerf is included in both:
        #
        #     scrap_width
        #     scrap_weight
        #

        scrap_width = (
            unused_width
            + kerf_width
        )

        scrap_weight = (
            self.weight_engine.weight_per_meter(
                scrap_width
            )
            * running_length
        )

        # =====================================================
        # PRODUCED MATERIAL
        # =====================================================

        total_produced_weight = (
            raw_material_weight
            
        )

        # =====================================================
        # CUSTOMER WEIGHT
        # =====================================================

        customer_weight = 0.0

        if product_width > 0:

            for width, count in (
                customer_counts.items()
            ):

                strip_width = (
                    width * count
                )

                strip_weight = (
                    total_produced_weight
                    * strip_width
                    / product_width
                )

                customer_weight += (
                    strip_weight
                )

        # =====================================================
        # STOCK WEIGHT
        # =====================================================

        stock_weight = 0.0

        if product_width > 0:

            for width, count in (
                stock_counts.items()
            ):

                strip_width = (
                    width * count
                )

                strip_weight = (
                    total_produced_weight
                    * strip_width
                    / product_width
                )

                stock_weight += (
                    strip_weight
                )

        # =====================================================
        # CUSTOMER OVERPRODUCTION
        # =====================================================

        required_customer_weight = sum(
            order.required_weight_kg
            for order in self.orders
        )

        customer_overproduction = max(
            0.0,
            customer_weight
            - required_customer_weight,
        )

        # =====================================================
        # TOTAL PRODUCED
        # =====================================================
        #
        # This is ONLY customer + stock.
        #
        # Scrap is kept separately.
        #
        # Therefore:
        #
        # Customer + Stock + Scrap
        #     =
        # Raw coil weight
        #

        total_produced = (
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

            product_width_mm=int(
                product_width
            ),

            kerf_width_mm=kerf_width,

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
                customer_overproduction
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
    # =========================================================
    # SCORING / RANKING
    # =========================================================

    def _score_plan(
        self,
        plan: SlittingPlan,
    ) -> tuple:

        customer_weights = (
            self._calculate_customer_weights(
                plan.customer_widths,
                plan.running_length_m,
            )
        )

        total_shortfall = 0.0
        total_overproduction = 0.0
        total_absolute_deviation = 0.0
        max_customer_deviation = 0.0

        for order in self.orders:

            produced = customer_weights.get(
                order.width_mm,
                0.0,
            )

            required = (
                order.required_weight_kg
            )

            shortfall = max(
                0.0,
                required - produced,
            )

            overproduction = max(
                0.0,
                produced - required,
            )

            deviation = abs(
                produced - required
            )

            total_shortfall += (
                shortfall
            )

            total_overproduction += (
                overproduction
            )

            total_absolute_deviation += (
                deviation
            )

            max_customer_deviation = max(
                max_customer_deviation,
                deviation,
            )

        # =====================================================
        # FIXED COIL WEIGHT
        # =====================================================
        #
        # When coil weight is fixed, running length is fixed.
        #
        # Therefore it may be mathematically impossible to
        # satisfy every customer order exactly.
        #
        # Example 3:
        #
        # 40 x 16  -> ~1536 kg
        # 110 x 1  -> ~264 kg
        # 144 x 2  -> ~691 kg
        # 206 x 1  -> ~494 kg
        #
        # The 206 mm order is slightly below 500 kg.
        #
        # That is acceptable because adding another 206 mm
        # strip creates a much larger deviation.
        #

        if (
            self.coil.weight_kg is not None
            and self.coil.weight_kg > 0
        ):

            return (

                # 1. Minimize total customer deviation
                total_absolute_deviation,

                # 2. Minimize worst individual deviation
                max_customer_deviation,

                # 3. Minimize customer overproduction
                total_overproduction,

                # 4. Minimize customer shortfall
                total_shortfall,

                # 5. Minimize scrap
                plan.scrap_weight_kg,

                # 6. Minimize unused physical width
                plan.unused_width_mm,

                # 7. Prefer less raw material
                plan.total_raw_material_weight_kg,

                # 8. Prefer fewer stock sizes
                plan.distinct_stock_sizes,

                # 9. Prefer more stock material
                -plan.stock_weight_kg,
            )

        # =====================================================
        # FLEXIBLE COIL WEIGHT
        # =====================================================

        return (

            # 1. Minimize total customer deviation
            total_absolute_deviation,

            # 2. Minimize worst individual deviation
            max_customer_deviation,

            # 3. Minimize customer overproduction
            total_overproduction,

            # 4. Minimize shortfall
            total_shortfall,

            # 5. Minimize scrap
            plan.scrap_weight_kg,

            # 6. Minimize unused width
            plan.unused_width_mm,

            # 7. Minimize raw material
            plan.total_raw_material_weight_kg,

            # 8. Fewer stock sizes
            plan.distinct_stock_sizes,

            # 9. More stock material
            -plan.stock_weight_kg,
        )