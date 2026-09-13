const mapEl = document.getElementById("map");
// Locale-aware: the base URLs are rendered server-side via {% url %} so they
// carry the active language prefix (e.g. /fr/api/map/points/, /fr/gebaeude/0/).
const pointsUrl = mapEl.dataset.pointsUrl;
const buildingUrlTemplate = mapEl.dataset.buildingUrlTemplate;
// Heating-group display labels are rendered server-side with {% trans %}, so the
// legend and popups follow the active language without shipping a translation
// table to the client.
const heatingLabels = JSON.parse(mapEl.dataset.heatingLabels);
const surfaceLabel = mapEl.dataset.surfaceLabel;

const hintEl = document.getElementById("map-hint");
const legendEl = document.getElementById("map-legend");
const limitEl = document.getElementById("map-limit");
// Hint text carries an {n} placeholder so the message can name the active
// threshold (e.g. "…250 oder mehr…") in the current language.
const hintTemplate = mapEl.dataset.hintTemplate;

// Max objects to show before the map hides everything and asks the user to zoom
// in. Bound to the <select>; falls back to 250 if the control is absent.
function currentLimit() {
  return (limitEl && parseInt(limitEl.value, 10)) || 250;
}

function buildingUrl(egid) {
  return buildingUrlTemplate.replace(/0\/$/, `${egid}/`);
}

// GENH1 heating-source codes → semantic group. Group order is fixed so a group's
// colour never depends on which groups happen to be in view (colour follows the
// entity, not its rank).
const HEATING_GROUPS = [
  { key: "heat_pump", color: "#1baf7a", codes: [7501, 7510, 7511, 7512, 7513] },
  { key: "gas", color: "#eb6834", codes: [7520] },
  { key: "oil", color: "#e34948", codes: [7530] },
  { key: "wood", color: "#008300", codes: [7540, 7541, 7542, 7543] },
  { key: "waste_heat", color: "#4a3aa7", codes: [7550] },
  { key: "electric", color: "#e87ba4", codes: [7560] },
  { key: "solar", color: "#eda100", codes: [7570] },
  { key: "district", color: "#2a78d6", codes: [7580, 7581, 7582] },
  // Keine (7500), Unbestimmt (7598), Andere (7599), missing → neutral grey.
  { key: "none_other", color: "#898781", codes: [7500, 7598, 7599] },
];
const NONE_OTHER = HEATING_GROUPS[HEATING_GROUPS.length - 1];

const groupByCode = new Map();
HEATING_GROUPS.forEach((g) => g.codes.forEach((c) => groupByCode.set(c, g)));

function heatingGroup(genh1) {
  return groupByCode.get(genh1) || NONE_OTHER;
}

// Circle AREA is proportional to heated surface (GEBF m²), so the radius scales
// with its square root. Clamped so tiny buildings stay visible and huge ones
// don't swamp neighbours. Missing/zero GEBF renders at the minimum radius.
const MIN_R = 4;
const MAX_R = 26;
const R_SCALE = 0.7; // ~10px at 200 m²

function circleRadius(gebf) {
  if (!gebf || gebf <= 0) return MIN_R;
  return Math.max(MIN_R, Math.min(MAX_R, R_SCALE * Math.sqrt(gebf)));
}

// Restore the map view and object-limit from the URL query so a full-page reload
// (e.g. a language switch, which reloads under a new locale prefix) returns to the
// same place. Falls back to a Switzerland-wide view.
const urlParams = new URLSearchParams(location.search);
const initLat = parseFloat(urlParams.get("lat"));
const initLng = parseFloat(urlParams.get("lng"));
const initZoom = parseInt(urlParams.get("z"), 10);
const initLimit = urlParams.get("limit");
if (limitEl && [...limitEl.options].some((o) => o.value === initLimit)) {
  limitEl.value = initLimit;
}

