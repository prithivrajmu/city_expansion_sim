from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_DISTRICT_STRATEGY = {
    "mode": "balanced",
    "growth_signal_bias": 0.0,
    "conversion_threshold_delta": 0.0,
    "access_drift": 0.0,
    "land_value_multiplier": 1.0,
    "population_multiplier": 1.0,
    "risk_drift": 0.0,
    "risk_weight": 1.0,
}

DISTRICT_STRATEGY_PRESETS = {
    "balanced": DEFAULT_DISTRICT_STRATEGY,
    "growth_first": {
        "mode": "growth_first",
        "growth_signal_bias": 0.16,
        "conversion_threshold_delta": -0.08,
        "access_drift": 0.035,
        "land_value_multiplier": 1.35,
        "population_multiplier": 1.12,
        "risk_drift": 0.012,
        "risk_weight": 0.9,
    },
    "resilience_first": {
        "mode": "resilience_first",
        "growth_signal_bias": -0.08,
        "conversion_threshold_delta": 0.05,
        "access_drift": 0.015,
        "land_value_multiplier": 0.9,
        "population_multiplier": 0.94,
        "risk_drift": -0.03,
        "risk_weight": 1.15,
    },
}

COMMAND_COST_FACTORS = {
    "build_transit": {"budget": 24, "politicalCapital": 8, "strengthBudget": 180, "strengthPoliticalCapital": 60},
    "upzone_district": {"budget": 14, "politicalCapital": 11, "strengthBudget": 120, "strengthPoliticalCapital": 90},
    "flood_barrier": {"budget": 18, "politicalCapital": 9, "strengthBudget": 160, "strengthPoliticalCapital": 70},
}


@dataclass
class CellSnapshot:
    index: int
    district: str
    kind: str
    urbanized: bool
    population: int
    land_value: int
    risk: float
    access: float


@dataclass
class SimulationSnapshot:
    tick: int
    year: int
    title: str
    summary: str
    metrics: dict
    grid: list[CellSnapshot]
    events: list[str]
    interventions: list[dict]
    districts: list[str]


@dataclass
class Scenario:
    id: str
    name: str
    description: str
    focus: str
    baseYear: int
    ticksPerYear: int
    gridWidth: int
    gridHeight: int
    policyBoost: float
    residentDemand: float
    developerPressure: float
    infrastructureMomentum: float
    initialBudget: int
    initialPoliticalCapital: int
    agentProfiles: dict
    events: list[dict]
    cells: list[dict]
    districtStrategies: dict[str, dict] | None = None


@dataclass
class TimelineEntry:
    tick: int
    year: int
    urbanCells: int
    population: int
    averageLandValue: int
    interventionCount: int


