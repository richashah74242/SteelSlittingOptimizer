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
from .schemas import (
    OptimizeRequest,
)

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

        coil = Coil(
            thickness_mm=request.thickness_mm,
            width_mm=request.coil_width_mm,
            weight_kg=request.coil_weight_kg,
            kerf_mm=request.kerf_mm,
        )

        orders = [
            Order(
                width_mm=order.width_mm,
                required_weight_kg=(
                    order.required_weight_kg
                ),
            )

            for order in request.orders
        ]

        settings = Settings(
            allow_overproduction=True,
            max_overproduction_percent=100.0,
            max_knives=12,
            allow_stock_production=True,
        )

        input_data = InputData(
            coil=coil,
            orders=orders,
            stock_widths_mm=(
                request.stock_widths_mm
            ),
            settings=settings,
        )

        optimizer = SlittingOptimizer(
            input_data
        )

        plans = optimizer.optimize(
            top_n=request.top_n
        )

        return {
            "scenarios": [
                _plan_to_response(
                    plan
                )

                for plan in plans
            ]
        }

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def _plan_to_response(plan):

    return {

        "customer_material": [

            {
                "width_mm": width,
                "strips": count,
            }

            for width, count
            in sorted(
                plan.customer_widths.items()
            )
                if count > 0
        ],

        "stock_material": [

            {
                "width_mm": width,
                "strips": count,
            }

            for width, count
            in sorted(
                plan.stock_widths.items()
            )
                if count > 0
        ],

        "running_length_m": (
            round(
                plan.running_length_m,
                2,
            )
        ),

        "raw_material_weight_kg": (
            round(
                plan.total_raw_material_weight_kg,
                2,
            )
        ),

        "scrap_weight_kg": (
            round(
                plan.scrap_weight_kg,
                2,
            )
        ),

        "unused_width_mm": (
            plan.unused_width_mm
        ),

        "customer_weight_kg": (
            round(
                plan.customer_weight_kg,
                2,
            )
        ),

        "stock_weight_kg": (
            round(
                plan.stock_weight_kg,
                2,
            )
        ),

        "customer_overproduction_kg": (
            round(
                plan.customer_overproduction_kg,
                2,
            )
        ),
    }