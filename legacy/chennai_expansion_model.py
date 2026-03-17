# Chennai Urban Expansion Simulation (2030–2040)
# Core Model Logic with Economic and Population Prediction

import numpy as np
import geopandas as gpd
import rasterio
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import json
import os

# Load Input Layers
land_use_2020 = rasterio.open("data/chennai_landuse_2020.tif")
land_array = land_use_2020.read(1)

distance_to_roads = rasterio.open("data/dist_to_roads.tif").read(1)
distance_to_econ = rasterio.open("data/dist_to_econ.tif").read(1)
flood_risk = rasterio.open("data/flood_risk.tif").read(1)

# Stack Features
X = np.stack([
    land_array.flatten(),
    distance_to_roads.flatten(),
    distance_to_econ.flatten(),
    flood_risk.flatten()
], axis=1)

# Labels for 2030
labels = rasterio.open("data/chennai_landuse_2030_truth.tif").read(1).flatten()
valid_mask = ~np.isnan(X).any(axis=1) & (labels >= 0)
X_valid = X[valid_mask]
y_valid = labels[valid_mask]

# Train Classifier
X_train, X_test, y_train, y_test = train_test_split(X_valid, y_valid, test_size=0.2, random_state=42)
clf = RandomForestClassifier(n_estimators=100, random_state=0)
clf.fit(X_train, y_train)
print("Accuracy:", accuracy_score(y_test, clf.predict(X_test)))

# Predict Urban Expansion
predictions = {}
for year in [2030, 2040]:
    urban_flat = clf.predict(X)
    urban_map = np.zeros_like(land_array)
    urban_map.flat = urban_flat
    predictions[str(year)] = urban_map

# Land Price Prediction
base_price = 1000
def predict_price(urban, roads, econ):
    return base_price * (1 + 0.5 * urban + 0.3 / (roads + 1) + 0.2 / (econ + 1))

land_price_2040 = predict_price(predictions["2040"], distance_to_roads, distance_to_econ)

# Population Distribution
population_density = predictions["2040"] * np.random.uniform(200, 400, land_array.shape)

# Save for Web
os.makedirs("output", exist_ok=True)
with open("output/urban_predictions.json", "w") as f:
    json.dump({k: v.tolist() for k, v in predictions.items()}, f)
np.save("output/land_price_2040.npy", land_price_2040)
np.save("output/pop_density_2040.npy", population_density)

# Quick Visualization
plt.subplot(1, 2, 1)
plt.imshow(predictions["2040"], cmap='viridis')
plt.title("Urban Map 2040")
plt.subplot(1, 2, 2)
plt.imshow(land_price_2040, cmap='hot')
plt.title("Land Price 2040")
plt.show()
