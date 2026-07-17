from pathlib import Path

from .excel_handler import (
    read_input_excel,
)

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

    plan = optimizer.optimize()

    print()

    print("=" * 70)

    print(
        "STEEL SLITTING OPTIMIZATION RESULT"
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

    print(
        f"Weight: "
        f"{data.coil.weight_kg:.2f} kg"
    )

    print(
        f"Kerf: "
        f"{data.coil.kerf_mm:.2f} mm"
    )

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
        f"{plan.used_width_mm - plan.kerf_width_mm:.2f} mm"
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
        f"{plan.scrap_width_mm:.2f} mm"
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

    print("=" * 70)


if __name__ == "__main__":

    main()