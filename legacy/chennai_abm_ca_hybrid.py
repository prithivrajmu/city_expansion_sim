# Hybrid CA + ABM Simulation Extension for Chennai Urban Growth
# Models developer, resident, and government behavior with geospatial influence

import numpy as np

# Define agent classes
class Resident:
    def __init__(self, id, preferences):
        self.id = id
        self.preferences = preferences  # e.g., {"proximity_to_jobs": 0.6, "flood_risk": 0.1, "cost": 0.3}

    def choose_location(self, urban_map, distance_to_econ, flood_risk, land_price):
        utility = (self.preferences["proximity_to_jobs"] * (1 / (distance_to_econ + 1)) +
                   self.preferences["flood_risk"] * (1 - flood_risk) -
                   self.preferences["cost"] * (land_price / np.max(land_price)))
        return np.unravel_index(np.argmax(utility), utility.shape)

class Developer:
    def __init__(self, budget):
        self.budget = budget

    def develop(self, land_price, existing_urban):
        developable = (existing_urban == 0) & (land_price < self.budget)
        score = (1 / (land_price + 1))
        return np.where(developable, score, 0)

class Government:
    def incentivize(self, infra_priority_map):
        return infra_priority_map * 0.1  # boost utility around planned infrastructure

# Example ABM step
residents = [Resident(id=i, preferences={"proximity_to_jobs": 0.5, "flood_risk": 0.2, "cost": 0.3}) for i in range(100)]
developer = Developer(budget=2000)
government = Government()

# Inputs from CA model or geospatial layers
urban_map = predictions["2040"]
price_map = land_price_2040
infra_priority_map = np.random.uniform(0, 1, urban_map.shape)  # placeholder

# Resident decisions
resident_locations = [r.choose_location(urban_map, distance_to_econ, flood_risk, price_map) for r in residents]

# Developer selects cells to develop
dev_score = developer.develop(price_map, urban_map)

# Government intervention
gov_boost = government.incentivize(infra_priority_map)

# Update urban map
urban_map_updated = urban_map + (dev_score > 0.1).astype(int) + (gov_boost > 0.05).astype(int)

# Final output update
predictions["2040"] = np.clip(urban_map_updated, 0, 1)

# Export hybrid results
import json
with open("output/abm_hybrid_2040.json", "w") as f:
    json.dump(predictions["2040"].tolist(), f)

print("Hybrid CA + ABM update complete.")
