from __future__ import annotations

import json
import sys
import uuid
from collections import OrderedDict
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from simulation.core.engine import SimulationSession, create_session_from_scenario

SCENARIOS_DIR = ROOT_DIR / "simulation" / "scenarios"
SAVES_DIR = ROOT_DIR / "simulation" / "saves"


@dataclass
class SessionEnvelope:
    session_id: str
    scenario_id: str
    snapshot: object

    def to_payload(self) -> dict:
        return {
            "sessionId": self.session_id,
            "scenarioId": self.scenario_id,
            "snapshot": asdict(self.snapshot),
        }


class SessionStore:
    def __init__(self, max_sessions: int = 12) -> None:
        self._sessions: OrderedDict[str, SimulationSession] = OrderedDict()
        self._max_sessions = max_sessions
        SAVES_DIR.mkdir(parents=True, exist_ok=True)

    def list_scenarios(self) -> list[dict]:
        items: list[dict] = []
        for path in sorted(SCENARIOS_DIR.glob("*.json")):
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            items.append(
                {
                    "id": data["id"],
                    "name": data["name"],
                    "description": data["description"],
                    "ticksPerYear": data["ticksPerYear"],
                    "focus": data["focus"],
                }
            )
        return items

    def create_session(self, scenario_id: str) -> SessionEnvelope:
        scenario_path = self._scenario_path(scenario_id)
        session_id = str(uuid.uuid4())
        session = create_session_from_scenario(scenario_path)
        self._ensure_capacity()
        self._sessions[session_id] = session
        return SessionEnvelope(session_id=session_id, scenario_id=scenario_id, snapshot=session.snapshot())

    def get_session(self, session_id: str) -> SessionEnvelope:
        session = self._get_session(session_id)
        return SessionEnvelope(session_id=session_id, scenario_id=session.scenario.id, snapshot=session.snapshot())

    def tick(self, session_id: str, steps: int) -> SessionEnvelope:
        session = self._get_session(session_id)
        for _ in range(steps):
            session.tick()
        return SessionEnvelope(session_id=session_id, scenario_id=session.scenario.id, snapshot=session.snapshot())

    def apply_command(self, session_id: str, payload: dict) -> SessionEnvelope:
        session = self._get_session(session_id)
        session.apply_command(payload)
        return SessionEnvelope(session_id=session_id, scenario_id=session.scenario.id, snapshot=session.snapshot())

    def report(self, session_id: str) -> dict:
        session = self._get_session(session_id)
        return session.report()

    def timeline(self, session_id: str) -> list[dict]:
        session = self._get_session(session_id)
        return [asdict(entry) for entry in session.timeline()]

    def replay(self, session_id: str, tick: int) -> dict:
        session = self._get_session(session_id)
        replay = session.replay(tick)
        replay["grid"] = [asdict(cell) for cell in replay["grid"]]
        return replay

    def save_session(self, session_id: str, label: str | None = None) -> dict:
        session = self._get_session(session_id)
        save_id = label or f"{session.scenario.id}-tick-{session.tick_count}"
        safe_id = self._normalize_identifier(save_id)
        path = SAVES_DIR / f"{safe_id}.json"
        payload = {
            "saveId": safe_id,
            "scenarioId": session.scenario.id,
            "sessionId": session_id,
            "state": session.export_state(),
        }
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return {"saveId": safe_id, "tick": session.tick_count, "scenarioId": session.scenario.id}

    def list_saves(self) -> list[dict]:
        items: list[dict] = []
        for path in sorted(SAVES_DIR.glob("*.json")):
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            items.append(
                {
                    "saveId": payload["saveId"],
                    "scenarioId": payload["scenarioId"],
                    "tick": payload["state"]["tickCount"],
                }
            )
        return items

    def load_save(self, save_id: str) -> SessionEnvelope:
        safe_id = self._normalize_identifier(save_id)
        path = SAVES_DIR / f"{safe_id}.json"
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        session_id = str(uuid.uuid4())
        session = SimulationSession.from_state(payload["state"])
        self._ensure_capacity()
        self._sessions[session_id] = session
        return SessionEnvelope(session_id=session_id, scenario_id=session.scenario.id, snapshot=session.snapshot())

    def _get_session(self, session_id: str) -> SimulationSession:
        session = self._sessions[session_id]
        self._sessions.move_to_end(session_id)
        return session

    def _ensure_capacity(self) -> None:
        while len(self._sessions) >= self._max_sessions:
            self._sessions.popitem(last=False)

    def _scenario_path(self, scenario_id: str) -> Path:
        safe_id = self._normalize_identifier(scenario_id)
        path = SCENARIOS_DIR / f"{safe_id}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Scenario not found: {safe_id}")
        return path

    def _normalize_identifier(self, value: str) -> str:
        normalized = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value).strip("-")
        if not normalized:
            raise ValueError("Identifier must contain at least one alphanumeric character")
        return normalized


SESSION_STORE = SessionStore()
