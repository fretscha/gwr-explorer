const mapEl = document.getElementById("map");
// Locale-aware: the base URLs are rendered server-side via {% url %} so they
// carry the active language prefix (e.g. /fr/api/map/points/, /fr/gebaeude/0/).
const pointsUrl = mapEl.dataset.pointsUrl;
const buildingUrlTemplate = mapEl.dataset.buildingUrlTemplate;

function buildingUrl(egid) {
  return buildingUrlTemplate.replace(/0\/$/, `${egid}/`);
}

const map = L.map("map").setView([46.8, 8.2], 8);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap" }).addTo(map);
let layer = L.layerGroup().addTo(map);

async function refresh() {
  const b = map.getBounds();
  const q = new URLSearchParams({ south: b.getSouth(), west: b.getWest(), north: b.getNorth(), east: b.getEast() });
  const fc = await (await fetch(`${pointsUrl}?${q}`)).json();
  layer.clearLayers();
  fc.features.forEach((f) => {
    const [lon, lat] = f.geometry.coordinates;
    L.marker([lat, lon])
      .addTo(layer)
      .bindPopup(`<a href="${buildingUrl(f.properties.egid)}">EGID ${f.properties.egid}</a>`);
  });
}
map.on("moveend", refresh);
refresh();
