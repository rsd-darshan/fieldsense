/**
 * FieldSense — turn prediction JSON into a calm, non-technical result card.
 * Depends on nothing; call FieldSenseResult.render(mountEl, kind, payload).
 */
(function (global) {
  "use strict";

  function esc(s) {
    if (s == null || s === "") return "";
    const d = document.createElement("div");
    d.textContent = String(s);
    return d.innerHTML;
  }

  function riskWord(level) {
    const k = String(level || "").toLowerCase();
    if (k === "low") return "Low";
    if (k === "medium") return "Medium";
    if (k === "high") return "High";
    return level ? String(level).charAt(0).toUpperCase() + String(level).slice(1) : "—";
  }

  function intelFrom(data) {
    const i = data && data.intelligence;
    return i && typeof i === "object" ? i : {};
  }


  function prettyLabel(value) {
    const s = String(value == null ? "" : value).trim();
    if (!s) return "—";
    const normalized = s.replace(/_/g, " ").replace(/\s+/g, " ").trim();
    if (/^[a-z\s]+$/.test(normalized)) {
      return normalized.split(" ").map(w => w ? (w[0].toUpperCase() + w.slice(1)) : "").join(" ");
    }
    return normalized;
  }
  function humanizeFertilizerLabel(label, catalog) {
    const s = label == null ? "" : String(label).trim();
    if (!s) return "—";
    if (Array.isArray(catalog) && catalog.indexOf(s) !== -1) return s;
    return s;
  }

  function cropConditionLines(features) {
    if (!features || typeof features !== "object") return [];
    const lines = [];
    const n = features.N;
    const p = features.P;
    const k = features.K;
    if (n != null && n !== "") lines.push(`<li><span>Nitrogen</span> ${esc(n)}</li>`);
    if (p != null && p !== "") lines.push(`<li><span>Phosphorus</span> ${esc(p)}</li>`);
    if (k != null && k !== "") lines.push(`<li><span>Potassium</span> ${esc(k)}</li>`);
    const t = features.temperature;
    if (t != null && t !== "") lines.push(`<li><span>Temperature</span> ${esc(t)} °C</li>`);
    const h = features.humidity;
    if (h != null && h !== "") lines.push(`<li><span>Air humidity</span> ${esc(h)}%</li>`);
    const ph = features.ph;
    if (ph != null && ph !== "") lines.push(`<li><span>Soil pH</span> ${esc(ph)}</li>`);
    const r = features.rainfall;
    if (r != null && r !== "") lines.push(`<li><span>Rainfall</span> ${esc(r)} mm</li>`);
    return lines;
  }

  function fertConditionLines(inputs) {
    if (!inputs || typeof inputs !== "object") return [];
    const lines = [];
    const t = inputs.temperature;
    if (t != null && t !== "") lines.push(`<li><span>Temperature</span> ${esc(t)} °C</li>`);
    const h = inputs.humidity;
    if (h != null && h !== "") lines.push(`<li><span>Air humidity</span> ${esc(h)}%</li>`);
    const m = inputs.moisture;
    if (m != null && m !== "") lines.push(`<li><span>Soil moisture</span> ${esc(m)}%</li>`);
    const soil = inputs.soil_type;
    if (soil != null && soil !== "") lines.push(`<li><span>Soil type</span> ${esc(soil)}</li>`);
    const crop = inputs.crop_type;
    if (crop != null && crop !== "") lines.push(`<li><span>Crop</span> ${esc(crop)}</li>`);
    const n = inputs.nitrogen;
    if (n != null && n !== "") lines.push(`<li><span>Nitrogen</span> ${esc(n)}</li>`);
    const p = inputs.phosphorous;
    if (p != null && p !== "") lines.push(`<li><span>Phosphorus</span> ${esc(p)}</li>`);
    const k = inputs.potassium;
    if (k != null && k !== "") lines.push(`<li><span>Potassium</span> ${esc(k)}</li>`);
    return lines;
  }

  function shortMeaning(summary, fallback) {
    let s = (summary || "").trim();
    if (!s && fallback) s = String(fallback).trim().slice(0, 280);
    if (!s) return "This read reflects the numbers and patterns we saw in your field profile.";
    if (s.length > 320) return s.slice(0, 317).trim() + "…";
    return s;
  }

  function renderCard(title, primaryHtml, score, riskLevel, meaning, conditionLines) {
    const scoreNum = score != null && score !== "" ? esc(score) : "—";
    const risk = riskWord(riskLevel);
    const healthLine =
      score != null && score !== ""
        ? `Field health (${scoreNum}/100) — ${esc(risk)} risk`
        : `Field health — ${esc(risk)} risk`;
    const cond =
      conditionLines && conditionLines.length
        ? `<section class="fs-result__section"><h4 class="fs-result__h">Current conditions</h4><ul class="fs-result__list">${conditionLines.join("")}</ul></section>`
        : "";
    return `
<div class="fs-result__card">
  <h3 class="fs-result__h fs-result__h--model">${esc(title)}</h3>
  <section class="fs-result__section">
    <h4 class="fs-result__h">Primary result</h4>
    <p class="fs-result__primary">${primaryHtml}</p>
  </section>
  <section class="fs-result__section">
    <h4 class="fs-result__h">Field health</h4>
    <p class="fs-result__health">${healthLine}</p>
  </section>
  <section class="fs-result__section">
    <h4 class="fs-result__h">What this means</h4>
    <p class="fs-result__meaning">${esc(meaning)}</p>
  </section>
  ${cond}
</div>`;
  }

  function renderError(message) {
    return `<div class="fs-result__card fs-result__card--error" role="alert"><p class="fs-result__err">${esc(message)}</p></div>`;
  }

  function renderLoading() {
    return `<div class="fs-result__card fs-result__card--loading"><p class="fs-result__loading">Working on it…</p></div>`;
  }

  const api = {
    loading(mount) {
      mount.className = "fs-result-mount fs-result-mount--loading";
      mount.innerHTML = renderLoading();
      mount.hidden = false;
    },

    render(mount, kind, data, fertCatalog) {
      mount.hidden = false;
      if (!data || typeof data !== "object") {
        mount.className = "fs-result-mount fs-result-mount--error";
        mount.innerHTML = renderError("Something went wrong. Please try again.");
        return;
      }
      if (data.error) {
        mount.className = "fs-result-mount fs-result-mount--error";
        mount.innerHTML = renderError(data.error);
        return;
      }

      const intel = intelFrom(data);
      const score = intel.health_score;
      const risk = intel.risk_level;
      const summary = intel.summary || "";
      let title = "Result";
      let primary = "—";
      let meaningFallback = "";
      let lines = [];

      if (kind === "crop") {
        title = "Crop";
        primary = esc(prettyLabel(data.label || "—"));
        meaningFallback = "";
        lines = cropConditionLines(data.features_used);
      } else if (kind === "fert") {
        title = "Fertilizer";
        primary = esc(prettyLabel(humanizeFertilizerLabel(data.label, fertCatalog)));
        lines = fertConditionLines(data.inputs);
      } else if (kind === "leaf") {
        title = "Plant check";
        primary = esc(prettyLabel(data.prediction || "—"));
        const d = (data.description || "").trim();
        const ps = (data.possible_steps || "").trim();
        meaningFallback = d ? d : ps;
        lines = [];
      }

      const meaning = shortMeaning(summary, meaningFallback);
      mount.className = "fs-result-mount fs-result-mount--ok";
      mount.innerHTML = renderCard(title, primary, score, risk, meaning, lines);
    },
  };

  global.FieldSenseResult = api;
})(typeof window !== "undefined" ? window : this);
