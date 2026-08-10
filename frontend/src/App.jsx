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
    "40,110,144,232,206"
  );

  const [topN, setTopN] = useState(10);
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
   * Combine customer and stock material having
   * the same width.
   */
  function getProducedMaterial(scenario) {
    const materialMap = new Map();

    const addMaterial = (items) => {
      items
        .filter((item) => item.strips > 0)
        .forEach((item) => {
          const existing =
            materialMap.get(item.width_mm) || {
              width_mm: item.width_mm,
              strips: 0,
              typeWidth: 0,
            };

          existing.strips += item.strips;

          materialMap.set(
            item.width_mm,
            existing
          );
        });
    };

    addMaterial(
      scenario.customer_material || []
    );

    addMaterial(
      scenario.stock_material || []
    );

    const materials = Array.from(
      materialMap.values()
    ).sort(
      (a, b) =>
        a.width_mm - b.width_mm
    );

    /*
     * Backend gives us customer and stock total
     * weights. Since every strip in a scenario has
     * the same running length and thickness,
     * weight is proportional to width × strips.
     *
     * Therefore we can derive the individual
     * displayed weight without changing backend
     * weight calculations.
     */
    const totalProducedWeight =
      Number(
        scenario.customer_weight_kg || 0
      ) +
      Number(
        scenario.stock_weight_kg || 0
      );

    const totalWidth = materials.reduce(
      (total, item) =>
        total +
        item.width_mm * item.strips,
      0
    );

    return materials.map((item) => {
      const materialWidth =
        item.width_mm * item.strips;

      const weight =
        totalWidth > 0
          ? (
              totalProducedWeight *
              materialWidth /
              totalWidth
            )
          : 0;

      return {
        ...item,
        weight,
      };
    });
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
              Number(order.width_mm),

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

        top_n: Number(topN),
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

          body: JSON.stringify(payload),
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
        data.scenarios
      );
    } catch (error) {
      setError(error.message);
    }

    setLoading(false);
  }

  return (
    <div className="app">

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

        {/* COIL DETAILS */}

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

        {/* CUSTOMER ORDERS */}

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

        {/* STOCK WIDTHS */}

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

        {/* OPTIMIZATION SETTINGS */}

        <section className="card">

          <h2>
            Optimization Settings
          </h2>

          <div className="input-group">

            <label>
              Number of Scenarios
            </label>

            <input
              type="number"
              min="1"
              max="100"
              value={topN}
              onChange={(event) =>
                setTopN(
                  event.target.value
                )
              }
            />

          </div>

        </section>

        <button
          className="optimize-button"
          onClick={optimize}
          disabled={loading}
        >
          {loading
            ? "Optimizing..."
            : "Optimize"}
        </button>

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {/* RESULTS */}

        {scenarios.length > 0 && (

          <section className="results">

            <h2>
              Optimization Results
            </h2>

            {scenarios.map(
              (scenario, index) => {

                const materials =
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

                const totalProduced =
                  Number(
                    scenario.customer_weight_kg ||
                      0
                  ) +
                  Number(
                    scenario.stock_weight_kg ||
                      0
                  );

                /*
                 * Kerf is always 5 mm.
                 * It is included in total scrap width.
                 */
                const totalScrapWidth =
                  Number(
                    scenario.unused_width_mm ||
                      0
                  ) + 5;

                return (

                  <div
                    className="scenario-card"
                    key={index}
                  >

                    <div className="scenario-title">

                      <h3>
                        Scenario {index + 1}
                      </h3>

                    </div>

                    {/* PRODUCED MATERIAL */}

                    <div className="material-section">

                      <h4>
                        Produced Material
                      </h4>

                      <div className="material-table">

                        <div className="material-table-header">

                          <span>
                            Width
                          </span>

                          <span>
                            Strips
                          </span>

                          <span>
                            Weight
                          </span>

                        </div>

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

                              <strong>
                                {item.weight.toFixed(
                                  2
                                )} kg
                              </strong>

                            </div>

                          )
                        )}

                        {/* TOTAL */}

                        <div className="material-table-total">

                          <strong>
                            Total
                          </strong>

                          <strong>
                            {totalStrips}
                          </strong>

                          <strong>
                            {totalProduced.toFixed(
                              2
                            )} kg
                          </strong>

                        </div>

                      </div>

                    </div>

                    {/* FINAL SUMMARY */}

                    <div className="summary-grid">

                      <div>

                        <span>
                          Total Scrap Width
                        </span>

                        <strong>
                          {totalScrapWidth} mm
                        </strong>

                      </div>

                      <div>

                        <span>
                          Total Produced
                        </span>

                        <strong>
                          {totalProduced.toFixed(
                            2
                          )} kg
                        </strong>

                      </div>

                      <div>

                        <span>
                          Scrap Weight
                        </span>

                        <strong>
                          {Number(
                            scenario.scrap_weight_kg ||
                              0
                          ).toFixed(2)} kg
                        </strong>

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