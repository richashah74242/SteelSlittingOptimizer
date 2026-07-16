from pathlib import Path

from src.steel_optimizer.excel_handler import (
    read_input_excel,
)


def test_read_input_excel():

    input_file = Path(
        "templates/input.xlsx"
    )

    data = read_input_excel(input_file)

    assert data.coil.width_mm == 1250

    assert data.coil.weight_kg == 3000

    assert len(data.orders) == 2

    assert data.orders[0].width_mm == 135

    assert data.orders[1].width_mm == 87

    assert data.settings.max_knives == 12