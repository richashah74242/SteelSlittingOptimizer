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

            minimum_count = (
                self._minimum_count(
                    order.width_mm,
                    order.required_weight_kg,
                )
            )

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

        required_length = 0.0

        for order in (
            self.orders
        ):

            count = (
                customer_counts[
                    order.width_mm
                ]
            )

            weight_per_meter = (
                self.weight_engine
                .weight_per_meter(
                    order.width_mm
                )
            )

            length_required = (
                order.required_weight_kg
                / (
                    count
                    * weight_per_meter
                )
            )

            required_length = max(
                required_length,
                length_required,
            )

        return required_length

    def _create_plan(
        self,
        customer_counts: Counter[int],
        stock_counts: Counter[int],
    ) -> SlittingPlan:

        customer_width = sum(
            width * count
            for width, count
            in customer_counts.items()
        )

        stock_width = sum(
            width * count
            for width, count
            in stock_counts.items()
        )

        product_width = (
            customer_width
            + stock_width
        )

        # -----------------------------------------------------
        # CASE 1: FIXED COIL WIDTH
        # -----------------------------------------------------

        if self.has_fixed_coil_width:

            raw_coil_width = (
                self.coil.width_mm
            )

            unused_width = (
                self.usable_width
                - product_width
            )

        # -----------------------------------------------------
        # CASE 2: NO FIXED COIL WIDTH
        # -----------------------------------------------------

        else:

            # The raw coil must contain:
            #
            # customer widths
            # + stock widths
            # + kerf
            #
            raw_coil_width = (
                product_width
                + self.coil.kerf_mm
            )

            unused_width = 0

        running_length = (
            self._calculate_running_length(
                customer_counts
            )
        )

        customer_weight = 0.0

        for width, count in (
            customer_counts.items()
        ):

            customer_weight += (
                self.weight_engine
                .weight_per_meter(
                    width
                )
                * count
                * running_length
            )

        stock_weight = 0.0

        for width, count in (
            stock_counts.items()
        ):

            stock_weight += (
                self.weight_engine
                .weight_per_meter(
                    width
                )
                * count
                * running_length
            )

        required_customer_weight = sum(
            order.required_weight_kg
            for order in self.orders
        )

        overproduction = max(
            0.0,
            customer_weight
            - required_customer_weight,
        )

        total_produced = (
            customer_weight
            + stock_weight
        )

        raw_material_weight = (
            self.weight_engine
            .weight_per_meter(
                raw_coil_width
            )
            * running_length
        )

        scrap_weight = (
            self.weight_engine
            .weight_per_meter(
                unused_width
            )
            * running_length
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

        return (

            # 1. Minimize customer overproduction
            plan.customer_overproduction_kg,

            # 2. Minimize raw material weight
            plan.total_raw_material_weight_kg,

            # 3. Minimize unused width
            plan.unused_width_mm,

            # 4. Prefer fewer stock sizes
            plan.distinct_stock_sizes,

            # 5. Prefer more stock material
            -plan.stock_weight_kg,
        )