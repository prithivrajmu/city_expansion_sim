// React + Leaflet Urban Expansion Simulator
// Displays predicted urban growth, land price, and population maps

import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, ImageOverlay } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { Slider } from "@/components/ui/slider";

const yearOptions = [2020, 2030, 2040];

export default function UrbanSim() {
  const [year, setYear] = useState(2040);
  const [urbanData, setUrbanData] = useState(null);
  const [landPrice, setLandPrice] = useState(null);
  const [popDensity, setPopDensity] = useState(null);

  useEffect(() => {
    fetch(`/output/urban_predictions.json`)
      .then(res => res.json())
      .then(data => setUrbanData(data[year]))
      .catch(console.error);

    fetch(`/output/land_price_2040.npy`)
      .then(res => res.arrayBuffer())
      .then(buf => setLandPrice(new Float32Array(buf)))
      .catch(console.error);

    fetch(`/output/pop_density_2040.npy`)
      .then(res => res.arrayBuffer())
      .then(buf => setPopDensity(new Float32Array(buf)))
      .catch(console.error);
  }, [year]);

  return (
    <div className="w-full h-screen flex flex-col">
      <h1 className="text-xl font-bold p-4">Chennai Urban Expansion Simulator</h1>

      <Slider
        min={2020}
        max={2040}
        step={10}
        value={[year]}
        onValueChange={([val]) => setYear(val)}
        className="px-6"
      />

      <MapContainer center={[13.08, 80.27]} zoom={10} className="flex-1">
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        {urbanData && (
          <ImageOverlay
            url={`/tiles/urban_${year}.png`}
            bounds={[[12.8, 79.8], [13.5, 80.5]]} // Adjust as per georeferencing
            opacity={0.6}
          />
        )}
      </MapContainer>
    </div>
  );
}