class SimulationSession:
    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.tick_count = 0
        self.cells = [cell.copy() for cell in scenario.cells]
        self.interventions: list[dict] = []
        self.budget = scenario.initialBudget
        self.political_capital = scenario.initialPoliticalCapital
        self.events: list[str] = [
            f"Scenario '{scenario.name}' initialized with {len(self.cells)} cells."
        ]
        self.applied_events: list[dict] = []
        self.history: list[dict] = []
        self._record_history()

    def tick(self) -> None:
        width = self.scenario.gridWidth
        resident_pressure = self._resident_pressure()
        developer_pressure = self._developer_pressure()
        government_pressure = self._government_pressure()
        self._apply_scheduled_events()
        next_cells: list[dict] = []
        conversions = 0

        for index, cell in enumerate(self.cells):
            strategy = self._district_strategy(cell["district"])
            urban_neighbors = self._urban_neighbor_ratio(index, width)
            growth_signal = (
                urban_neighbors * 0.8
                + cell["access"] * self.scenario.infrastructureMomentum
                + resident_pressure * 0.4
                + developer_pressure * 0.35
                + government_pressure * 0.2
                + strategy["growth_signal_bias"]
                - cell["risk"] * 0.55 * strategy["risk_weight"]
            )
            threshold = 1.2 - self.scenario.policyBoost + strategy["conversion_threshold_delta"]

            next_cell = cell.copy()
            if cell["kind"] != "water":
                next_cell["access"] = self._clamp(cell["access"] + strategy["access_drift"])
                next_cell["risk"] = self._clamp(cell["risk"] + strategy["risk_drift"])
            if not cell["urbanized"] and cell["kind"] != "water" and growth_signal >= threshold:
                next_cell["urbanized"] = True
                next_cell["kind"] = "urban"
                next_cell["population"] += self._scaled_value(120, strategy["population_multiplier"])
                next_cell["landValue"] += self._scaled_value(80, strategy["land_value_multiplier"])
                conversions += 1
            elif cell["urbanized"]:
                next_cell["population"] += self._scaled_value(
                    18 + (next_cell["access"] * 12) - (next_cell["risk"] * 6),
                    strategy["population_multiplier"],
                )
                next_cell["landValue"] += self._scaled_value(
                    12 + (urban_neighbors * 10),
                    strategy["land_value_multiplier"],
                )
            else:
                next_cell["landValue"] += self._scaled_value(
                    2 + (next_cell["access"] * 4) - (next_cell["risk"] * 2),
                    strategy["land_value_multiplier"],
                )

            next_cells.append(next_cell)

        self.cells = next_cells
        self.tick_count += 1
        self._replenish_resources()
        year = self._current_year()
        self.events.append(
            f"Tick {self.tick_count}: {conversions} cells urbanized, corridor pressure at year {year}."
        )
        self.events = self.events[-10:]
        self._record_history()

    def apply_command(self, command: dict) -> None:
        command_type = command.get("type")
        district = command.get("district")
        strength = float(command.get("strength", 0.08))

        if command_type not in {"upzone_district", "build_transit", "flood_barrier"}:
            raise ValueError(f"Unsupported command type: {command_type}")

        touched = 0
        for cell in self.cells:
            if district and cell["district"] != district:
                continue
            if cell["kind"] == "water":
                continue
            touched += 1

        if touched == 0:
            raise ValueError("Command requires at least one non-water cell in the selected district")

        cost = self.command_cost(command_type, touched, strength)
        if self.budget < cost["budget"]:
            raise ValueError(
                f"Insufficient budget for {command_type}: need {cost['budget']}, have {self.budget}"
            )
        if self.political_capital < cost["politicalCapital"]:
            raise ValueError(
                "Insufficient political capital for "
                f"{command_type}: need {cost['politicalCapital']}, have {self.political_capital}"
            )

        self.budget -= cost["budget"]
        self.political_capital -= cost["politicalCapital"]

        touched = 0
        for cell in self.cells:
            if district and cell["district"] != district:
                continue
            if cell["kind"] == "water":
                continue

            if command_type == "upzone_district":
                cell["landValue"] += int(16 + (strength * 40))
                cell["population"] += int(10 + (strength * 28))
                cell["access"] = min(1.0, cell["access"] + strength * 0.2)
            elif command_type == "build_transit":
                cell["access"] = min(1.0, cell["access"] + strength)
                cell["landValue"] += int(14 + (strength * 30))
            elif command_type == "flood_barrier":
                cell["risk"] = max(0.0, cell["risk"] - strength)
                cell["landValue"] += int(8 + (strength * 20))
            touched += 1

        applied = {
            "type": command_type,
            "district": district or "all",
            "strength": round(strength, 2),
            "tick": self.tick_count,
            "touched": touched,
            "cost": cost,
        }
        self.interventions.append(applied)
        self.interventions = self.interventions[-12:]
        self.events.append(
            f"Command applied: {command_type} in {applied['district']} touching {touched} cells "
            f"for budget {cost['budget']} and political capital {cost['politicalCapital']}."
        )
        self.events = self.events[-10:]
        self._record_history()

    def snapshot(self) -> SimulationSnapshot:
        metrics = self._metrics()
        return SimulationSnapshot(
            tick=self.tick_count,
            year=self._current_year(),
            title=self.scenario.name,
            summary=(
                "A deterministic city-growth slice with residents, developers, policy boost, "
                "infrastructure access, and flood-risk pressure."
            ),
            metrics=metrics,
            grid=[
                CellSnapshot(
                    index=index,
                    district=cell["district"],
                    kind=cell["kind"],
                    urbanized=cell["urbanized"],
                    population=cell["population"],
                    land_value=cell["landValue"],
                    risk=cell["risk"],
                    access=cell["access"],
                )
                for index, cell in enumerate(self.cells)
            ],
            events=list(self.events),
            interventions=list(self.interventions),
            districts=self.districts(),
        )

    def _metrics(self) -> dict:
        urban_cells = sum(1 for cell in self.cells if cell["urbanized"])
        population = sum(cell["population"] for cell in self.cells)
        average_land_value = sum(cell["landValue"] for cell in self.cells) // len(self.cells)
        average_risk = round(sum(cell["risk"] for cell in self.cells) / len(self.cells), 3)
        average_access = round(sum(cell["access"] for cell in self.cells) / len(self.cells), 3)
        return {
            "urbanCells": urban_cells,
            "population": population,
            "averageLandValue": average_land_value,
            "urbanizationRate": round(urban_cells / len(self.cells), 3),
            "averageRisk": average_risk,
            "averageAccess": average_access,
            "interventionCount": len(self.interventions),
            "residentPressure": self._resident_pressure(),
            "developerPressure": self._developer_pressure(),
            "governmentPressure": self._government_pressure(),
            "eventCount": len(self.applied_events),
            "budget": self.budget,
            "politicalCapital": self.political_capital,
        }

    def districts(self) -> list[str]:
        return sorted({cell["district"] for cell in self.cells if cell["kind"] != "water"})

    def _urban_neighbor_ratio(self, index: int, width: int) -> float:
        neighbors = self._neighbor_indices(index, width, len(self.cells))
        if not neighbors:
            return 0.0
        urban_neighbors = sum(1 for neighbor in neighbors if self.cells[neighbor]["urbanized"])
        return urban_neighbors / len(neighbors)

    def _neighbor_indices(self, index: int, width: int, total: int) -> list[int]:
        row = index // width
        col = index % width
        neighbors: list[int] = []
        for d_row in (-1, 0, 1):
            for d_col in (-1, 0, 1):
                if d_row == 0 and d_col == 0:
                    continue
                next_row = row + d_row
                next_col = col + d_col
                if next_row < 0 or next_col < 0:
                    continue
                next_index = next_row * width + next_col
                if next_col >= width or next_index >= total:
                    continue
                neighbors.append(next_index)
        return neighbors

    def _current_year(self) -> int:
        return self.scenario.baseYear + (self.tick_count // self.scenario.ticksPerYear)

    def _resident_pressure(self) -> float:
        profile = self.scenario.agentProfiles.get("residents", {})
        return round(self.scenario.residentDemand * profile.get("mobility", 1.0) * profile.get("housingUrgency", 1.0), 3)

    def _developer_pressure(self) -> float:
        profile = self.scenario.agentProfiles.get("developers", {})
        return round(self.scenario.developerPressure * profile.get("capitalAggression", 1.0) * profile.get("speculation", 1.0), 3)

    def _government_pressure(self) -> float:
        profile = self.scenario.agentProfiles.get("government", {})
        return round(self.scenario.policyBoost * profile.get("deliveryBias", 1.0) * profile.get("coordination", 1.0), 3)

    def _district_strategy(self, district: str) -> dict:
        definition = (self.scenario.districtStrategies or {}).get(district, {})
        mode = definition.get("mode", "balanced")
        preset = DISTRICT_STRATEGY_PRESETS.get(mode, DEFAULT_DISTRICT_STRATEGY)
        strategy = preset.copy()
        for key in DEFAULT_DISTRICT_STRATEGY:
            if key == "mode":
                continue
            if key in definition:
                strategy[key] = definition[key]
        return strategy

    def _clamp(self, value: float) -> float:
        return min(1.0, max(0.0, round(value, 3)))

    def _scaled_value(self, base: float, multiplier: float) -> int:
        return int(round(base * multiplier))

    def command_cost(self, command_type: str, touched: int, strength: float) -> dict[str, int]:
        factors = COMMAND_COST_FACTORS[command_type]
        return {
            "budget": int(round((factors["budget"] * touched) + (strength * factors["strengthBudget"]))),
            "politicalCapital": int(
                round((factors["politicalCapital"] * touched) + (strength * factors["strengthPoliticalCapital"]))
            ),
        }

    def _replenish_resources(self) -> None:
        government = self.scenario.agentProfiles.get("government", {})
        budget_gain = max(6, int(round(16 * self._government_pressure())))
        political_gain = max(3, int(round(8 * government.get("coordination", 1.0))))
        self.budget += budget_gain
        self.political_capital += political_gain

    def _apply_scheduled_events(self) -> None:
        next_tick = self.tick_count + 1
        due_events = [event for event in self.scenario.events if event["tick"] == next_tick]
        for event in due_events:
            self._apply_event(event)

    def _apply_event(self, event: dict) -> None:
        district = event.get("district")
        impact = event.get("impact", {})
        touched = 0
        for cell in self.cells:
            if district and cell["district"] != district:
                continue
            if cell["kind"] == "water":
                continue
            cell["access"] = min(1.0, max(0.0, cell["access"] + impact.get("access", 0.0)))
            cell["risk"] = min(1.0, max(0.0, cell["risk"] + impact.get("risk", 0.0)))
            cell["landValue"] += int(impact.get("landValue", 0))
            cell["population"] += int(impact.get("population", 0))
            touched += 1
        record = {
            "tick": event["tick"],
            "title": event["title"],
            "district": district or "all",
            "touched": touched,
        }
        self.applied_events.append(record)
        self.applied_events = self.applied_events[-12:]
        self.events.append(f"Scenario event: {event['title']} affected {record['district']} ({touched} cells).")
        self.events = self.events[-10:]

    def _record_history(self) -> None:
        metrics = self._metrics()
        entry = {
            "tick": self.tick_count,
            "year": self._current_year(),
            "metrics": metrics,
            "cells": [cell.copy() for cell in self.cells],
            "events": list(self.events),
            "interventions": list(self.interventions),
            "scenarioEvents": list(self.applied_events),
            "resources": {"budget": self.budget, "politicalCapital": self.political_capital},
        }
        if self.history and self.history[-1]["tick"] == self.tick_count:
            self.history[-1] = entry
        else:
            self.history.append(entry)
        self.history = self.history[-64:]

    def timeline(self) -> list[TimelineEntry]:
        return [
            TimelineEntry(
                tick=entry["tick"],
                year=entry["year"],
                urbanCells=entry["metrics"]["urbanCells"],
                population=entry["metrics"]["population"],
                averageLandValue=entry["metrics"]["averageLandValue"],
                interventionCount=entry["metrics"]["interventionCount"],
            )
            for entry in self.history
        ]

    def replay(self, tick: int) -> dict:
        if tick < 0:
            raise ValueError("Tick must be non-negative")
        for entry in self.history:
            if entry["tick"] == tick:
                return {
                    "tick": entry["tick"],
                    "year": entry["year"],
                    "metrics": entry["metrics"],
                    "grid": [
                        CellSnapshot(
                            index=index,
                            district=cell["district"],
                            kind=cell["kind"],
                            urbanized=cell["urbanized"],
                            population=cell["population"],
                            land_value=cell["landValue"],
                            risk=cell["risk"],
                            access=cell["access"],
                        )
                        for index, cell in enumerate(entry["cells"])
                    ],
                    "events": entry["events"],
                    "interventions": entry["interventions"],
                    "scenarioEvents": entry.get("scenarioEvents", []),
                }
        raise ValueError(f"Replay tick not found: {tick}")

    def export_state(self) -> dict:
        return {
            "scenario": asdict(self.scenario),
            "tickCount": self.tick_count,
            "cells": [cell.copy() for cell in self.cells],
            "interventions": list(self.interventions),
            "appliedEvents": list(self.applied_events),
            "events": list(self.events),
            "history": self.history,
            "resources": {"budget": self.budget, "politicalCapital": self.political_capital},
        }

    @classmethod
    def from_state(cls, state: dict) -> "SimulationSession":
        scenario = Scenario(**state["scenario"])
        session = cls(scenario=scenario)
        session.tick_count = state["tickCount"]
        session.cells = [cell.copy() for cell in state["cells"]]
        session.interventions = list(state["interventions"])
        session.applied_events = list(state.get("appliedEvents", []))
        session.events = list(state["events"])
        resources = state.get("resources", {})
        session.budget = resources.get("budget", scenario.initialBudget)
        session.political_capital = resources.get(
            "politicalCapital", scenario.initialPoliticalCapital
        )
        session.history = list(state.get("history", [])) or []
        if not session.history:
            session._record_history()
        return session

    def report(self) -> dict:
        metrics = self._metrics()
        baseline_entry = self.history[0] if self.history else None
        fastest_growth = sorted(
            self.cells,
            key=lambda cell: (cell["urbanized"], cell["access"], cell["landValue"]),
            reverse=True,
        )[:3]
        risk_zones = sorted(self.cells, key=lambda cell: cell["risk"], reverse=True)[:3]
        comparison = self._comparison_metrics(baseline_entry)
        return {
            "headline": (
                f"{self.scenario.name} at year {self._current_year()} has "
                f"{metrics['urbanCells']} urban cells and population {metrics['population']}."
            ),
            "summary": [
                f"Urbanization rate is {metrics['urbanizationRate']} with average land value {metrics['averageLandValue']}.",
                f"Average infrastructure access is {metrics['averageAccess']} and average risk is {metrics['averageRisk']}.",
                f"{metrics['interventionCount']} interventions have been applied in this session.",
                f"Resident pressure is {metrics['residentPressure']}, developer pressure is {metrics['developerPressure']}, and government pressure is {metrics['governmentPressure']}.",
                f"Compared with baseline, population changed by {comparison['populationDelta']} and average land value changed by {comparison['averageLandValueDelta']}.",
                f"Remaining budget is {metrics['budget']} and political capital is {metrics['politicalCapital']}.",
            ],
            "growthFrontier": [
                {
                    "district": cell["district"],
                    "population": cell["population"],
                    "landValue": cell["landValue"],
                    "access": cell["access"],
                }
                for cell in fastest_growth
            ],
            "riskWatch": [
                {
                    "district": cell["district"],
                    "risk": cell["risk"],
                    "landValue": cell["landValue"],
                }
                for cell in risk_zones
            ],
            "interventions": list(self.interventions),
            "scenarioEvents": list(self.applied_events),
            "recentEvents": list(self.events[-5:]),
            "timeline": [asdict(entry) for entry in self.timeline()],
            "agentSummary": self.scenario.agentProfiles,
            "comparison": comparison,
            "districtComparison": self._district_comparison(baseline_entry),
            "interventionROI": self._intervention_roi(),
            "resources": {
                "budget": self.budget,
                "politicalCapital": self.political_capital,
                "startingBudget": self.scenario.initialBudget,
                "startingPoliticalCapital": self.scenario.initialPoliticalCapital,
            },
        }

    def _comparison_metrics(self, baseline_entry: dict | None) -> dict:
        current = self._metrics()
        if not baseline_entry:
            return {
                "baselineTick": 0,
                "currentTick": self.tick_count,
                "populationDelta": 0,
                "urbanCellsDelta": 0,
                "averageLandValueDelta": 0,
                "averageRiskDelta": 0.0,
                "averageAccessDelta": 0.0,
            }

        baseline_metrics = baseline_entry["metrics"]
        return {
            "baselineTick": baseline_entry["tick"],
            "currentTick": self.tick_count,
            "populationDelta": current["population"] - baseline_metrics["population"],
            "urbanCellsDelta": current["urbanCells"] - baseline_metrics["urbanCells"],
            "averageLandValueDelta": current["averageLandValue"] - baseline_metrics["averageLandValue"],
            "averageRiskDelta": round(current["averageRisk"] - baseline_metrics["averageRisk"], 3),
            "averageAccessDelta": round(current["averageAccess"] - baseline_metrics["averageAccess"], 3),
        }

    def _district_comparison(self, baseline_entry: dict | None) -> list[dict]:
        current_by_district = self._district_metrics(self.cells)
        baseline_by_district = self._district_metrics(baseline_entry["cells"]) if baseline_entry else {}
        items: list[dict] = []
        for district in sorted(current_by_district):
            current = current_by_district[district]
            baseline = baseline_by_district.get(
                district,
                {
                    "population": 0,
                    "landValue": 0,
                    "risk": 0.0,
                    "access": 0.0,
                    "urbanCells": 0,
                },
            )
            items.append(
                {
                    "district": district,
                    "populationDelta": current["population"] - baseline["population"],
                    "landValueDelta": current["landValue"] - baseline["landValue"],
                    "riskDelta": round(current["risk"] - baseline["risk"], 3),
                    "accessDelta": round(current["access"] - baseline["access"], 3),
                    "urbanCellsDelta": current["urbanCells"] - baseline["urbanCells"],
                }
            )
        return items

    def _district_metrics(self, cells: list[dict]) -> dict[str, dict]:
        district_data: dict[str, dict] = {}
        district_counts: dict[str, int] = {}
        for cell in cells:
            if cell["kind"] == "water":
                continue
            district = cell["district"]
            district_data.setdefault(
                district,
                {"population": 0, "landValue": 0, "risk": 0.0, "access": 0.0, "urbanCells": 0},
            )
            district_counts[district] = district_counts.get(district, 0) + 1
            district_data[district]["population"] += cell["population"]
            district_data[district]["landValue"] += cell["landValue"]
            district_data[district]["risk"] += cell["risk"]
            district_data[district]["access"] += cell["access"]
            district_data[district]["urbanCells"] += 1 if cell["urbanized"] else 0

        for district, totals in district_data.items():
            count = max(1, district_counts[district])
            totals["risk"] = round(totals["risk"] / count, 3)
            totals["access"] = round(totals["access"] / count, 3)
        return district_data

    def _intervention_roi(self) -> list[dict]:
        items: list[dict] = []
        for intervention in self.interventions:
            before_entry = self._history_entry(intervention["tick"])
            district = intervention["district"]
            current_metrics = self._district_metrics(self.cells)
            before_metrics = self._district_metrics(before_entry["cells"]) if before_entry else {}
            current = current_metrics.get(district)
            previous = before_metrics.get(
                district,
                {"population": 0, "landValue": 0, "risk": 0.0, "access": 0.0, "urbanCells": 0},
            )
            if not current:
                continue
            denominator = max(1.0, intervention["strength"] * max(1, intervention["touched"]) * 100)
            value_gain = current["landValue"] - previous["landValue"]
            population_gain = current["population"] - previous["population"]
            risk_delta = round(current["risk"] - previous["risk"], 3)
            items.append(
                {
                    "type": intervention["type"],
                    "district": district,
                    "tick": intervention["tick"],
                    "valueGain": value_gain,
                    "populationGain": population_gain,
                    "riskDelta": risk_delta,
                    "efficiency": round(value_gain / denominator, 3),
                }
            )
        return items

    def _history_entry(self, tick: int) -> dict | None:
        for entry in self.history:
            if entry["tick"] == tick:
                return entry
        return None


def create_session_from_scenario(path: Path) -> SimulationSession:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    scenario = Scenario(**data)
    return SimulationSession(scenario=scenario)
