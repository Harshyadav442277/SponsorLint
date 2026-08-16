/* SponsorLint UI. Vanilla JS, no build step, no framework. */

const state = {
  briefText: "",
  spec: null,
  takes: [],
  specId: null,
};

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
};

/* ----------------------------------------------------------- screens */

function show(name) {
  document.querySelectorAll(".screen").forEach((s) =>
    s.classList.toggle("is-active", s.id === `screen-${name}`)
  );
  document.querySelectorAll("#flow li").forEach((li) => {
    const step = li.dataset.step;
    if (step === name) li.setAttribute("aria-current", "step");
    else li.removeAttribute("aria-current");
  });
  window.scrollTo({ top: 0, behavior: "instant" });
}

function markDone(name) {
  const li = document.querySelector(`#flow li[data-step="${name}"]`);
  if (li) li.dataset.done = "true";
}

function fail(message) {
  const box = $("error");
  box.textContent = message;
  box.hidden = false;
  box.scrollIntoView({ block: "nearest" });
}

function clearError() {
  $("error").hidden = true;
}

async function call(url, options) {
  const response = await fetch(url, options);
  let body = null;
  try {
    body = await response.json();
  } catch (_) {
    /* non-JSON error body */
  }
  if (!response.ok) {
    const detail = (body && (body.detail || body.message)) || `Request failed (${response.status}).`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body;
}

/* ------------------------------------------------------------ step 1 */

$("load-sample").addEventListener("click", async () => {
  clearError();
  try {
    const data = await call("/api/sample");
    state.briefText = data.brief_text;
    state.spec = data.spec;
    state.takes = data.takes;
    enterReview();
  } catch (err) {
    fail(err.message);
  }
});

$("compile").addEventListener("click", async () => {
  clearError();
  const file = $("brief-file").files[0];
  const text = $("brief-text").value.trim();
  if (!file && !text) {
    fail("Upload a brief file or paste the brief text first.");
    return;
  }

  const form = new FormData();
  if (file) form.append("brief", file);
  form.append("text", text);

  const button = $("compile");
  button.disabled = true;
  button.textContent = "Compiling…";
  try {
    const data = await call("/api/compile", { method: "POST", body: form });
    state.briefText = data.brief_text;
    state.spec = data.spec;
    // Committed takes belong only to the committed Aegis sample campaign.
    // A custom brief must be checked against the user's own upload.
    state.takes = [];
    enterReview();
  } catch (err) {
    fail(err.message);
  } finally {
    button.disabled = false;
    button.textContent = "Compile Brief";
  }
});

/* ------------------------------------------------------------ step 2 */

function enterReview() {
  markDone("upload");
  $("brief-display").textContent = state.briefText;
  renderReview();
  show("review");
}

const TYPES = [
  "MUST_SAY",
  "MUST_NOT_SAY",
  "EXACT_VALUE",
  "MUST_DISCLOSE",
  "DURATION",
  "URL_OR_CTA",
];

function fieldsFor(rule) {
  switch (rule.type) {
    case "MUST_SAY":
    case "MUST_NOT_SAY":
      return [{ key: "phrases", label: "phrases", kind: "lines" }];
    case "EXACT_VALUE":
      return [{ key: "expected", label: "expected", kind: "text" }];
    case "URL_OR_CTA":
      return [
        { key: "expected", label: "expected", kind: "text" },
        { key: "within_last_seconds", label: "within_last_seconds", kind: "number" },
      ];
    case "DURATION":
      return [
        { key: "min_seconds", label: "min_seconds", kind: "number" },
        { key: "max_seconds", label: "max_seconds", kind: "number" },
      ];
    case "MUST_DISCLOSE":
      return [{ key: "within_first_seconds", label: "within_first_seconds", kind: "number" }];
    default:
      return [];
  }
}

function renderReview() {
  const host = $("review-rows");
  host.innerHTML = "";

  state.spec.rules.forEach((rule, index) => {
    const row = el("div", "review-row");
    if (rule.needs_review) row.classList.add("is-review");

    const source = el("div", "review-source");
    source.textContent = `"${rule.source_quote}"`;
    row.appendChild(source);

    const right = el("div", "review-rule");

    const head = el("div", "rule-head");
    const typeSelect = el("select");
    typeSelect.className = "chip chip--type";
    TYPES.forEach((t) => {
      const opt = el("option", null, t);
      opt.value = t;
      if (t === rule.type) opt.selected = true;
      typeSelect.appendChild(opt);
    });
    typeSelect.addEventListener("change", () => {
      rule.type = typeSelect.value;
      renderReview();
    });
    head.appendChild(typeSelect);

    if (rule.needs_review) head.appendChild(el("span", "chip chip--manual", "NEEDS INPUT"));

    const actions = el("div", "rule-actions");
    const del = el("button", null, "Delete");
    del.type = "button";
    del.addEventListener("click", () => {
      state.spec.rules.splice(index, 1);
      renderReview();
    });
    actions.appendChild(del);
    head.appendChild(el("span", "", ""));
    head.lastChild.style.flex = "1 1 auto";
    head.appendChild(actions);
    right.appendChild(head);

    const dl = el("dl", "rule-fields");

    appendField(dl, "label", input("text", rule.label || "", (v) => (rule.label = v)));

    fieldsFor(rule).forEach((f) => {
      let control;
      if (f.kind === "lines") {
        control = document.createElement("textarea");
        control.rows = Math.max(1, (rule[f.key] || []).length);
        control.value = (rule[f.key] || []).join("\n");
        control.style.minHeight = "0";
        control.addEventListener("input", () => {
          rule[f.key] = control.value.split("\n").map((s) => s.trim()).filter(Boolean);
        });
      } else if (f.kind === "number") {
        control = input("number", rule[f.key] ?? "", (v) => {
          rule[f.key] = v === "" ? null : Number(v);
          if (f.key === "within_first_seconds" && v !== "") rule.needs_review = false;
        });
      } else {
        control = input("text", rule[f.key] ?? "", (v) => (rule[f.key] = v));
      }
      appendField(dl, f.label, control);
    });

    const sev = el("select");
    ["error", "warning"].forEach((s) => {
      const opt = el("option", null, s);
      opt.value = s;
      if (s === (rule.severity || "error")) opt.selected = true;
      sev.appendChild(opt);
    });
    sev.addEventListener("change", () => (rule.severity = sev.value));
    appendField(dl, "severity", sev);

    right.appendChild(dl);
    row.appendChild(right);
    host.appendChild(row);
  });

  const manual = state.spec.manual_review || [];
  const manualHost = $("manual-list");
  manualHost.innerHTML = "";
  if (!manual.length) {
    manualHost.appendChild(el("p", "muted", "Nothing in this brief needs manual review."));
  }
  manual.forEach((item) => {
    const card = el("div", "result result--manual");
    const head = el("div", "result-head");
    head.appendChild(el("span", "chip chip--manual", "MANUAL"));
    head.appendChild(el("h3", null, item.reason));
    card.appendChild(head);
    card.appendChild(el("div", "evidence", `"${item.source_quote}"`));
    const confirmation = el("label", "manual-confirm");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = Boolean(item.confirmed);
    checkbox.addEventListener("change", () => {
      item.confirmed = checkbox.checked;
      renderReview();
    });
    confirmation.appendChild(checkbox);
    confirmation.appendChild(document.createTextNode("Confirmed manually"));
    card.appendChild(confirmation);
    manualHost.appendChild(card);
  });

  const unresolved = manual.filter((item) => !item.confirmed).length;
  const confirmed = manual.length - unresolved;
  $("review-count").textContent =
    `${state.spec.rules.length} requirement${state.spec.rules.length === 1 ? "" : "s"} extracted` +
    ` · ${unresolved} manual unresolved` +
    (confirmed ? ` · ${confirmed} manually confirmed` : "");
}

function appendField(dl, label, control) {
  dl.appendChild(el("dt", null, label));
  const dd = el("dd");
  dd.appendChild(control);
  dl.appendChild(dd);
}

function input(type, value, onChange) {
  const node = document.createElement("input");
  node.type = type;
  node.value = value;
  if (type === "number") node.step = "any";
  node.addEventListener("input", () => onChange(node.value));
  return node;
}

$("add-rule").addEventListener("click", () => {
  const used = new Set(state.spec.rules.map((r) => r.id));
  let n = 1;
  while (used.has(`r${n}`)) n += 1;
  state.spec.rules.push({
    id: `r${n}`,
    type: "MUST_SAY",
    label: "New requirement",
    source_quote: "Added by hand during review.",
    severity: "error",
    needs_review: false,
    phrases: [""],
  });
  renderReview();
});

$("approve").addEventListener("click", async () => {
  clearError();
  try {
    const data = await call("/api/spec/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ spec: state.spec }),
    });
    state.specId = data.spec_id;
    markDone("review");
    renderTakes();
    show("processing");
  } catch (err) {
    fail(err.message);
  }
});

