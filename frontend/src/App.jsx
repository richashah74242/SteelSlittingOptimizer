import { useState } from "react";

function App() {
  const [thickness, setThickness] = useState("");
  const [coilWidth, setCoilWidth] = useState("");
  const [coilWeight, setCoilWeight] = useState("");
  const [kerf, setKerf] = useState("");

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
      orders.filter(
        (_, i) => i !== index
      )
    );
  }

  function updateOrder(
    index,
    field,
    value
  ) {
    const updatedOrders = [
      ...orders,
    ];

    updatedOrders[index][field] =
      value;

    setOrders(
      updatedOrders
    );
  }

  async function optimize() {
    setLoading(true);

    setError("");

    setScenarios([]);

    try {
      const payload = {
        thickness_mm:
          Number(thickness),

        coil_width_mm:
          Number(coilWidth),

        kerf_mm:
          Number(kerf),

        coil_weight_kg:
          coilWeight
            ? Number(coilWeight)
            : null,

        orders:
          orders.map(
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
            .map(
              (width) =>
                Number(
                  width.trim()
                )
            )
            .filter(
              (width) =>
                width > 0
            ),

        top_n: Number(topN),
      };

      const response =
        await fetch(
          "http://127.0.0.1:8000/optimize",
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
        data.scenarios
      );
    } catch (error) {
      setError(
        error.message
      );
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

        <section className="card">

          <h2>
            Coil Details
          </h2>

          <div className="form-grid">

            <div className="form-group">

              <label>
                Thickness (mm)
              </label>

              <input
                type="number"
                min="0"
                step="0.01"
                value={thickness}
                onChange={(event) =>
                  setThickness(
                    event.target.value
                  )
                }
                placeholder="e.g. 0.8"
              />

            </div>

            <div className="form-group">

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

            <div className="form-group">

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

            <div className="form-group">

              <label>
                Kerf (mm)
              </label>

              <input
                type="number"
                min="0"
                step="0.01"
                value={kerf}
                onChange={(event) =>
                  setKerf(
                    event.target.value
                  )
                }
                placeholder="e.g. 6"
              />

            </div>

          </div>

        </section>

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
                      removeOrder(
                        index
                      )
                    }
                  >
                    Remove
                  </button>

                )}

              </div>

            )
          )}

        </section>

        <section className="card">

          <h2>
            Stock Widths
          </h2>

          <div className="form-group">

            <label>
              Available Stock Widths (mm)
            </label>

            <input
              type="text"
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

        <section className="card">

          <h2>
            Optimization Settings
          </h2>

          <div className="form-group">

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

        {scenarios.length > 0 && (

          <section className="results">

            <h2>
              Optimization Results
            </h2>

            {scenarios.map(
              (scenario, index) => (

                <div
                  className="scenario-card"
                  key={index}
                >

                  <div className="scenario-title">

                    <h3>
                      Scenario {index + 1}
                    </h3>

                  </div>

                  <div className="material-section">

                    <h4>
                      Customer Material
                    </h4>

                    {scenario.customer_material.map(
                      (item, itemIndex) => (

                        <div
                          className="material-row"
                          key={itemIndex}
                        >

                          <span>
                            {item.width_mm} mm
                          </span>

                          <strong>
                            × {item.strips} strips
                          </strong>

                        </div>

                      )
                    )}

                  </div>

                  <div className="material-section">

                    <h4>
                      Stock Material
                    </h4>

                    {scenario.stock_material
                      .filter(
                        (item) =>
                          item.strips > 0
                      )
                      .map(
                        (item, itemIndex) => (

                          <div
                            className="material-row"
                            key={itemIndex}
                          >

                            <span>
                              {item.width_mm} mm
                            </span>

                            <strong>
                              × {item.strips} strips
                            </strong>

                          </div>

                        )
                      )}

                  </div>

                  <div className="summary-grid">

                    <div>
                      <span>
                        Running Length
                      </span>

                      <strong>
                        {scenario.running_length_m} m
                      </strong>
                    </div>

                    <div>
                      <span>
                        Raw Material
                      </span>

                      <strong>
                        {scenario.raw_material_weight_kg} kg
                      </strong>
                    </div>

                    <div>
                      <span>
                        Customer Material
                      </span>

                      <strong>
                        {scenario.customer_weight_kg} kg
                      </strong>
                    </div>

                    <div>
                      <span>
                        Stock Material
                      </span>

                      <strong>
                        {scenario.stock_weight_kg} kg
                      </strong>
                    </div>

                    <div>
                      <span>
                        Scrap
                      </span>

                      <strong>
                        {scenario.scrap_weight_kg} kg
                      </strong>
                    </div>

                    <div>
                      <span>
                        Unused Width
                      </span>

                      <strong>
                        {scenario.unused_width_mm} mm
                      </strong>
                    </div>

                  </div>

                </div>

              )
            )}

          </section>

        )}

      </main>

    </div>
  );
}

export default App;