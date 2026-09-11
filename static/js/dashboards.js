document.querySelectorAll("canvas[data-metric]").forEach(async (cv) => {
  // Locale-aware: the stats URL is rendered server-side via {% url %} so it
  // carries the active language prefix (e.g. /fr/api/stats/<metric>/).
  const res = await fetch(cv.dataset.statsUrl);
  const { labels, values } = await res.json();
  // Locale-aware: the dataset label is rendered server-side (same pattern as
  // data-stats-url) so the Chart.js tooltip/legend follows the active language.
  const countLabel = cv.dataset.countLabel || "Anzahl";
  new Chart(cv, { type: "bar", data: { labels, datasets: [{ label: countLabel, data: values }] } });
});
