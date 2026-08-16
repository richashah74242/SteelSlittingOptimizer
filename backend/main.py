from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

print("********** BACKEND LOADED **********")

app = FastAPI(
    title="Steel Slitting Optimizer API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .schemas import OptimizeRequest

from src.steel_optimizer.models import (
    Coil,
    Order,
    Settings,
    InputData,
)

from src.steel_optimizer.optimizer import (
    SlittingOptimizer,
)


@app.get("/")
def root():

    return {
        "message": "Steel Slitting Optimizer API is running"
    }


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


@app.post("/optimize")
def optimize(
    request: OptimizeRequest,
):

    try:

        # =====================================================
        # COIL
        # =====================================================

        coil = Coil(
            thickness_mm=0.8,
            width_mm=request.coil_width_mm,
            weight_kg=request.coil_weight_kg,
            kerf_mm=5,
        )

        # =====================================================
        # CUSTOMER ORDERS
        # =====================================================

        orders = [
            Order(
                width_mm=order.width_mm,
                required_weight_kg=(
                    order.required_weight_kg
                ),
            )
            for order in request.orders
        ]

        # =====================================================
        # SETTINGS
        # =====================================================

        settings = Settings(
            allow_overproduction=True,
            max_overproduction_percent=100.0,
            max_knives=12,
            allow_stock_production=True,
        )

        # =====================================================
        # INPUT DATA
        # =====================================================

        input_data = InputData(
            coil=coil,
            orders=orders,
            stock_widths_mm=(
                request.stock_widths_mm
            ),
            settings=settings,
        )

        # =====================================================
        # OPTIMIZER
        # =====================================================

        optimizer = SlittingOptimizer(
            input_data
        )

        plans = optimizer.optimize(
            top_n=request.top_n
        )

        # =====================================================
        # RESPONSE
        # =====================================================

        return {
            "scenarios": [
                _plan_to_response(
                    plan,
                    request.orders,
                )
                for plan in plans
            ]
        }

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def _plan_to_response(
    plan,
    orders,
):

    # =========================================================
    # REQUIRED WEIGHTS
    # =========================================================
    #
    # Create a lookup:
    #
    # 40  -> 1500 kg
    # 110 -> 250 kg
    # 206 -> 500 kg
    #
    # This is used only for displaying the required weight.
    # =========================================================

    required_weights = {
        order.width_mm: order.required_weight_kg
        for order in orders
    }

    # =========================================================
    # CUSTOMER MATERIAL
    # =========================================================

    customer_material = []

    for width, count in sorted(
        plan.customer_widths.items()
    ):

        if count <= 0:
            continue

        customer_material.append(
            {
                "width_mm": width,

                "strips": count,

                "total_width_used_mm": (
                    width * count
                ),

                "required_weight_kg": round(
                    required_weights.get(
                        width,
                        0.0,
                    ),
                    2,
                ),

                "actual_weight_kg": round(
                    _get_customer_width_weight(
                        plan,
                        width,
                    ),
                    2,
                ),
            }
        )

    # =========================================================
    # STOCK MATERIAL
    # =========================================================

    stock_material = []

    for width, count in sorted(
        plan.stock_widths.items()
    ):

        if count <= 0:
            continue

        stock_material.append(
            {
                "width_mm": width,

                "strips": count,

                "total_width_used_mm": (
                    width * count
                ),
            }
        )

    # =========================================================
    # FINAL RESPONSE
    # =========================================================

    return {

        "customer_material": (
            customer_material
        ),

        "stock_material": (
            stock_material
        ),

        "coil_width_mm": (
            plan.product_width_mm
            + plan.unused_width_mm
        ),

        "total_product_width_used_mm": (
            plan.product_width_mm
        ),

        "running_length_m": round(
            plan.running_length_m,
            2,
        ),

        "raw_material_weight_kg": round(
            plan.total_raw_material_weight_kg,
            2,
        ),

        "scrap_weight_kg": round(
            plan.scrap_weight_kg,
            2,
        ),

        "unused_width_mm": (
            plan.unused_width_mm
        ),

        "customer_weight_kg": round(
            plan.customer_weight_kg,
            2,
        ),

        "stock_weight_kg": round(
            plan.stock_weight_kg,
            2,
        ),

        "customer_overproduction_kg": round(
            plan.customer_overproduction_kg,
            2,
        ),
    }


def _get_customer_width_weight(
    plan,
    width,
):
    """
    Calculate the actual weight for one
    customer width inside the selected plan.

    Uses the same proportional-width logic
    as the optimizer.
    """

    count = plan.customer_widths.get(
        width,
        0,
    )

    if count <= 0:
        return 0.0

    total_width_used = (
        plan.product_width_mm
    )

    if total_width_used <= 0:
        return 0.0

    # Customer + stock produced weight.
    total_produced_weight = (
        plan.total_produced_weight_kg
    )

    strip_width = (
        width * count
    )

    return (
        total_produced_weight
        * strip_width
        / total_width_used
    )