import os
import time
import requests
from dash import Dash, html, dcc, Input, Output, State, no_update, callback_context
from dash.exceptions import PreventUpdate

# ─── Configuration ─────────────────────────────────────────────────────────────
DATABRICKS_INSTANCE = "https://dbc-4ff3d9fe-2240.cloud.databricks.com"
DATABRICKS_TOKEN    = "dapied620788912c33d028c5e1fbaa4ebb87"
JOB_ID              = 846942694131253  # your notebook-task Job ID

HEADERS = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
    "Content-Type":  "application/json"
}

# ─── Dash App Layout ──────────────────────────────────────────────────────────
app = Dash(__name__)
app.layout = html.Div([
    html.H3("🔎 Ask Nimble-Maps Agent"),
    dcc.Input(
        id="user-input",
        type="text",
        placeholder="Enter your question…",
        style={"width": "80%", "padding": "8px"}
    ),
    html.Button("Run Agent", id="run-button", n_clicks=0, style={"margin": "8px"}),
    dcc.Loading(
        id="loading-spinner",
        type="default",
        children=html.Div(
            id="result",
            style={"whiteSpace": "pre-wrap", "marginTop": "16px"}
        )
    ),
    dcc.Store(id="start-time"),
    dcc.Store(id="run-id"),
    dcc.Interval(id="poll-interval", interval=2000, disabled=True)
])

# ─── Trigger the notebook job ─────────────────────────────────────────────────
def trigger_notebook(question: str) -> int:
    payload = {"job_id": JOB_ID, "notebook_params": {"question": question}}
    resp = requests.post(
        f"{DATABRICKS_INSTANCE}/api/2.1/jobs/run-now",
        headers=HEADERS,
        json=payload
    )
    resp.raise_for_status()
    return resp.json().get("run_id")

# ─── Single callback: start job & poll for output ──────────────────────────────
@app.callback(
    Output("start-time",   "data"),
    Output("run-id",       "data"),
    Output("result",       "children"),
    Output("poll-interval","disabled"),
    Input("run-button",    "n_clicks"),
    Input("poll-interval", "n_intervals"),
    State("user-input",    "value"),
    State("run-id",        "data"),
    State("start-time",    "data")
)
def manage_run(n_clicks, n_intervals, question, run_id, start_ts):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    # 1) User clicked Run Agent
    if trigger == "run-button":
        if not question:
            return no_update, no_update, "⚠️ Please enter a question.", True
        new_run_id = trigger_notebook(question)
        return (
            time.time(),
            new_run_id,
            f"✅ Job launched – run_id={new_run_id}",
            False
        )

    # 2) Polling interval tick
    if trigger == "poll-interval" and run_id and start_ts:
        # check lifecycle state
        state_resp = requests.get(
            f"{DATABRICKS_INSTANCE}/api/2.1/jobs/runs/get",
            headers=HEADERS,
            params={"run_id": run_id}
        )
        if state_resp.ok:
            st = state_resp.json().get("state", {})
            life = st.get("life_cycle_state")
            result_state = st.get("result_state")

            # still running
            if life in ("PENDING", "RUNNING", "TERMINATING"):
                elapsed = int(time.time() - start_ts)
                return (
                    start_ts,
                    run_id,
                    f"⏳ Job running… {elapsed}s elapsed (state={life})",
                    False
                )

            # finished
            if life == "TERMINATED":
                if result_state == "SUCCESS":
                    out_resp = requests.get(
                        f"{DATABRICKS_INSTANCE}/api/2.1/jobs/runs/get-output",
                        headers=HEADERS,
                        params={"run_id": run_id}
                    )
                    # if out_resp.status_code == 200:
                        # result = out_resp.json()
                    result = out_resp.json().get("notebook_output", {}).get("result", "(no output)")
                    # else:
                    #     result = f"✅ Completed but no notebook output (status={out_resp.status_code})"
                else:
                    result = f"❌ Job terminated with state: {result_state}"
                return (
                    no_update,
                    no_update,
                    result,
                    True
                )
        # state API failed
        elapsed = int(time.time() - start_ts)
        return (
            start_ts,
            run_id,
            f"⚠️ Poll error, retrying… {elapsed}s elapsed",
            False
        )

    # nothing else
    raise PreventUpdate

# ─── Run server ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run_server(debug=True)