/* ------------------------------------------------------------ step 3 */

function renderTakes() {
  const select = $("take");
  select.innerHTML = "";
  if (!state.takes.length) {
    const opt = el("option", null, "No committed takes found");
    opt.value = "";
    select.appendChild(opt);
    return;
  }
  state.takes.forEach((t) => {
    const opt = el("option", null, t.label);
    opt.value = t.id;
    select.appendChild(opt);
  });
}

function steps(items) {
  const host = $("steps");
  host.innerHTML = "";
  items.forEach((item) => {
    const li = el("li");
    li.dataset.state = item.state;
    const glyph = { done: "✓", active: "◐", pending: "·" }[item.state];
    li.appendChild(el("span", "glyph", glyph));
    li.appendChild(document.createTextNode(item.text));
    host.appendChild(li);
  });
  $("progress-panel").hidden = false;
}

$("back-to-review").addEventListener("click", () => show("review"));

$("run-check").addEventListener("click", async () => {
  clearError();
  const video = $("video-file").files[0];
  const take = $("take").value;

  if (!video && !take) {
    fail("Choose a committed take or upload a video file.");
    return;
  }

  const form = new FormData();
  form.append("spec_id", state.specId);
  if (video) form.append("video", video);
  else form.append("take", take);

  steps([
    { state: "done", text: `Approved ${state.spec.rules.length} requirements` },
    {
      state: "active",
      text: video ? "Transcribing sponsor segment…" : "Loading cached transcript",
    },
    { state: "pending", text: "Running checks" },
  ]);

  const button = $("run-check");
  button.disabled = true;
  try {
    const data = await call("/api/verify", { method: "POST", body: form });
    steps([
      { state: "done", text: `Approved ${state.spec.rules.length} requirements` },
      { state: "done", text: video ? "Transcribed sponsor segment" : "Loaded cached transcript" },
      { state: "done", text: "Ran checks" },
    ]);
    markDone("processing");
    renderReport(data.report);
    show("report");
  } catch (err) {
    $("progress-panel").hidden = true;
    fail(err.message);
  } finally {
    button.disabled = false;
  }
});