const map = L.map("map").setView(
  Number.isFinite(initLat) && Number.isFinite(initLng) ? [initLat, initLng] : [46.8, 8.2],
  Number.isInteger(initZoom) ? initZoom : 8,
);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap" }).addTo(map);
let layer = L.layerGroup().addTo(map);

// Density heatmap shown when a viewport holds more than the threshold of buildings:
// the server returns an aggregated grid (lat, lng, count) instead of points.
let heat = null;
function clearHeat() {
  if (heat) {
    map.removeLayer(heat);
    heat = null;
  }
}
function renderHeat(density) {
  clearHeat();
  if (!density || !density.length) return;
  const max = density.reduce((m, d) => Math.max(m, d[2]), 0) || 1;
  heat = L.heatLayer(
    density.map(([lat, lng, n]) => [lat, lng, n / max]),
    { radius: 22, blur: 18, minOpacity: 0.3 },
  ).addTo(map);
}

// Write the current view + limit back to the URL (without a history entry) so it
// is always current for the language switcher's `next` value.
function syncUrl(limit) {
  const c = map.getCenter();
  const p = new URLSearchParams(location.search);
  p.set("lat", c.lat.toFixed(5));
  p.set("lng", c.lng.toFixed(5));
  p.set("z", map.getZoom());
  p.set("limit", limit);
  history.replaceState(null, "", `?${p}`);
}

function renderLegend() {
  if (legendEl.dataset.built) return;
  legendEl.innerHTML = HEATING_GROUPS.map(
    (g) =>
      `<div style="display:flex; align-items:center; gap:0.5rem; padding:0.1rem 0;">` +
      `<span style="display:inline-block; flex:none; width:0.75rem; height:0.75rem; border-radius:9999px;` +
      ` border:1px solid #fff; box-shadow:0 0 1px rgba(0,0,0,0.4); background:${g.color};"></span>` +
      `<span>${heatingLabels[g.key]}</span></div>`,
  ).join("");
  legendEl.dataset.built = "1";
}

async function refresh() {
  const b = map.getBounds();
  const limit = currentLimit();
  syncUrl(limit);
  const q = new URLSearchParams({
    south: b.getSouth(),
    west: b.getWest(),
    north: b.getNorth(),
    east: b.getEast(),
    limit,
  });
  const fc = await (await fetch(`${pointsUrl}?${q}`)).json();
  layer.clearLayers();

  // Only draw individual objects once fewer than the selected threshold are in
  // view; above that the server returns truncated with a density grid, which we
  // render as a heatmap overview instead of the circles.
  if (fc.truncated) {
    if (L.heatLayer) {
      renderHeat(fc.density);
      hintEl.style.display = "none";
    } else {
      // Fallback if the heat plugin failed to load: prompt the user to zoom in.
      hintEl.textContent = hintTemplate.replaceAll("{n}", limit);
      hintEl.style.display = "block";
    }
    legendEl.style.display = "none";
    return;
  }
  clearHeat();
  hintEl.style.display = "none";
  if (fc.features.length) {
    renderLegend();
    legendEl.style.display = "block";
  } else {
    legendEl.style.display = "none";
  }

  fc.features.forEach((f) => {
    const [lon, lat] = f.geometry.coordinates;
    const { egid, genh1, gebf } = f.properties;
    const group = heatingGroup(genh1);
    // Colour = heating method; a 1.5px white ring keeps overlapping circles
    // visually separated (the secondary encoding the legend relies on).
    L.circleMarker([lat, lon], {
      radius: circleRadius(gebf),
      color: "#ffffff",
      weight: 1.5,
      fillColor: group.color,
      fillOpacity: 0.85,
    })
      .addTo(layer)
      .bindPopup(
        `<a href="${buildingUrl(egid)}">EGID ${egid}</a><br>` +
          `${heatingLabels[group.key]}<br>` +
          `${surfaceLabel}: ${gebf ? `${gebf} m²` : "–"}`,
      );
  });
}
map.on("moveend", refresh);
if (limitEl) limitEl.addEventListener("change", refresh);
refresh();
