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
CAMPAIGNS_DIR = ROOT_DIR / "simulation" / "campaigns"
SAVES_DIR = ROOT_DIR / "simulation" / "saves"


@dataclass
class SessionEnvelope:
    session_id: str
    scenario_id: str
    snapshot: object
    campaign: dict | None = None

    def to_payload(self) -> dict:
        return {
            "sessionId": self.session_id,
            "scenarioId": self.scenario_id,
            "snapshot": asdict(self.snapshot),
            "campaign": self.campaign,
        }


class SessionStore:
    def __init__(self, max_sessions: int = 12) -> None:
        self._sessions: OrderedDict[str, SimulationSession] = OrderedDict()
        self._max_sessions = max_sessions
        self._campaign_runs: OrderedDict[str, dict] = OrderedDict()
        self._session_campaigns: dict[str, str] = {}
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
        return self._session_envelope(session_id, session)

    def list_campaigns(self) -> list[dict]:
        items: list[dict] = []
        for path in sorted(CAMPAIGNS_DIR.glob("*.json")):
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            items.append(
                {
                    "id": data["id"],
                    "name": data["name"],
                    "description": data["description"],
                    "stageCount": len(data.get("stages", [])),
                    "stages": data.get("stages", []),
                }
            )
        return items

    def create_campaign_run(self, campaign_id: str) -> SessionEnvelope:
        campaign = self._campaign_definition(campaign_id)
        stages = campaign.get("stages", [])
        if not stages:
            raise ValueError(f"Campaign has no stages: {campaign_id}")

        stage = stages[0]
        session_id, session = self._create_runtime_session(stage["scenarioId"])
        run_id = str(uuid.uuid4())
        run = {
            "runId": run_id,
            "campaignId": campaign["id"],
            "campaignName": campaign["name"],
            "description": campaign["description"],
            "stageIndex": 0,
            "completedStages": [],
            "stageResults": [],
            "activeSessionId": session_id,
            "stages": stages,
        }
        self._campaign_runs[run_id] = run
        self._session_campaigns[session_id] = run_id
        return self._session_envelope(session_id, session)

    def get_campaign_run(self, run_id: str) -> dict:
        return self._campaign_payload(self._campaign_runs[run_id])

    def advance_campaign_run(self, run_id: str) -> SessionEnvelope:
        run = self._campaign_runs[run_id]
        session = self._get_session(run["activeSessionId"])
        report = session.report()
        evaluation = report["evaluation"]
        current_stage = run["stages"][run["stageIndex"]]

        if evaluation["tick"] < evaluation["horizonTicks"]:
            raise ValueError("Campaign stage can only advance after the evaluation horizon")
        if evaluation["status"] != "success":
            raise ValueError("Campaign stage must clear all objectives before advancing")

        run["completedStages"].append(current_stage["id"])
        run["stageResults"].append(
            {
                "stageId": current_stage["id"],
                "scenarioId": current_stage["scenarioId"],
                "headline": report["headline"],
                "status": evaluation["status"],
                "passedObjectives": evaluation["passedObjectives"],
                "totalObjectives": evaluation["totalObjectives"],
                "budget": report["resources"]["budget"],
                "politicalCapital": report["resources"]["politicalCapital"],
            }
        )

        next_stage_index = run["stageIndex"] + 1
        if next_stage_index >= len(run["stages"]):
            completed_session_id = run["activeSessionId"]
            run["activeSessionId"] = None
            return SessionEnvelope(
                session_id=completed_session_id or "",
                scenario_id=current_stage["scenarioId"],
                snapshot=session.snapshot(),
                campaign=self._campaign_payload(run),
            )

        next_stage = run["stages"][next_stage_index]
        carryover = self._carryover_resources(report)
        session_id, next_session = self._create_runtime_session(next_stage["scenarioId"], carryover)
        run["stageIndex"] = next_stage_index
        run["activeSessionId"] = session_id
        self._session_campaigns[session_id] = run_id
        return self._session_envelope(session_id, next_session)

    def get_session(self, session_id: str) -> SessionEnvelope:
        session = self._get_session(session_id)
        return self._session_envelope(session_id, session)

    def tick(self, session_id: str, steps: int) -> SessionEnvelope:
        session = self._get_session(session_id)
        for _ in range(steps):
            session.tick()
        return self._session_envelope(session_id, session)

    def apply_command(self, session_id: str, payload: dict) -> SessionEnvelope:
        session = self._get_session(session_id)
        session.apply_command(payload)
        return self._session_envelope(session_id, session)

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
        return self._session_envelope(session_id, session)

    def _create_runtime_session(
        self, scenario_id: str, resource_overrides: dict | None = None
    ) -> tuple[str, SimulationSession]:
        scenario_path = self._scenario_path(scenario_id)
        session_id = str(uuid.uuid4())
        session = create_session_from_scenario(scenario_path, resource_overrides=resource_overrides)
        self._ensure_capacity()
        self._sessions[session_id] = session
        return session_id, session

    def _session_envelope(self, session_id: str, session: SimulationSession) -> SessionEnvelope:
        campaign = None
        run_id = self._session_campaigns.get(session_id)
        if run_id and run_id in self._campaign_runs:
            campaign = self._campaign_payload(self._campaign_runs[run_id])
        return SessionEnvelope(
            session_id=session_id,
            scenario_id=session.scenario.id,
            snapshot=session.snapshot(),
            campaign=campaign,
        )

    def _get_session(self, session_id: str) -> SimulationSession:
        session = self._sessions[session_id]
        self._sessions.move_to_end(session_id)
        return session

    def _ensure_capacity(self) -> None:
        while len(self._sessions) >= self._max_sessions:
            evicted_session_id, _ = self._sessions.popitem(last=False)
            self._session_campaigns.pop(evicted_session_id, None)

    def _scenario_path(self, scenario_id: str) -> Path:
        safe_id = self._normalize_identifier(scenario_id)
        path = SCENARIOS_DIR / f"{safe_id}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Scenario not found: {safe_id}")
        return path

    def _campaign_definition(self, campaign_id: str) -> dict:
        safe_id = self._normalize_identifier(campaign_id)
        path = CAMPAIGNS_DIR / f"{safe_id}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Campaign not found: {safe_id}")
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _campaign_payload(self, run: dict) -> dict:
        current_stage = run["stages"][run["stageIndex"]] if run["stageIndex"] < len(run["stages"]) else None
        return {
            "runId": run["runId"],
            "campaignId": run["campaignId"],
            "campaignName": run["campaignName"],
            "description": run["description"],
            "stageIndex": run["stageIndex"],
            "stageCount": len(run["stages"]),
            "currentStage": current_stage,
            "completedStages": list(run["completedStages"]),
            "stageResults": list(run["stageResults"]),
            "isComplete": run["activeSessionId"] is None,
        }

    def _carryover_resources(self, report: dict) -> dict:
        evaluation = report["evaluation"]
        resources = report["resources"]
        objective_bonus = evaluation["passedObjectives"] * 16
        return {
            "budget": resources["startingBudget"] + max(0, resources["budget"] // 4) + objective_bonus,
            "politicalCapital": (
                resources["startingPoliticalCapital"]
                + max(0, resources["politicalCapital"] // 5)
                + (evaluation["passedObjectives"] * 6)
            ),
        }

    def _normalize_identifier(self, value: str) -> str:
        normalized = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value).strip("-")
        if not normalized:
            raise ValueError("Identifier must contain at least one alphanumeric character")
        return normalized


SESSION_STORE = SessionStore()
