from app.server import app
from app.store import SESSION_STORE
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
        horizonTicks=4,
        objectives=[
            {"id": "growth", "title": "Grow district population", "metric": "population", "target": 4200, "comparator": "at_least"},
            {"id": "risk", "title": "Keep risk controlled", "metric": "averageRisk", "target": 0.3, "comparator": "at_most"},
        ],
        initialBudget=500,
        initialPoliticalCapital=220,
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


def test_scenario_detail_exposes_authoring_summary():
    client = app.test_client()
    response = client.get("/scenarios/chennai_coastal_corridor")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["scenario"]["id"] == "chennai_coastal_corridor"
    assert payload["authoring"]["districtCount"] > 0
    assert payload["validation"]["valid"] is True


def test_authoring_validation_flags_invalid_scenario_shape():
    client = app.test_client()
    response = client.post(
        "/authoring/validate/scenario",
        json={
            "id": "broken",
            "name": "Broken Scenario",
            "description": "Missing core fields and malformed references.",
            "focus": "Validation",
            "gridWidth": 2,
            "gridHeight": 2,
            "horizonTicks": 4,
            "objectives": [{"id": "x", "title": "Bad", "metric": "notReal", "target": 1}],
            "events": [{"tick": 1, "title": "Ghost event", "district": "Missing", "impact": {}}],
            "cells": [{"district": "Only", "kind": "green", "urbanized": False, "population": 10, "landValue": 10, "risk": 0.1, "access": 0.2}],
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["valid"] is False
    assert any(issue["field"] == "cells" for issue in payload["issues"])
    assert any(issue["field"] == "objectives[0].metric" for issue in payload["issues"])


def test_session_tick_command_and_report_flow():
    client = app.test_client()

    create_response = client.post("/sessions", json={"scenarioId": "chennai_coastal_corridor"})
    assert create_response.status_code == 201
    payload = create_response.get_json()
    session_id = payload["sessionId"]
    assert payload["snapshot"]["metrics"]["urbanCells"] > 0
    assert payload["snapshot"]["metrics"]["budget"] > 0
    assert payload["snapshot"]["metrics"]["politicalCapital"] > 0

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
    assert "comparison" in report
    assert "districtComparison" in report
    assert "interventionROI" in report
    assert "resources" in report
    assert "objectives" in report
    assert "evaluation" in report
    assert payload["campaign"] is None


def test_campaign_listing_and_run_progression_flow():
    client = app.test_client()

    campaigns_response = client.get("/campaigns")
    assert campaigns_response.status_code == 200
    campaigns = campaigns_response.get_json()["items"]
    assert any(item["id"] == "southern_growth_arc" for item in campaigns)

    run_response = client.post("/campaigns/southern_growth_arc/runs")
    assert run_response.status_code == 201
    payload = run_response.get_json()
    assert payload["campaign"]["campaignId"] == "southern_growth_arc"
    assert payload["campaign"]["stageIndex"] == 0
    assert payload["scenarioId"] == "chennai_coastal_corridor"

    session_id = payload["sessionId"]
    campaign_session = SESSION_STORE._sessions[session_id]
    campaign_session.tick_count = campaign_session.scenario.horizonTicks
    campaign_session.budget = 200
    campaign_session.political_capital = 140
    for cell in campaign_session.cells:
        if cell["kind"] != "water":
            cell["urbanized"] = True
            cell["kind"] = "urban"
            cell["risk"] = min(cell["risk"], 0.2)
    campaign_session._record_history()

    advance_response = client.post(f"/campaign-runs/{payload['campaign']['runId']}/advance")
    assert advance_response.status_code == 201
    advanced = advance_response.get_json()
    assert advanced["campaign"]["stageIndex"] == 1
    assert advanced["scenarioId"] == "metro_delta_arc"
    assert advanced["snapshot"]["metrics"]["budget"] > 580
    assert advanced["snapshot"]["metrics"]["politicalCapital"] > 260

    run_status_response = client.get(f"/campaign-runs/{payload['campaign']['runId']}")
    assert run_status_response.status_code == 200
    run_status = run_status_response.get_json()
    assert len(run_status["completedStages"]) == 1
    assert run_status["currentStage"]["scenarioId"] == "metro_delta_arc"


def test_campaign_advance_requires_horizon_completion():
    client = app.test_client()
    run_response = client.post("/campaigns/southern_growth_arc/runs")
    run_payload = run_response.get_json()

    response = client.post(f"/campaign-runs/{run_payload['campaign']['runId']}/advance")
    assert response.status_code == 400
    assert response.get_json()["error"] == "bad_request"


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
    assert "path" not in saves_response.get_json()["items"][0]


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


def test_invalid_scenario_id_returns_404():
    client = app.test_client()
    response = client.post("/sessions", json={"scenarioId": "../missing"})
    assert response.status_code == 404
    assert response.get_json()["error"] == "not_found"


def test_invalid_save_id_returns_404():
    client = app.test_client()
    response = client.post("/saves/not-a-real-save/load")
    assert response.status_code == 404
    assert response.get_json()["error"] == "not_found"


def test_invalid_campaign_id_returns_404():
    client = app.test_client()
    response = client.post("/campaigns/not-a-real-campaign/runs")
    assert response.status_code == 404
    assert response.get_json()["error"] == "not_found"


def test_report_exposes_baseline_deltas_and_intervention_roi():
    client = app.test_client()
    create_response = client.post("/sessions", json={"scenarioId": "metro_delta_arc"})
    session_id = create_response.get_json()["sessionId"]

    client.post(
        f"/sessions/{session_id}/commands",
        json={"type": "build_transit", "district": "Outer Arc", "strength": 0.12},
    )
    client.post(f"/sessions/{session_id}/tick", json={"steps": 2})

    report = client.get(f"/sessions/{session_id}/report").get_json()
    assert report["comparison"]["currentTick"] == 2
    assert any(item["district"] == "Outer Arc" for item in report["districtComparison"])
    assert any(item["type"] == "build_transit" for item in report["interventionROI"])


def test_intervention_requires_budget_and_political_capital():
    session = SimulationSession(
        make_strategy_scenario(
            {
                "Growth District": {"mode": "growth_first"},
                "Resilience District": {"mode": "resilience_first"},
            }
        )
    )
    session.budget = 10
    session.political_capital = 5

    try:
        session.apply_command({"type": "build_transit", "district": "Growth District", "strength": 0.2})
        assert False, "Expected insufficient-resource error"
    except ValueError as error:
        assert "Insufficient" in str(error)


def test_tick_replenishes_budget_and_political_capital():
    session = SimulationSession(make_strategy_scenario())
    baseline_budget = session.budget
    baseline_political = session.political_capital

    session.tick()

    assert session.budget > baseline_budget
    assert session.political_capital > baseline_political


def test_report_exposes_objective_progress_and_evaluation():
    client = app.test_client()
    create_response = client.post("/sessions", json={"scenarioId": "chennai_coastal_corridor"})
    session_id = create_response.get_json()["sessionId"]

    client.post(f"/sessions/{session_id}/tick", json={"steps": 8})
    report = client.get(f"/sessions/{session_id}/report").get_json()

    assert report["evaluation"]["tick"] == 8
    assert report["evaluation"]["status"] in {"success", "at_risk"}
    assert len(report["objectives"]) == 3


def test_invalid_tick_payload_returns_400():
    client = app.test_client()
    create_response = client.post("/sessions", json={"scenarioId": "metro_delta_arc"})
    session_id = create_response.get_json()["sessionId"]

    response = client.post(f"/sessions/{session_id}/tick", json={"steps": "three"})
    assert response.status_code == 400
    assert response.get_json()["error"] == "bad_request"


def test_invalid_command_payload_returns_400():
    client = app.test_client()
    create_response = client.post("/sessions", json={"scenarioId": "metro_delta_arc"})
    session_id = create_response.get_json()["sessionId"]

    response = client.post(
        f"/sessions/{session_id}/commands",
        json={"type": "build_transit", "district": "Outer Arc", "strength": "high"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "bad_request"


def test_session_store_evicts_old_sessions_when_capacity_is_reached():
    SESSION_STORE._sessions.clear()
    first_session_id = client = None
    for index in range(SESSION_STORE._max_sessions + 1):
        payload = app.test_client().post("/sessions", json={"scenarioId": "metro_delta_arc"}).get_json()
        if index == 0:
            first_session_id = payload["sessionId"]

    assert first_session_id is not None
    response = app.test_client().get(f"/sessions/{first_session_id}/state")
    assert response.status_code == 404
