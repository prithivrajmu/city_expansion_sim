from app.server import app
from simulation.core.engine import Scenario, SimulationSession


def make_strategy_scenario(district_strategies=None):
    return Scenario(
        id="district-strategy-test",
        name="District Strategy Test",
        description="Scenario used to verify district strategy modifiers.",
        focus="District strategy behavior",
        baseYear=2026,
        ticksPerYear=4,
        gridWidth=2,
        gridHeight=1,
        policyBoost=0.12,
        residentDemand=0.66,
        developerPressure=0.74,
        infrastructureMomentum=0.71,
        agentProfiles={
            "residents": {"mobility": 1.0, "housingUrgency": 1.0},
            "developers": {"capitalAggression": 1.0, "speculation": 1.0},
            "government": {"deliveryBias": 1.0, "coordination": 1.0},
        },
        events=[],
        cells=[
            {
                "district": "Growth District",
                "kind": "urban",
                "urbanized": True,
                "population": 200,
                "landValue": 150,
                "risk": 0.2,
                "access": 0.7,
            },
            {
                "district": "Resilience District",
                "kind": "urban",
                "urbanized": True,
                "population": 200,
                "landValue": 150,
                "risk": 0.2,
                "access": 0.7,
            },
        ],
        districtStrategies=district_strategies,
    )


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_session_tick_command_and_report_flow():
    client = app.test_client()

    create_response = client.post("/sessions", json={"scenarioId": "chennai_coastal_corridor"})
    assert create_response.status_code == 201
    payload = create_response.get_json()
    session_id = payload["sessionId"]
    assert payload["snapshot"]["metrics"]["urbanCells"] > 0

    command_response = client.post(
        f"/sessions/{session_id}/commands",
        json={"type": "build_transit", "district": "Outer Growth", "strength": 0.12},
    )
    assert command_response.status_code == 200
    command_payload = command_response.get_json()
    assert command_payload["snapshot"]["interventions"][-1]["type"] == "build_transit"

    tick_response = client.post(f"/sessions/{session_id}/tick", json={"steps": 2})
    assert tick_response.status_code == 200
    tick_payload = tick_response.get_json()
    assert tick_payload["snapshot"]["tick"] == 2

    report_response = client.get(f"/sessions/{session_id}/report")
    assert report_response.status_code == 200
    report = report_response.get_json()
    assert "headline" in report
    assert len(report["growthFrontier"]) == 3
    assert "agentSummary" in report


def test_save_load_and_replay_flow():
    client = app.test_client()
    create_response = client.post("/sessions", json={"scenarioId": "metro_delta_arc"})
    session_id = create_response.get_json()["sessionId"]

    client.post(
        f"/sessions/{session_id}/commands",
        json={"type": "upzone_district", "district": "Outer Arc", "strength": 0.11},
    )
    client.post(f"/sessions/{session_id}/tick", json={"steps": 3})

    timeline_response = client.get(f"/sessions/{session_id}/timeline")
    assert timeline_response.status_code == 200
    assert len(timeline_response.get_json()["items"]) >= 2

    replay_response = client.get(f"/sessions/{session_id}/replay/0")
    assert replay_response.status_code == 200
    assert replay_response.get_json()["tick"] == 0

    save_response = client.post(f"/sessions/{session_id}/save", json={"label": "test-save"})
    assert save_response.status_code == 201
    save_id = save_response.get_json()["saveId"]

    saves_response = client.get("/saves")
    assert saves_response.status_code == 200
    assert any(item["saveId"] == save_id for item in saves_response.get_json()["items"])

    load_response = client.post(f"/saves/{save_id}/load")
    assert load_response.status_code == 201
    loaded = load_response.get_json()
    assert loaded["snapshot"]["tick"] == 3


def test_scenario_events_affect_runtime_state():
    client = app.test_client()
    create_response = client.post("/sessions", json={"scenarioId": "metro_delta_arc"})
    session_id = create_response.get_json()["sessionId"]

    tick_response = client.post(f"/sessions/{session_id}/tick", json={"steps": 3})
    snapshot = tick_response.get_json()["snapshot"]
    assert snapshot["metrics"]["eventCount"] >= 2

    report_response = client.get(f"/sessions/{session_id}/report")
    report = report_response.get_json()
    assert len(report["scenarioEvents"]) >= 2


def test_district_strategy_modes_change_runtime_behavior():
    session = SimulationSession(
        make_strategy_scenario(
            {
                "Growth District": {"mode": "growth_first"},
                "Resilience District": {"mode": "resilience_first"},
            }
        )
    )

    session.tick()

    growth_cell, resilience_cell = session.cells
    assert growth_cell["access"] > resilience_cell["access"]
    assert growth_cell["landValue"] > resilience_cell["landValue"]
    assert growth_cell["population"] > resilience_cell["population"]
    assert growth_cell["risk"] > resilience_cell["risk"]


def test_district_without_strategy_uses_safe_defaults():
    baseline_session = SimulationSession(make_strategy_scenario())
    partial_strategy_session = SimulationSession(
        make_strategy_scenario({"Growth District": {"mode": "growth_first"}})
    )

    baseline_session.tick()
    partial_strategy_session.tick()

    baseline_resilience = baseline_session.cells[1]
    unconfigured_resilience = partial_strategy_session.cells[1]
    assert unconfigured_resilience["access"] == baseline_resilience["access"]
    assert unconfigured_resilience["landValue"] == baseline_resilience["landValue"]
    assert unconfigured_resilience["population"] == baseline_resilience["population"]
    assert unconfigured_resilience["risk"] == baseline_resilience["risk"]
