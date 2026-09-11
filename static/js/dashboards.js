document.querySelectorAll("canvas[data-metric]").forEach(async (cv) => {
  // Locale-aware: the stats URL is rendered server-side via {% url %} so it
  // carries the active language prefix (e.g. /fr/api/stats/<metric>/).
  const res = await fetch(cv.dataset.statsUrl);
  const { labels, values } = await res.json();
  new Chart(cv, { type: "bar", data: { labels, datasets: [{ label: "Anzahl", data: values }] } });
});
