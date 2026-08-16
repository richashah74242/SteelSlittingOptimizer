import { useState } from "react";

function App() {
  const [coilWidth, setCoilWidth] = useState("");
  const [coilWeight, setCoilWeight] = useState("");

  const [orders, setOrders] = useState([
    {
      width_mm: "",
      required_weight_kg: "",
    },
  ]);

  const [stockWidths, setStockWidths] = useState(
    "40,110,112,144,206,232"
  );

  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function addOrder() {
    setOrders([
      ...orders,
      {
        width_mm: "",
        required_weight_kg: "",
      },
    ]);
  }

  function removeOrder(index) {
    setOrders(
      orders.filter((_, i) => i !== index)
    );
  }

  function updateOrder(index, field, value) {
    const updatedOrders = orders.map(
      (order, i) =>
        i === index
          ? {
              ...order,
              [field]: value,
            }
          : order
    );

    setOrders(updatedOrders);
  }

  /*
   * ============================================================
   * CALCULATE DISPLAY MATERIAL
   * ============================================================
   *
   * Customer + stock strips having the same width are combined.
   *
   * Example:
   *
   * 40 × 3   = 120 mm
   * 110 × 2  = 220 mm
   * 112 × 1  = 112 mm
   * 144 × 1  = 144 mm
   * 206 × 2  = 412 mm
   * 232 × 1  = 232 mm
   *
   * Total produced width = 1240 mm
   *
   * Coil width = 1250 mm
   *
   * Scrap = 1250 - 1240 = 10 mm
   *
   * IMPORTANT:
   *
   * Material weights are calculated using:
   *
   *     material width / total produced width
   *
   * So:
   *
   * 40 mm × 3 = 120 mm
   *
   * 25833.33 × 120 / 1240
   *
   * = 2500 kg
   *
   * Scrap is calculated separately from the scrap width.
   */
  function getProducedMaterial(scenario) {
    const materialMap = new Map();

    function addMaterial(items) {
      (items || [])
        .filter(
          (item) =>
            Number(item.strips || 0) > 0
        )
        .forEach((item) => {
          const width = Number(
            item.width_mm || 0
          );

          const strips = Number(
            item.strips || 0
          );

          if (width <= 0 || strips <= 0) {
            return;
          }

          const existing =
            materialMap.get(width) || {
              width_mm: width,
              strips: 0,
            };

          existing.strips += strips;

          materialMap.set(
            width,
            existing
          );
        });
    }

    addMaterial(
      scenario.customer_material
    );

    addMaterial(
      scenario.stock_material
    );

    /*
     * Sort by width.
     */
    const materials = Array.from(
      materialMap.values()
    ).sort(
      (a, b) =>
        a.width_mm - b.width_mm
    );

    /*
     * ============================================================
     * TOTAL PRODUCED WIDTH
     * ============================================================
     */
    const totalWidthUsed =
      materials.reduce(
        (total, item) =>
          total +
          item.width_mm *
            item.strips,
        0
      );

    /*
     * ============================================================
     * TOTAL PRODUCED MATERIAL WEIGHT
     * ============================================================
     *
     * This is customer + stock material.
     *
     * Example:
     *
     * customer = 7296 kg
     * stock    = 18537.33 kg
     *
     * total = 25833.33 kg
     */
    const totalProducedWeight =
      Number(
        scenario.customer_weight_kg || 0
      ) +
      Number(
        scenario.stock_weight_kg || 0
      );

    /*
     * ============================================================
     * INDIVIDUAL MATERIAL WEIGHT
     * ============================================================
     *
     * Weight is proportional to width.
     *
     * Example:
     *
     * 40 × 3 = 120 mm
     *
     * weight =
     *
     * 25833.33 × 120 / 1240
     *
     * = 2500 kg
     */
    const materialsWithWeight =
      materials.map((item) => {
        const materialWidth =
          item.width_mm *
          item.strips;

        const weight =
          totalWidthUsed > 0
            ? (
                totalProducedWeight *
                materialWidth /
                totalWidthUsed
              )
            : 0;

        return {
          ...item,

          total_width_used:
            materialWidth,

          weight,
        };
      });

    /*
     * ============================================================
     * COIL WIDTH
     * ============================================================
     */
    const actualCoilWidth =
      Number(
        scenario.coil_width_mm ||
          coilWidth ||
          0
      );

    /*
     * ============================================================
     * SCRAP WIDTH
     * ============================================================
     *
     * Scrap is the remaining part of the coil.
     *
     * 1250 - 1240 = 10 mm
     *
     * DO NOT add kerf again here.
     *
     * The table must satisfy:
     *
     * material width + scrap width = coil width
     *
     * 1240 + 10 = 1250
     */
    const scrapWidth =
      actualCoilWidth > 0
        ? Math.max(
            0,
            actualCoilWidth -
              totalWidthUsed
          )
        : 0;

    /*
     * ============================================================
     * SCRAP WEIGHT
     * ============================================================
     *
     * Scrap weight is calculated using the same
     * running-length basis as the produced material.
     *
     * Since:
     *
     * produced weight / produced width
     *
     * gives weight per mm of width,
     *
     * scrap weight =
     *
     * total produced weight
     * × scrap width
     * / total produced width
     *
     * Example:
     *
     * 25833.33 × 10 / 1240
     *
     * = 208.33 kg
     */
    const scrapWeight =
      totalWidthUsed > 0
        ? (
            totalProducedWeight *
            scrapWidth /
            totalWidthUsed
          )
        : 0;

    /*
     * ============================================================
     * TOTAL COIL WEIGHT
     * ============================================================
     *
     * Material + scrap.
     */
    const totalCoilWeight =
      totalProducedWeight +
      scrapWeight;

    return {
      materials:
        materialsWithWeight,

      totalWidthUsed,

      totalProducedWeight,

      scrapWidth,

      scrapWeight,

      totalCoilWeight,

      coilWidth: actualCoilWidth,
    };
  }

  async function optimize() {
    setLoading(true);
    setError("");
    setScenarios([]);

    try {
      const payload = {
        coil_width_mm:
          Number(coilWidth),

        coil_weight_kg:
          coilWeight
            ? Number(coilWeight)
            : null,

        orders: orders.map(
          (order) => ({
            width_mm:
              Number(
                order.width_mm
              ),

            required_weight_kg:
              Number(
                order.required_weight_kg
              ),
          })
        ),

        stock_widths_mm:
          stockWidths
            .split(",")
            .map((width) =>
              Number(width.trim())
            )
            .filter(
              (width) => width > 0
            ),

        top_n: 6,
      };

      const API_URL =
        import.meta.env.VITE_API_URL ||
        "http://127.0.0.1:8000";

      const response = await fetch(
        `${API_URL}/optimize`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify(
            payload
          ),
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Optimization failed"
        );
      }

      setScenarios(
        data.scenarios || []
      );
    } catch (error) {
      setError(error.message);
    }

    setLoading(false);
  }

  return (
    <div className="app">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="header">
        <h1>
          Steel Slitting Optimizer
        </h1>

        <p>
          Find the best slitting scenarios
          with minimum material wastage.
        </p>
      </header>


      <main className="container">

        {/* =====================================================
            COIL DETAILS
        ===================================================== */}

        <section className="card">

          <h2>
            Coil Details
          </h2>

          <div className="input-grid">

            <div className="input-group">

              <label>
                Coil Width (mm)
              </label>

              <input
                type="number"
                min="1"
                value={coilWidth}
                onChange={(event) =>
                  setCoilWidth(
                    event.target.value
                  )
                }
                placeholder="e.g. 1250"
              />

            </div>


            <div className="input-group">

              <label>
                Coil Weight (kg)

                <span className="optional">
                  Optional
                </span>
              </label>

              <input
                type="number"
                min="0"
                step="0.01"
                value={coilWeight}
                onChange={(event) =>
                  setCoilWeight(
                    event.target.value
                  )
                }
                placeholder="Optional"
              />

            </div>

          </div>

        </section>


        {/* =====================================================
            CUSTOMER ORDERS
        ===================================================== */}

        <section className="card">

          <div className="section-header">

            <h2>
              Customer Orders
            </h2>

            <button
              className="secondary-button"
              onClick={addOrder}
            >
              + Add Order
            </button>

          </div>


          <div className="orders-header">

            <span>
              Width (mm)
            </span>

            <span>
              Required Weight (kg)
            </span>

            <span></span>

          </div>


          {orders.map(
            (order, index) => (

              <div
                className="order-row"
                key={index}
              >

                <input
                  type="number"
                  min="1"
                  value={
                    order.width_mm
                  }
                  onChange={(event) =>
                    updateOrder(
                      index,
                      "width_mm",
                      event.target.value
                    )
                  }
                  placeholder="e.g. 40"
                />


                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={
                    order.required_weight_kg
                  }
                  onChange={(event) =>
                    updateOrder(
                      index,
                      "required_weight_kg",
                      event.target.value
                    )
                  }
                  placeholder="e.g. 2000"
                />


                {orders.length > 1 && (

                  <button
                    className="remove-button"
                    onClick={() =>
                      removeOrder(index)
                    }
                  >
                    Remove
                  </button>

                )}

              </div>

            )
          )}

        </section>


        {/* =====================================================
            STOCK WIDTHS
        ===================================================== */}

        <section className="card">

          <h2>
            Stock Widths
          </h2>

          <div className="input-group">

            <label>
              Available Stock Widths (mm)
            </label>

            <input
              type="text"
              className="full-input"
              value={stockWidths}
              onChange={(event) =>
                setStockWidths(
                  event.target.value
                )
              }
              placeholder="e.g. 40, 110, 144, 206, 232"
            />

            <small>
              Enter widths separated by commas.
            </small>

          </div>

        </section>


        {/* =====================================================
            OPTIMIZE
        ===================================================== */}

        <button
          className="optimize-button"
          onClick={optimize}
          disabled={loading}
        >
          {loading
            ? "Optimizing..."
            : "Optimize"}
        </button>


        {/* =====================================================
            ERROR
        ===================================================== */}

        {error && (
          <div className="error">
            {error}
          </div>
        )}


        {/* =====================================================
            RESULTS
        ===================================================== */}

        {scenarios.length > 0 && (

          <section className="results">

            <h2>
              Optimization Results
            </h2>


            {scenarios.map(
              (scenario, index) => {

                const {
                  materials,
                  totalWidthUsed,
                  totalProducedWeight,
                  scrapWidth,
                  scrapWeight,
                  totalCoilWeight,
                  coilWidth: resultCoilWidth,
                } =
                  getProducedMaterial(
                    scenario
                  );


                const totalStrips =
                  materials.reduce(
                    (total, item) =>
                      total +
                      item.strips,
                    0
                  );


                return (

                  <div
                    className="scenario-card"
                    key={index}
                  >

                    {/* =================================================
                        SCENARIO
                    ================================================= */}

                    <div className="scenario-title">

                      <h3>
                        Scenario {index + 1}
                      </h3>

                    </div>


                    {/* =================================================
                        PRODUCED MATERIAL
                    ================================================= */}

                    <div className="material-section">

                      <h4>
                        Produced Material
                      </h4>


                      <div className="material-table">

                        {/* HEADER */}

                        <div className="material-table-header">

                          <span>
                            Width
                          </span>

                          <span>
                            Strips
                          </span>

                          <span>
                            Total Width Used
                          </span>

                          <span>
                            Weight
                          </span>

                        </div>


                        {/* =================================================
                            MATERIAL ROWS
                        ================================================= */}

                        {materials.map(
                          (item) => (

                            <div
                              className="material-table-row"
                              key={
                                item.width_mm
                              }
                            >

                              <span>
                                {item.width_mm} mm
                              </span>


                              <span>
                                {item.strips}
                              </span>


                              <span>
                                {item.total_width_used} mm
                              </span>


                              <strong>
                                {item.weight.toFixed(
                                  2
                                )} kg
                              </strong>

                            </div>

                          )
                        )}


                        {/* =================================================
                            SCRAP ROW
                        ================================================= */}

                        <div className="material-table-row scrap-row">

                          <span>
                            Scrap
                          </span>

                          <span>
                            —
                          </span>

                          <span>
                            {scrapWidth} mm
                          </span>

                          <strong>
                            {scrapWeight.toFixed(
                              2
                            )} kg
                          </strong>

                        </div>


                        {/* =================================================
                            TOTAL ROW
                        ================================================= */}

                        <div className="material-table-total">

                          <strong>
                            Total
                          </strong>

                          <strong>
                            {totalStrips}
                          </strong>

                          <strong>
                            {(
                              totalWidthUsed +
                              scrapWidth
                            )} mm
                          </strong>

                          <strong>
                            {totalCoilWeight.toFixed(
                              2
                            )} kg
                          </strong>

                        </div>

                      </div>

                    </div>

                  </div>

                );

              }
            )}

          </section>

        )}

      </main>

    </div>
  );
}

export default App;