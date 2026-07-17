from src.steel_optimizer.models import (
    Coil,
    Order,
)

from src.steel_optimizer.weight_engine import (
    WeightEngine,
)


def test_weight_for_width():

    coil = Coil(
        thickness_mm=0.8,
        width_mm=1250,
        weight_kg=3000,
        kerf_mm=6,
    )

    engine = WeightEngine(coil)

    weight = engine.weight_for_width(
        250
    )

    assert weight == 600


def test_strips_required():

    coil = Coil(
        thickness_mm=0.8,
        width_mm=1250,
        weight_kg=3000,
        kerf_mm=6,
    )

    order = Order(
        width_mm=135,
        required_weight_kg=554,
    )

    engine = WeightEngine(coil)

    strips = engine.strips_required(
        order
    )

    # One strip = 324 kg
    # 554 / 324 = 1.71
    # Therefore 2 strips are required.

    assert strips == 2


def test_overproduction():

    coil = Coil(
        thickness_mm=0.8,
        width_mm=1250,
        weight_kg=3000,
        kerf_mm=6,
    )

    order = Order(
        width_mm=135,
        required_weight_kg=554,
    )

    engine = WeightEngine(coil)

    overproduction = (
        engine.overproduction_weight(
            order,
            2,
        )
    )

    assert round(
        overproduction,
        2,
    ) == 94