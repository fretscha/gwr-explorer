document.querySelectorAll("canvas[data-metric]").forEach(async (cv) => {
  const res = await fetch(`/api/stats/${cv.dataset.metric}/`);
  const { labels, values } = await res.json();
  new Chart(cv, { type: "bar", data: { labels, datasets: [{ label: "Anzahl", data: values }] } });
});
