const map = L.map("map").setView([46.8, 8.2], 8);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap" }).addTo(map);
let layer = L.layerGroup().addTo(map);

async function refresh() {
  const b = map.getBounds();
  const q = new URLSearchParams({ south: b.getSouth(), west: b.getWest(), north: b.getNorth(), east: b.getEast() });
  const fc = await (await fetch(`/api/map/points/?${q}`)).json();
  layer.clearLayers();
  fc.features.forEach((f) => {
    const [lon, lat] = f.geometry.coordinates;
    L.marker([lat, lon])
      .addTo(layer)
      .bindPopup(`<a href="/gebaeude/${f.properties.egid}/">EGID ${f.properties.egid}</a>`);
  });
}
map.on("moveend", refresh);
refresh();
