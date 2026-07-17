from src.steel_optimizer.models import (
    Coil,
    InputData,
    Order,
    Settings,
)

from src.steel_optimizer.pattern_generator import (
    PatternGenerator,
)

from src.steel_optimizer.optimizer import (
    SlittingOptimizer,
)


def test_optimizer():

    coil = Coil(
        thickness_mm=0.8,
        width_mm=1250,
        weight_kg=3000,
        kerf_mm=6,
    )

    orders = [
        Order(
            width_mm=135,
            required_weight_kg=554,
        ),
        Order(
            width_mm=87,
            required_weight_kg=233,
        ),
    ]

    settings = Settings(
        allow_overproduction=True,
        max_overproduction_percent=100,
        max_knives=12,
        allow_stock_production=True,
    )

    input_data = InputData(
        coil=coil,
        orders=orders,
        stock_widths_mm=[
            50,
            75,
            100,
            125,
            150,
            200,
            250,
            300,
        ],
        settings=settings,
    )

    generator = PatternGenerator(
        coil_width_mm=1250,
        kerf_mm=6,
        max_knives=12,
    )

    patterns = generator.generate(
        [
            135,
            87,
        ]
    )

    optimizer = SlittingOptimizer(
        input_data,
        patterns,
    )

    result = optimizer.optimize()

    assert result.total_runs > 0

    assert (
        result.produced_widths[135] > 0
    )

    assert (
        result.produced_widths[87] > 0
    )