from __future__ import annotations

from flask import Flask, jsonify, request
from flask_cors import CORS

from .store import SESSION_STORE

app = Flask(__name__)
CORS(app)


@app.errorhandler(KeyError)
def handle_missing_key(error: KeyError):
    return jsonify({"error": "not_found", "message": str(error)}), 404


@app.errorhandler(FileNotFoundError)
def handle_missing_file(error: FileNotFoundError):
    return jsonify({"error": "not_found", "message": str(error)}), 404


@app.errorhandler(ValueError)
def handle_bad_request(error: ValueError):
    return jsonify({"error": "bad_request", "message": str(error)}), 400


@app.get("/health")
def health() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@app.get("/scenarios")
def scenarios():
    return jsonify({"items": SESSION_STORE.list_scenarios()})


@app.get("/saves")
def saves():
    return jsonify({"items": SESSION_STORE.list_saves()})


@app.post("/sessions")
def create_session():
    payload = request.get_json(silent=True) or {}
    scenario_id = payload.get("scenarioId", "chennai_coastal_corridor")
    session = SESSION_STORE.create_session(scenario_id)
    return jsonify(session.to_payload()), 201


@app.get("/sessions/<session_id>/state")
def get_state(session_id: str):
    session = SESSION_STORE.get_session(session_id)
    return jsonify(session.to_payload())


@app.post("/sessions/<session_id>/tick")
def tick(session_id: str):
    payload = request.get_json(silent=True) or {}
    steps = max(1, min(int(payload.get("steps", 1)), 24))
    session = SESSION_STORE.tick(session_id, steps)
    return jsonify(session.to_payload())


@app.post("/sessions/<session_id>/commands")
def apply_command(session_id: str):
    payload = request.get_json(silent=True) or {}
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
    payload = request.get_json(silent=True) or {}
    return jsonify(SESSION_STORE.save_session(session_id, payload.get("label"))), 201


@app.post("/saves/<save_id>/load")
def load_save(save_id: str):
    session = SESSION_STORE.load_save(save_id)
    return jsonify(session.to_payload()), 201
