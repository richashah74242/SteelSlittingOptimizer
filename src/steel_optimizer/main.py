from pathlib import Path

from .optimizer import (
    SlittingOptimizer,
)


def print_counter(
    title: str,
    values,
):

    print()
    print(title)
    print("-" * 60)

    if not values:

        print("None")

        return

    for width, count in sorted(
        values.items()
    ):

        print(
            f"{width} mm"
            f" -> "
            f"{count} strip(s)"
        )


def print_plan(
    plan,
    scenario_number: int,
):

    print()

    print("=" * 70)

    print(
        f"SCENARIO {scenario_number}"
    )

    print("=" * 70)

    print()

    print_counter(
        "CUSTOMER MATERIAL",
        plan.customer_widths,
    )

    print_counter(
        "STOCK MATERIAL",
        plan.stock_widths,
    )

    print()

    print("WIDTH CALCULATION")

    print("-" * 70)

    print(
        f"Customer + stock width: "
        f"{plan.product_width_mm:.2f} mm"
    )

    print(
        f"Cutting wastage: "
        f"{plan.kerf_width_mm:.2f} mm"
    )

    print(
        f"Total used width: "
        f"{plan.used_width_mm:.2f} mm"
    )

    print(
        f"Remaining scrap width: "
        f"{plan.unused_width_mm:.2f} mm"
    )

    print()

    print(
        f"Running length: "
        f"{plan.running_length_m:.2f} m"
    )

    print()

    print("WEIGHT CALCULATION")

    print("-" * 70)

    print(
        f"Customer material: "
        f"{plan.customer_weight_kg:.2f} kg"
    )

    print(
        f"Stock material: "
        f"{plan.stock_weight_kg:.2f} kg"
    )

    print(
        f"Customer overproduction: "
        f"{plan.customer_overproduction_kg:.2f} kg"
    )

    print(
        f"Scrap material: "
        f"{plan.scrap_weight_kg:.2f} kg"
    )

    print(
        f"Total produced material: "
        f"{plan.total_produced_weight_kg:.2f} kg"
    )

    print()

    print(
        f"Total raw material weight: "
        f"{plan.total_raw_material_weight_kg:.2f} kg"
    )


def main():

    input_file = Path(
        "templates/input.xlsx"
    )

    data = read_input_excel(
        input_file
    )

    optimizer = SlittingOptimizer(
        data
    )

    plans = optimizer.optimize(
        top_n=10
    )

    print()

    print("=" * 70)

    print(
        "STEEL SLITTING OPTIMIZATION RESULTS"
    )

    print("=" * 70)

    print()

    print("RAW COIL")

    print("-" * 70)

    print(
        f"Thickness: "
        f"{data.coil.thickness_mm} mm"
    )

    print(
        f"Width: "
        f"{data.coil.width_mm} mm"
    )

    if data.coil.weight_kg is None:

        print(
            "Weight: Calculated from "
            "required customer material"
        )

    else:

        print(
            f"Weight: "
            f"{data.coil.weight_kg:.2f} kg"
        )

    print(
        f"Kerf: "
        f"{data.coil.kerf_mm:.2f} mm"
    )

    for index, plan in enumerate(
        plans,
        start=1,
    ):

        print_plan(
            plan,
            index,
        )

    print()

    print("=" * 70)


if __name__ == "__main__":

    main()