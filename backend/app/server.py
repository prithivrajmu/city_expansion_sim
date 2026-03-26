from __future__ import annotations

from flask import Flask, jsonify, request
from flask_cors import CORS

from .store import SESSION_STORE

app = Flask(__name__)
CORS(app)

SUPPORTED_COMMANDS = {"upzone_district", "build_transit", "flood_barrier"}


@app.errorhandler(KeyError)
def handle_missing_key(error: KeyError):
    return jsonify({"error": "not_found", "message": str(error)}), 404


@app.errorhandler(FileNotFoundError)
def handle_missing_file(error: FileNotFoundError):
    return jsonify({"error": "not_found", "message": str(error)}), 404


@app.errorhandler(ValueError)
def handle_bad_request(error: ValueError):
    return jsonify({"error": "bad_request", "message": str(error)}), 400


@app.errorhandler(TypeError)
def handle_type_error(error: TypeError):
    return jsonify({"error": "bad_request", "message": str(error)}), 400


def require_json_object() -> dict:
    payload = request.get_json(silent=True)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
    return payload


def parse_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must not be empty")
    return cleaned


def parse_steps(payload: dict) -> int:
    value = payload.get("steps", 1)
    if not isinstance(value, int):
        raise ValueError("steps must be an integer")
    if value < 1 or value > 24:
        raise ValueError("steps must be between 1 and 24")
    return value


def parse_command(payload: dict) -> dict:
    command_type = parse_string(payload.get("type"), "type")
    if command_type not in SUPPORTED_COMMANDS:
        raise ValueError(f"Unsupported command type: {command_type}")

    district = parse_string(payload.get("district"), "district")
    strength = payload.get("strength", 0.08)
    if not isinstance(strength, (int, float)):
        raise ValueError("strength must be a number")
    strength = float(strength)
    if strength < 0.01 or strength > 0.5:
        raise ValueError("strength must be between 0.01 and 0.5")

    return {"type": command_type, "district": district, "strength": strength}


def parse_optional_label(payload: dict) -> str | None:
    label = payload.get("label")
    if label is None:
        return None
    label = parse_string(label, "label")
    if len(label) > 64:
        raise ValueError("label must be 64 characters or fewer")
    return label


@app.get("/health")
def health() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@app.get("/scenarios")
def scenarios():
    return jsonify({"items": SESSION_STORE.list_scenarios()})


@app.get("/scenarios/<scenario_id>")
def scenario_detail(scenario_id: str):
    return jsonify(SESSION_STORE.scenario_definition(scenario_id))


@app.post("/authoring/validate/scenario")
def validate_scenario():
    payload = require_json_object()
    return jsonify(SESSION_STORE.validate_scenario_definition(payload))


@app.get("/campaigns")
def campaigns():
    return jsonify({"items": SESSION_STORE.list_campaigns()})


@app.get("/saves")
def saves():
    return jsonify({"items": SESSION_STORE.list_saves()})


@app.post("/sessions")
def create_session():
    payload = require_json_object()
    scenario_id = payload.get("scenarioId", "chennai_coastal_corridor")
    if not isinstance(scenario_id, str):
        raise ValueError("scenarioId must be a string")
    session = SESSION_STORE.create_session(scenario_id)
    return jsonify(session.to_payload()), 201


@app.post("/campaigns/<campaign_id>/runs")
def create_campaign_run(campaign_id: str):
    session = SESSION_STORE.create_campaign_run(campaign_id)
    return jsonify(session.to_payload()), 201


@app.get("/campaign-runs/<run_id>")
def get_campaign_run(run_id: str):
    return jsonify(SESSION_STORE.get_campaign_run(run_id))


@app.post("/campaign-runs/<run_id>/advance")
def advance_campaign_run(run_id: str):
    session = SESSION_STORE.advance_campaign_run(run_id)
    return jsonify(session.to_payload()), 201


@app.get("/sessions/<session_id>/state")
def get_state(session_id: str):
    session = SESSION_STORE.get_session(session_id)
    return jsonify(session.to_payload())


@app.post("/sessions/<session_id>/tick")
def tick(session_id: str):
    payload = require_json_object()
    steps = parse_steps(payload)
    session = SESSION_STORE.tick(session_id, steps)
    return jsonify(session.to_payload())


@app.post("/sessions/<session_id>/commands")
def apply_command(session_id: str):
    payload = parse_command(require_json_object())
    session = SESSION_STORE.apply_command(session_id, payload)
    return jsonify(session.to_payload())


@app.get("/sessions/<session_id>/metrics")
def metrics(session_id: str):
    session = SESSION_STORE.get_session(session_id)
    return jsonify({"metrics": session.snapshot.metrics, "events": session.snapshot.events[-5:]})


@app.get("/sessions/<session_id>/report")
def report(session_id: str):
    return jsonify(SESSION_STORE.report(session_id))


@app.get("/sessions/<session_id>/timeline")
def timeline(session_id: str):
    return jsonify({"items": SESSION_STORE.timeline(session_id)})


@app.get("/sessions/<session_id>/replay/<int:tick>")
def replay(session_id: str, tick: int):
    return jsonify(SESSION_STORE.replay(session_id, tick))


@app.post("/sessions/<session_id>/save")
def save_session(session_id: str):
    payload = require_json_object()
    return jsonify(SESSION_STORE.save_session(session_id, parse_optional_label(payload))), 201


@app.post("/saves/<save_id>/load")
def load_save(save_id: str):
    session = SESSION_STORE.load_save(save_id)
    return jsonify(session.to_payload()), 201