/* ------------------------------------------------------------ step 4 */

function renderReport(report) {
  const verdict = $("verdict");
  verdict.innerHTML = "";
  const banner = el("div", `verdict verdict--${report.state_class}`);
  banner.appendChild(el("div", "icon", report.icon));
  const body = el("div");
  body.appendChild(el("h2", null, report.label));
  body.appendChild(el("p", null, report.subline));
  body.appendChild(el("span", "score", `${report.score} requirements passed`));
  banner.appendChild(body);
  verdict.appendChild(banner);

  const host = $("findings");
  host.innerHTML = "";

  const failures = report.results.filter((r) => r.status === "FAIL" || r.status === "WARN");
  const manualResults = report.results.filter((r) => r.status === "MANUAL_REVIEW");
  const passes = report.results.filter((r) => r.status === "PASS");

  failures.forEach((r) => host.appendChild(resultCard(r)));

  if (manualResults.length || report.manual_review.length) {
    host.appendChild(el("p", "section-label", "Manual review"));
    manualResults.forEach((r) => host.appendChild(resultCard(r)));
    report.manual_review.forEach((item) => {
      const card = el("div", "result result--manual");
      const head = el("div", "result-head");
      head.appendChild(
        el("span", `chip chip--${item.confirmed ? "pass" : "manual"}`,
          item.confirmed ? "CONFIRMED" : "MANUAL")
      );
      head.appendChild(el("h3", null, item.reason));
      card.appendChild(head);
      card.appendChild(el("div", "evidence", `"${item.source_quote}"`));
      card.appendChild(el(
        "p",
        "advisory",
        item.confirmed
          ? "Confirmed by the creator during spec review."
          : "SponsorLint does not verify this. Confirm it yourself before sending."
      ));
      manualHostAppend(card, host);
    });
  }

  if (passes.length) {
    const details = el("details", "passes");
    details.appendChild(el("summary", null, `${passes.length} passing requirements`));
    passes.forEach((r) => details.appendChild(resultCard(r)));
    host.appendChild(details);
  }
}

function manualHostAppend(card, host) {
  host.appendChild(card);
}

function resultCard(r) {
  const card = el("div", `result result--${r.chip}`);

  const head = el("div", "result-head");
  head.appendChild(el("span", `chip chip--${r.chip}`, r.word));
  head.appendChild(el("h3", null, r.title));
  if (r.timecode) head.appendChild(timecodeButton(r.timecode));
  card.appendChild(head);

  const dl = el("dl", "rule-fields");
  if (r.expected) appendField(dl, "expected", el("span", null, r.expected));
  if (r.detected) appendField(dl, "detected", el("span", null, r.detected));
  if (dl.children.length) card.appendChild(dl);

  if (r.evidence_html) {
    const evidence = el("div", "evidence");
    evidence.innerHTML = `"${r.evidence_html}"`;
    card.appendChild(evidence);
  }

  if (r.advisory) card.appendChild(el("p", "advisory", r.advisory));

  const from = el("dl", "from-brief");
  from.appendChild(el("dt", null, "From the brief"));
  from.appendChild(el("dd", null, `"${r.source_quote}"`));
  card.appendChild(from);

  return card;
}

function timecodeButton(timecode) {
  const button = el("button", "timecode", timecode);
  button.type = "button";
  button.title = "Copy this timecode";
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(timecode);
      button.textContent = "copied";
      setTimeout(() => (button.textContent = timecode), 900);
    } catch (_) {
      /* clipboard unavailable — the timecode is still readable */
    }
  });
  return button;
}

$("recheck").addEventListener("click", () => show("review"));
$("start-over").addEventListener("click", () => window.location.reload());
