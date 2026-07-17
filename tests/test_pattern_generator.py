from src.steel_optimizer.pattern_generator import (
    PatternGenerator,
    SlitPattern,
)


def test_pattern_is_valid():

    generator = PatternGenerator(
        coil_width_mm=1250,
        kerf_mm=6,
        max_knives=12,
    )

    pattern = (
        135,
        135,
        87,
        87,
    )

    assert generator.is_valid(
        pattern
    )


def test_pattern_is_invalid():

    generator = PatternGenerator(
        coil_width_mm=1250,
        kerf_mm=6,
        max_knives=12,
    )

    pattern = (
        500,
        500,
        500,
    )

    assert not generator.is_valid(
        pattern
    )


def test_scrap_width():

    generator = PatternGenerator(
        coil_width_mm=1250,
        kerf_mm=6,
        max_knives=12,
    )

    pattern = SlitPattern(
        widths_mm=(
            300,
            300,
            300,
            135,
        )
    )

    scrap = generator.scrap_width(
        pattern
    )

    # Product width:
    #
    # 300 + 300 + 300 + 135 = 1035
    #
    # Kerf:
    #
    # 3 × 6 = 18
    #
    # Used = 1053
    #
    # Scrap = 1250 - 1053 = 197

    assert scrap == 197


def test_generate_patterns():

    generator = PatternGenerator(
        coil_width_mm=1250,
        kerf_mm=6,
        max_knives=4,
    )

    patterns = generator.generate(
        [
            135,
            87,
            300,
        ]
    )

    assert len(patterns) > 0

    for pattern in patterns:

        assert generator.is_valid(
            pattern.widths_mm
        )