// Extended React + Leaflet Urban Expansion UI with Layer Controls and Analytics

import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, ImageOverlay } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";

const yearOptions = [2020, 2030, 2040];

export default function UrbanSim() {
  const [year, setYear] = useState(2040);
  const [urbanData, setUrbanData] = useState(null);
  const [showUrban, setShowUrban] = useState(true);
  const [showPrice, setShowPrice] = useState(false);
  const [showPopulation, setShowPopulation] = useState(false);

  const imageBounds = [[12.8, 79.8], [13.5, 80.5]]; // Adjust based on Chennai bounds

  useEffect(() => {
    fetch(`/output/urban_predictions.json`)
      .then(res => res.json())
      .then(data => setUrbanData(data[year]))
      .catch(console.error);
  }, [year]);

  return (
    <div className="w-full h-screen flex flex-col">
      <h1 className="text-xl font-bold p-4">Chennai Urban Expansion Simulator</h1>

      <div className="flex flex-row gap-4 items-center px-6">
        <Slider
          min={2020}
          max={2040}
          step={10}
          value={[year]}
          onValueChange={([val]) => setYear(val)}
          className="w-1/2"
        />

        <div className="flex items-center gap-2">
          <Checkbox checked={showUrban} onCheckedChange={setShowUrban} /> Urban
          <Checkbox checked={showPrice} onCheckedChange={setShowPrice} /> Land Price
          <Checkbox checked={showPopulation} onCheckedChange={setShowPopulation} /> Population
        </div>
      </div>

      <div className="flex flex-row flex-1">
        <MapContainer center={[13.08, 80.27]} zoom={10} className="flex-1 z-0">
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

          {showUrban && (
            <ImageOverlay
              url={`/tiles/urban_${year}.png`}
              bounds={imageBounds}
              opacity={0.6}
            />
          )}

          {showPrice && year === 2040 && (
            <ImageOverlay
              url={`/output/land_price_2040.npy`}
              bounds={imageBounds}
              opacity={0.5}
            />
          )}

          {showPopulation && year === 2040 && (
            <ImageOverlay
              url={`/output/pop_density_2040.npy`}
              bounds={imageBounds}
              opacity={0.4}
            />
          )}
        </MapContainer>

        <div className="w-1/4 bg-white p-4 shadow-md">
          <Card>
            <CardContent>
              <p className="font-semibold">Year: {year}</p>
              <p>Total Urbanized Area: {urbanData ? urbanData.flat().filter(v => v > 0).length : 0}</p>
              <p>Price Layer: {showPrice ? "Visible" : "Hidden"}</p>
              <p>Population Layer: {showPopulation ? "Visible" : "Hidden"}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
