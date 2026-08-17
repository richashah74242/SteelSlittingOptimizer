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
   */
  function getProducedMaterial(scenario) {
    const materialMap = new Map();

    /*
     * ------------------------------------------------------------
     * CUSTOMER MATERIAL
     * ------------------------------------------------------------
     */
    (scenario.customer_material || [])
      .filter((item) => Number(item.strips || 0) > 0)
      .forEach((item) => {
        const width = Number(item.width_mm || 0);

        const existing =
          materialMap.get(width) || {
            width_mm: width,
            strips: 0,
            required_weight_kg: 0,
            is_customer: false,
          };

        existing.strips += Number(
          item.strips || 0
        );

        existing.is_customer = true;

        existing.required_weight_kg += Number(
          item.required_weight_kg || 0
        );

        materialMap.set(width, existing);
      });

    /*
     * ------------------------------------------------------------
     * STOCK MATERIAL
     * ------------------------------------------------------------
     */
    (scenario.stock_material || [])
      .filter((item) => Number(item.strips || 0) > 0)
      .forEach((item) => {
        const width = Number(item.width_mm || 0);

        const existing =
          materialMap.get(width) || {
            width_mm: width,
            strips: 0,
            required_weight_kg: 0,
            is_customer: false,
          };

        existing.strips += Number(
          item.strips || 0
        );

        materialMap.set(width, existing);
      });

    /*
     * ------------------------------------------------------------
     * SORT MATERIALS BY WIDTH
     * ------------------------------------------------------------
     */
    const materials = Array.from(
      materialMap.values()
    ).sort(
      (a, b) =>
        a.width_mm - b.width_mm
    );

    /*
     * ------------------------------------------------------------
     * TOTAL PRODUCED WIDTH
     * ------------------------------------------------------------
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
     * ------------------------------------------------------------
     * ACTUAL PRODUCED WEIGHT
     * ------------------------------------------------------------
     *
     * Customer + stock material.
     */
    const totalProducedWeight =
      Number(
        scenario.customer_weight_kg || 0
      ) +
      Number(
        scenario.stock_weight_kg || 0
      ) +
      Number(
        scenario.scrap_weight_kg || 0
      );
        const resultCoilWidth =
        Number(
          scenario.coil_width_mm ||
            coilWidth ||
            0
        );

      const totalCoilWeight =
        Number(
          scenario.raw_material_weight_kg || 0
        );
    /*
     * ------------------------------------------------------------
     * MATERIAL ACTUAL WEIGHTS
     * ------------------------------------------------------------
     *
     * Weight is distributed according to
     * each material's share of produced width.
     */
    const materialsWithWeight =
      materials.map((item) => {
        const materialWidth =
          item.width_mm *
          item.strips;

        const weight =
          resultCoilWidth > 0
            ? (
                totalCoilWeight *
                materialWidth /
                resultCoilWidth
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
     * ------------------------------------------------------------
     * RESULT COIL WIDTH
     * ------------------------------------------------------------
     *
     * IMPORTANT:
     * Do NOT create a variable called "coilWidth"
     * here because "coilWidth" already exists as React state.
     */

    const kerfWidth =
      Number(
        scenario.kerf_width_mm || 0
      );

    const unusedWidth =
      Number(
        scenario.unused_width_mm || 0
      );
    /*
     * ------------------------------------------------------------
     * SCRAP WIDTH
     * ------------------------------------------------------------
     */
const scrapWidth =
  kerfWidth +
  unusedWidth;

    /*
     * ------------------------------------------------------------
     * SCRAP WEIGHT
     * ------------------------------------------------------------
     *
     * Prefer backend scrap weight.
     *
     * If backend does not provide it,
     * calculate it from coil weight.
     */
 const scrapWeight =
  Number(
    scenario.scrap_weight_kg || 0
  );

    /*
     * ------------------------------------------------------------
     * TOTAL CUSTOMER REQUIRED WEIGHT
     * ------------------------------------------------------------
     */
    const totalRequiredWeight =
      materialsWithWeight.reduce(
        (total, item) =>
          total +
          Number(
            item.required_weight_kg || 0
          ),
        0
      );

    return {
      materials:
        materialsWithWeight,

      totalWidthUsed,

      totalProducedWeight,

      totalRequiredWeight,

      scrapWidth,

      scrapWeight,

      resultCoilWidth,
    };
  }

  /*
   * ============================================================
   * OPTIMIZE
   * ============================================================
   */
  async function optimize() {
    setLoading(true);
    setError("");
    setScenarios([]);

    try {
      /*
       * Validate coil width.
       */
      if (
        !coilWidth ||
        Number(coilWidth) <= 0
      ) {
        throw new Error(
          "Please enter a valid coil width."
        );
      }

      /*
       * Validate orders.
       */
      const validOrders =
        orders.filter(
          (order) =>
            Number(order.width_mm) > 0 &&
            Number(
              order.required_weight_kg
            ) >= 0
        );

      if (validOrders.length === 0) {
        throw new Error(
          "Please enter at least one valid customer order."
        );
      }

      /*
       * Parse stock widths.
       */
      const parsedStockWidths =
        stockWidths
          .split(",")
          .map((width) =>
            Number(width.trim())
          )
          .filter(
            (width) => width > 0
          );

      if (
        parsedStockWidths.length === 0
      ) {
        throw new Error(
          "Please enter at least one stock width."
        );
      }

      /*
       * ----------------------------------------------------------
       * API PAYLOAD
       * ----------------------------------------------------------
       */
      const payload = {
        coil_width_mm:
          Number(coilWidth),

        coil_weight_kg:
          coilWeight
            ? Number(coilWeight)
            : null,

        orders: validOrders.map(
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
          parsedStockWidths,

        top_n: 6,
      };

      /*
       * ----------------------------------------------------------
       * API URL
       * ----------------------------------------------------------
       */
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

      /*
       * ----------------------------------------------------------
       * READ RESPONSE
       * ----------------------------------------------------------
       */
      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Optimization failed"
        );
      }

      /*
       * ----------------------------------------------------------
       * GET SCENARIOS
       * ----------------------------------------------------------
       */
      const receivedScenarios =
        data.scenarios || [];

      /*
       * ----------------------------------------------------------
       * SORT SCENARIOS
       * ----------------------------------------------------------
       *
       * PRIORITY:
       *
       * 1. Lower scrap width
       * 2. If scrap width is same:
       *    lower scrap weight
       * 3. If both are same:
       *    lower customer overproduction
       * 4. If still same:
       *    lower total number of strips
       *
       * This means:
       *
       * Scenario A:
       * Scrap = 10 mm
       * Scrap weight = 250 kg
       *
       * Scenario B:
       * Scrap = 10 mm
       * Scrap weight = 200 kg
       *
       * Scenario B will be Scenario 1.
       */
      const sortedScenarios =
        receivedScenarios
          .map((scenario) => {
            const display =
              getProducedMaterial(
                scenario
              );

            const customerOverproduction =
              Math.max(
                0,
                Number(
                  scenario.customer_weight_kg ||
                    0
                ) -
                  display.totalRequiredWeight
              );

            const totalStrips =
              display.materials.reduce(
                (total, item) =>
                  total +
                  Number(
                    item.strips || 0
                  ),
                0
              );

            return {
              scenario,

              sortScrapWidth:
                Number(
                  display.scrapWidth || 0
                ),

              sortScrapWeight:
                Number(
                  display.scrapWeight || 0
                ),

              sortOverproduction:
                customerOverproduction,

              sortTotalStrips:
                totalStrips,
            };
          })

          .sort((a, b) => {
            /*
             * 1. Scrap width
             */
            if (
              a.sortScrapWidth !==
              b.sortScrapWidth
            ) {
              return (
                a.sortScrapWidth -
                b.sortScrapWidth
              );
            }

            /*
             * 2. Scrap weight
             */
            if (
              a.sortScrapWeight !==
              b.sortScrapWeight
            ) {
              return (
                a.sortScrapWeight -
                b.sortScrapWeight
              );
            }

            /*
             * 3. Customer overproduction
             */
            if (
              a.sortOverproduction !==
              b.sortOverproduction
            ) {
              return (
                a.sortOverproduction -
                b.sortOverproduction
              );
            }

            /*
             * 4. Number of strips
             */
            return (
              a.sortTotalStrips -
              b.sortTotalStrips
            );
          })

          .map(
            (item) =>
              item.scenario
          );

      setScenarios(
        sortedScenarios
      );
    } catch (error) {
      console.error(
        "Optimization error:",
        error
      );

      setError(
        error.message ||
          "Something went wrong while optimizing."
      );
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
            OPTIMIZE BUTTON
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
                  totalRequiredWeight,
                  scrapWidth,
                  scrapWeight,
                  resultCoilWidth,
                } =
                  getProducedMaterial(
                    scenario
                  );

                /*
                 * Total strips.
                 */
                const totalStrips =
                  materials.reduce(
                    (total, item) =>
                      total +
                      Number(
                        item.strips || 0
                      ),
                    0
                  );

                /*
                 * Actual total weight.
                 */
                const totalActualWeight =
                  Number(
                    scenario.raw_material_weight_kg || 0
                  );

                return (

                  <div
                    className="scenario-card"
                    key={index}
                  >

                    {/* =================================================
                        SCENARIO TITLE
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
                            Required Weight
                          </span>

                          <span>
                            Actual Weight
                          </span>

                        </div>


                        {/* MATERIAL ROWS */}

                        {materials.map(
                          (item) => (

                            <div
                              className="material-table-row"
                              key={`${item.width_mm}-${item.is_customer}`}
                            >

                              <span>
                                {item.width_mm} mm
                              </span>


                              <span>
                                {item.strips}
                              </span>


                              <span>
                                {
                                  item.total_width_used
                                }{" "}
                                mm
                              </span>


                              <span>
                                {item.is_customer &&
                                Number(
                                  item.required_weight_kg
                                ) > 0
                                  ? `${Number(
                                      item.required_weight_kg
                                    ).toFixed(2)} kg`
                                  : "—"}
                              </span>


                              <strong>
                                {Number(
                                  item.weight || 0
                                ).toFixed(2)}{" "}
                                kg
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
                            {scrapWidth.toFixed(
                              2
                            )}{" "}
                            mm
                          </span>

                          <span>
                            —
                          </span>

                          <strong>
                            {scrapWeight.toFixed(
                              2
                            )}{" "}
                            kg
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
                            {totalWidthUsed.toFixed(
                              2
                            )}{" "}
                            mm
                          </strong>

                          <strong>
                            {totalRequiredWeight.toFixed(
                              2
                            )}{" "}
                            kg
                          </strong>

                          <strong>
                            {totalActualWeight.toFixed(
                              2
                            )}{" "}
                            kg
                          </strong>

                        </div>

                      </div>

                    </div>


                    {/* =================================================
                        COIL SUMMARY
                    ================================================= */}

                    <div className="coil-summary">

                      <span>
                        Coil Width
                      </span>

                      <strong>
                        {resultCoilWidth.toFixed(
                          2
                        )}{" "}
                        mm
                      </strong>


                      <span>
                        Produced Width
                      </span>

                      <strong>
                        {totalWidthUsed.toFixed(
                          2
                        )}{" "}
                        mm
                      </strong>


                      <span>
                        Scrap Width
                      </span>

                      <strong>
                        {scrapWidth.toFixed(
                          2
                        )}{" "}
                        mm
                      </strong>

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