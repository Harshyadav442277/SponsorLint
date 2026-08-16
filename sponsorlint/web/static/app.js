/* SponsorLint UI — one local-first workflow, no framework, no build step. */

const SESSION_KEY = "sponsorlint-ui-v3";
const STEP_ORDER = ["upload", "review", "processing", "report"];
const STEP_HASH = { upload: "brief", review: "review", processing: "check", report: "report" };
const HASH_STEP = { brief: "upload", review: "review", check: "processing", report: "report" };

const initialState = () => ({
  briefText: "",
  spec: null,
  takes: [],
  specId: null,
  lastReport: null,
  lastReportId: null,
  lastTake: "v1",
  current: "upload",
  maxStep: 0,
  customBriefOpen: false,
});

const state = initialState();
const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
};

function restoreState() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(SESSION_KEY) || "null");
    if (saved && typeof saved === "object") Object.assign(state, saved);
  } catch (_) {
    sessionStorage.removeItem(SESSION_KEY);
  }
}

function persistState() {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(state));
  } catch (_) {
    /* Session persistence is a convenience, never a requirement. */
  }
}

function stepIndex(name) {
  return STEP_ORDER.indexOf(name);
}

function canAccess(name) {
  const index = stepIndex(name);
  if (index < 0 || index > state.maxStep) return false;
  if (name === "review") return Boolean(state.spec);
  if (name === "processing") return Boolean(state.spec && state.specId);
  if (name === "report") return Boolean(state.lastReport);
  return true;
}

function updateWorkflow() {
  const currentIndex = stepIndex(state.current);
  document.querySelectorAll("#flow li").forEach((item) => {
    const name = item.dataset.step;
    const index = stepIndex(name);
    const button = item.querySelector("button");
    const status = item.querySelector("small");
    item.classList.remove("is-current", "is-complete", "is-available", "is-locked");

    if (name === state.current) {
      item.classList.add("is-current");
      button.disabled = true;
      button.setAttribute("aria-current", "step");
      status.textContent = "Current";
    } else if (canAccess(name) && index < state.maxStep) {
      item.classList.add("is-complete");
      button.disabled = false;
      button.removeAttribute("aria-current");
      status.textContent = "Complete";
      item.querySelector(".step-node").textContent = "✓";
    } else if (canAccess(name)) {
      item.classList.add("is-available");
      button.disabled = false;
      button.removeAttribute("aria-current");
      status.textContent = index < currentIndex ? "Complete" : "Available";
      item.querySelector(".step-node").textContent = String(index + 1).padStart(2, "0");
    } else {
      item.classList.add("is-locked");
      button.disabled = true;
      button.removeAttribute("aria-current");
      status.textContent = "Locked";
      item.querySelector(".step-node").textContent = String(index + 1).padStart(2, "0");
    }

    if (name === state.current) {
      item.querySelector(".step-node").textContent = String(index + 1).padStart(2, "0");
    }
  });
}

function show(name, { historyMode = "push", focus = true } = {}) {
  if (!canAccess(name)) return false;
  state.current = name;
  document.querySelectorAll(".screen").forEach((screen) => {
    screen.classList.toggle("is-active", screen.id === `screen-${name}`);
  });
  updateWorkflow();
  persistState();

  const hash = `#${STEP_HASH[name]}`;
  if (historyMode === "replace") history.replaceState({ step: name }, "", hash);
  if (historyMode === "push" && location.hash !== hash) history.pushState({ step: name }, "", hash);

  window.scrollTo({ top: 0, behavior: "instant" });
  if (focus) {
    window.setTimeout(() => {
      document.querySelector(`#screen-${name} [data-screen-title]`)?.focus({ preventScroll: true });
    }, 30);
  }
  return true;
}

function navigate(name) {
  if (name === "review" && state.spec) renderReview();
  if (name === "processing" && state.specId) renderTakes();
  if (name === "report" && state.lastReport) renderReport(state.lastReport);
  show(name);
}

function fail(message) {
  const box = $("error");
  box.className = "notice notice--error";
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
    /* A proxy may return a non-JSON failure page. */
  }
  if (!response.ok) {
    const detail = (body && (body.detail || body.message)) || `Request failed (${response.status}).`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body;
}

/* ============================================================= motion */

function runTyper() {
  const host = $("principle-typer");
  if (!host) return;
  const source = host.textContent;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  host.textContent = "";
  const characters = [];

  source.split(/(\s+)/).forEach((part) => {
    if (/^\s+$/.test(part)) {
      host.appendChild(document.createTextNode(part));
      return;
    }
    const word = el("span", "typer-word");
    [...part].forEach((character) => {
      const span = el("span", "typer-char", character);
      word.appendChild(span);
      characters.push(span);
    });
    host.appendChild(word);
  });

  if (reduced) return;
  const states = ["is-block", "is-inverse", "is-outline"];
  let frame = 0;
  let energy = 0;
  let nextPulse = 0;
  host.addEventListener("pointermove", () => { energy = 1; });
  host.addEventListener("pointerleave", () => { energy = Math.max(energy, .35); });
  const animate = () => {
    const now = performance.now();
    if (now >= nextPulse) {
      frame = 0;
      nextPulse = now + 2500 + Math.random() * 1700;
    }
    characters.forEach((character, index) => {
      character.className = "typer-char";
      const local = frame - index * (energy > .5 ? .12 : .28);
      if (local >= 0 && local < 3.8 + energy * 2.4) {
        character.classList.add(states[(index + Math.floor(local)) % states.length]);
      }
    });
    frame += .9 + energy * 1.8;
    energy *= .92;
    window.setTimeout(animate, 52);
  };
  animate();
}

function initGlyphField() {
  const canvas = $("glyph-field");
  if (!canvas) return;
  const ctx = canvas.getContext("2d", { alpha: false });
  if (!ctx) return;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let animationFrame = 0;
  let resizeTimer = 0;
  let visible = true;
  let pointerActive = false;
  let pointerX = .5;
  let pointerY = .5;

  canvas.addEventListener("pointermove", (event) => {
    const rect = canvas.getBoundingClientRect();
    pointerX = Math.max(0, Math.min(1, (event.clientX - rect.left) / Math.max(1, rect.width)));
    pointerY = Math.max(0, Math.min(1, (event.clientY - rect.top) / Math.max(1, rect.height)));
    pointerActive = true;
  });
  canvas.addEventListener("pointerleave", () => { pointerActive = false; });
  canvas.addEventListener("pointercancel", () => { pointerActive = false; });
  new IntersectionObserver((entries) => {
    visible = entries.some((entry) => entry.isIntersecting);
  }, { rootMargin: "140px" }).observe(canvas);

  function seeded(index, offset = 0) {
    const value = Math.sin((index + 1) * 91.345 + offset * 17.17) * 43758.5453;
    return value - Math.floor(value);
  }

  function build() {
    window.cancelAnimationFrame(animationFrame);
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(280, Math.round(rect.width));
    const height = Math.max(240, Math.round(rect.height));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const mask = document.createElement("canvas");
    mask.width = width;
    mask.height = height;
    const maskContext = mask.getContext("2d");
    maskContext.fillStyle = "#fff";
    maskContext.textAlign = "center";
    maskContext.textBaseline = "middle";
    const mobile = width < 430;
    const fontSize = Math.floor(Math.min(width / 5.9, height / 4.4));
    maskContext.font = `800 ${fontSize}px ${getComputedStyle(document.body).fontFamily}`;
    const lines = ["VERIFY", "BEFORE", "SEND"];
    const lineGap = fontSize * .9;
    const centerY = height / 2 + fontSize * .05;
    lines.forEach((line, index) => {
      maskContext.fillText(line, width / 2, centerY + (index - 1) * lineGap);
    });

    const pixels = maskContext.getImageData(0, 0, width, height).data;
    const step = mobile ? 9 : 8;
    const targets = [];
    for (let y = step; y < height - step; y += step) {
      for (let x = step; x < width - step; x += step) {
        if (pixels[(y * width + x) * 4 + 3] > 120) targets.push({ x, y });
      }
    }
    const maxParticles = mobile ? 390 : 680;
    const stride = Math.max(1, Math.ceil(targets.length / maxParticles));
    const selected = targets.filter((_, index) => index % stride === 0).slice(0, maxParticles);
    const glyphs = "#%+=<>[]{}01/";
    const particles = selected.map((target, index) => {
      const angle = seeded(index, 1) * Math.PI * 8;
      const radius = Math.max(width, height) * (.18 + seeded(index, 2) * .78);
      return {
        tx: target.x,
        ty: target.y,
        sx: width / 2 + Math.cos(angle) * radius,
        sy: height / 2 + Math.sin(angle) * radius,
        angle,
        glyph: glyphs[index % glyphs.length],
        delay: seeded(index, 3) * .2,
      };
    });
    const atmosphere = Array.from({ length: mobile ? 38 : 76 }, (_, index) => ({
      x: seeded(index, 5) * width,
      y: seeded(index, 6) * height,
      glyph: glyphs[(index * 5) % glyphs.length],
      drift: seeded(index, 7) * 8 - 4,
    }));
    const start = performance.now();
    const duration = reduced ? 1 : 1120;

    function ease(value) {
      const v = Math.max(0, Math.min(1, value));
      return 1 - Math.pow(1 - v, 3);
    }

    function draw(now) {
      if (!visible || document.hidden) {
        animationFrame = window.requestAnimationFrame(draw);
        return;
      }
      const elapsed = now - start;
      const progress = Math.min(1, elapsed / duration);
      const seconds = elapsed / 1000;
      ctx.fillStyle = "#090a08";
      ctx.fillRect(0, 0, width, height);
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      ctx.font = `500 ${mobile ? 8 : 9}px ${getComputedStyle(canvas).fontFamily || "monospace"}`;
      atmosphere.forEach((item, index) => {
        const drift = reduced ? 0 : item.drift * Math.sin(seconds * .55 + index);
        ctx.fillStyle = "rgba(180,185,171,.105)";
        const parallaxX = pointerActive ? (pointerX - .5) * (2 + index % 4) : Math.sin(seconds * .23 + index) * .7;
        const parallaxY = pointerActive ? (pointerY - .5) * (2 + index % 3) : 0;
        ctx.fillText(item.glyph, item.x + drift + parallaxX, item.y + parallaxY);
      });

      particles.forEach((particle, index) => {
        const local = ease((progress - particle.delay) / (1 - particle.delay));
        const spin = (1 - local) * Math.PI * 1.7;
        let x = particle.sx + (particle.tx - particle.sx) * local + Math.cos(particle.angle + spin) * (1 - local) * 18;
        let y = particle.sy + (particle.ty - particle.sy) * local + Math.sin(particle.angle + spin) * (1 - local) * 18;
        if (progress >= 1 && !reduced) {
          x += Math.sin(seconds * .9 + index * .31) * 1.25;
          y += Math.cos(seconds * .72 + index * .27) * .85;
          if (pointerActive) {
            const cursorX = pointerX * width;
            const cursorY = pointerY * height;
            const deltaX = x - cursorX;
            const deltaY = y - cursorY;
            const distance = Math.max(1, Math.hypot(deltaX, deltaY));
            const influence = Math.max(0, 1 - distance / 105);
            x += (deltaX / distance) * influence * 16;
            y += (deltaY / distance) * influence * 16;
          }
        }
        const flicker = progress >= 1 && Math.sin(seconds * 2.3 + index * 8.1) > .996;
        const glyph = local < .78 || flicker ? glyphs[(index + Math.floor(seconds * 14)) % glyphs.length] : particle.glyph;
        const alpha = .18 + local * .76;

        if (!reduced && (local > .25 && local < .88 || pointerActive && progress >= 1)) {
          ctx.fillStyle = `rgba(255,92,76,${alpha * .13})`;
          ctx.fillText(glyph, x - (pointerActive ? 2.2 : 1.4), y);
          ctx.fillStyle = `rgba(87,205,255,${alpha * .10})`;
          ctx.fillText(glyph, x + (pointerActive ? 2.2 : 1.4), y);
        }
        ctx.fillStyle = `rgba(224,232,211,${alpha})`;
        ctx.fillText(glyph, x, y);
      });

      ctx.fillStyle = "rgba(255,255,255,.018)";
      for (let y = 2; y < height; y += 5) ctx.fillRect(0, y, width, 1);
      ctx.fillStyle = "rgba(0,0,0,.18)";
      ctx.fillRect(0, 0, width, 14);
      ctx.fillRect(0, height - 14, width, 14);
      ctx.fillRect(0, 0, 10, height);
      ctx.fillRect(width - 10, 0, 10, height);

      if (!reduced || progress < 1) animationFrame = window.requestAnimationFrame(draw);
    }

    animationFrame = window.requestAnimationFrame(draw);
  }

  build();
  window.addEventListener("resize", () => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(build, 140);
  });
}

function animateResolveIndicator() {
  const node = $("resolve-indicator");
  const final = "VERIFY";
  const glyphs = "#/[]{}01+*";
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    node.textContent = final;
    return () => {};
  }
  let frame = 0;
  const timer = window.setInterval(() => {
    node.textContent = [...final].map((character, index) =>
      index < frame / 2 ? character : glyphs[(index * 3 + frame) % glyphs.length]
    ).join("");
    frame = (frame + 1) % 18;
  }, 85);
  return () => {
    window.clearInterval(timer);
    node.textContent = final;
  };
}

/* ============================================================= Brief */

function openCustomBrief() {
  state.customBriefOpen = true;
  $("custom-brief-panel").hidden = false;
  $("show-custom-brief").setAttribute("aria-expanded", "true");
  persistState();
  $("custom-brief-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  window.setTimeout(() => $("mode-upload").focus(), 350);
}

let activeBriefMode = "upload";

function setBriefMode(mode) {
  activeBriefMode = mode;
  const upload = mode === "upload";
  $("mode-upload").setAttribute("aria-selected", String(upload));
  $("mode-paste").setAttribute("aria-selected", String(!upload));
  $("upload-mode").hidden = !upload;
  $("paste-mode").hidden = upload;
  (upload ? $("brief-file") : $("brief-text")).focus();
}

$("load-sample").addEventListener("click", async () => {
  clearError();
  const button = $("load-sample");
  button.disabled = true;
  button.querySelector(".cta-copy strong").textContent = "Loading Aegis campaign…";
  try {
    const data = await call("/api/sample");
    state.briefText = data.brief_text;
    state.spec = data.spec;
    state.takes = data.takes;
    state.specId = null;
    state.lastReport = null;
    state.lastReportId = null;
    state.lastTake = "v1";
    state.maxStep = 1;
    $("brief-display").textContent = state.briefText;
    renderReview();
    show("review");
  } catch (error) {
    fail(`${error.message} Try the sample again, or use your own brief.`);
  } finally {
    button.disabled = false;
    button.querySelector(".cta-copy strong").textContent = "Run sample campaign";
  }
});

$("show-custom-brief").addEventListener("click", openCustomBrief);
$("mode-upload").addEventListener("click", () => setBriefMode("upload"));
$("mode-paste").addEventListener("click", () => setBriefMode("paste"));

$("compile").addEventListener("click", async () => {
  clearError();
  const file = activeBriefMode === "upload" ? $("brief-file").files[0] : null;
  const text = activeBriefMode === "paste" ? $("brief-text").value.trim() : "";
  if (!file && !text) {
    fail("Add a brief first. Choose a file or paste the sponsor requirements.");
    return;
  }

  const form = new FormData();
  if (file) form.append("brief", file);
  form.append("text", text);
  const button = $("compile");
  button.disabled = true;
  button.textContent = "Compiling grounded rules…";
  try {
    const data = await call("/api/compile", { method: "POST", body: form });
    state.briefText = data.brief_text;
    state.spec = data.spec;
    state.takes = [];
    state.specId = null;
    state.lastReport = null;
    state.lastReportId = null;
    state.lastTake = "";
    state.maxStep = 1;
    $("brief-display").textContent = state.briefText;
    renderReview();
    show("review");
  } catch (error) {
    fail(`${error.message} Your brief is still here—adjust it and retry.`);
  } finally {
    button.disabled = false;
    button.innerHTML = 'Compile requirements <span aria-hidden="true">→</span>';
  }
});

/* ============================================================= Review */

const TYPES = ["MUST_SAY", "MUST_NOT_SAY", "EXACT_VALUE", "MUST_DISCLOSE", "DURATION", "URL_OR_CTA"];
const RULE_PAYLOAD_KEYS = ["expected", "phrases", "min_seconds", "max_seconds", "within_first_seconds", "within_last_seconds"];

function fieldsFor(rule) {
  switch (rule.type) {
    case "MUST_SAY":
    case "MUST_NOT_SAY":
      return [{ key: "phrases", label: "Phrases — one per line", kind: "lines" }];
    case "EXACT_VALUE":
      return [{ key: "expected", label: "Enforced value", kind: "text" }];
    case "URL_OR_CTA":
      return [
        { key: "expected", label: "URL or CTA", kind: "text" },
        { key: "within_last_seconds", label: "Required within final seconds", kind: "number" },
      ];
    case "DURATION":
      return [
        { key: "min_seconds", label: "Minimum seconds", kind: "number" },
        { key: "max_seconds", label: "Maximum seconds", kind: "number" },
      ];
    case "MUST_DISCLOSE":
      return [{ key: "within_first_seconds", label: "Required within first seconds", kind: "number" }];
    default:
      return [];
  }
}

function ruleDisplayValue(rule) {
  if (rule.type === "MUST_SAY") return (rule.phrases || []).map((value) => `“${value}”`).join(" or ") || "Phrase required";
  if (rule.type === "MUST_NOT_SAY") return `Never say ${(rule.phrases || []).map((value) => `“${value}”`).join(" or ")}`;
  if (rule.type === "EXACT_VALUE") return rule.expected || "Exact value required";
  if (rule.type === "MUST_DISCLOSE") return `Within the first ${rule.within_first_seconds ?? "?"} seconds`;
  if (rule.type === "DURATION") return `${rule.min_seconds ?? "?"}–${rule.max_seconds ?? "?"} seconds`;
  if (rule.type === "URL_OR_CTA") {
    const timing = rule.within_last_seconds != null ? ` · final ${rule.within_last_seconds}s` : "";
    return `${rule.expected || "URL required"}${timing}`;
  }
  return rule.label || "Requirement";
}

function markSpecDirty() {
  state.specId = null;
  state.lastReport = null;
  state.lastReportId = null;
  state.maxStep = Math.min(state.maxStep, 1);
  $("approval-status").textContent = "Changes need approval";
  updateWorkflow();
  persistState();
}

function editorField(label, control, wide = false) {
  const wrapper = el("label", `editor-field${wide ? " editor-field--wide" : ""}`);
  wrapper.appendChild(el("span", null, label));
  wrapper.appendChild(control);
  return wrapper;
}

function makeInput(type, value, onInput) {
  const input = document.createElement("input");
  input.type = type;
  input.value = value ?? "";
  if (type === "number") input.step = "any";
  input.addEventListener("input", () => onInput(input.value));
  return input;
}

function renderRuleCard(rule, index) {
  const card = el("article", "rule-card");
  card.dataset.ruleId = rule.id;
  const grid = el("div", "rule-card-grid");

  const source = el("div", "source-citation");
  const sourceLabel = el("div", "citation-label");
  sourceLabel.appendChild(el("span", null, "Source / brief"));
  sourceLabel.appendChild(el("span", null, `Citation ${String(index + 1).padStart(2, "0")}`));
  source.appendChild(sourceLabel);
  source.appendChild(el("blockquote", null, rule.source_quote || "Added manually during review."));
  grid.appendChild(source);

  const bridge = el("div", "rule-bridge");
  bridge.appendChild(el("span", null, "→"));
  grid.appendChild(bridge);

  const requirement = el("div", "requirement-view");
  const requirementLabel = el("div", "requirement-label");
  requirementLabel.appendChild(el("span", "rule-id", String(rule.id || `r${index + 1}`).toUpperCase()));
  requirementLabel.appendChild(el("span", "rule-type", rule.type.replaceAll("_", " ")));
  requirement.appendChild(requirementLabel);
  requirement.appendChild(el("h3", null, rule.label || "Untitled requirement"));
  const value = el("p", "rule-value", ruleDisplayValue(rule));
  requirement.appendChild(value);
  const meta = el("div", "rule-meta");
  meta.appendChild(el("span", null, `${rule.severity || "error"} severity`));
  if (rule.needs_review) meta.appendChild(el("span", "rule-needs-input", "Needs human input"));
  requirement.appendChild(meta);

  const details = el("details", "rule-editor");
  details.appendChild(el("summary", null, "Edit requirement"));
  const panel = el("div", "editor-panel");

  const typeSelect = document.createElement("select");
  TYPES.forEach((type) => {
    const option = el("option", null, type.replaceAll("_", " "));
    option.value = type;
    option.selected = type === rule.type;
    typeSelect.appendChild(option);
  });
  typeSelect.addEventListener("change", () => {
    RULE_PAYLOAD_KEYS.forEach((key) => delete rule[key]);
    rule.type = typeSelect.value;
    rule.needs_review = false;
    markSpecDirty();
    renderReview();
  });
  panel.appendChild(editorField("Rule type", typeSelect));

  const severity = document.createElement("select");
  ["error", "warning"].forEach((level) => {
    const option = el("option", null, level);
    option.value = level;
    option.selected = level === (rule.severity || "error");
    severity.appendChild(option);
  });
  severity.addEventListener("change", () => {
    rule.severity = severity.value;
    markSpecDirty();
    meta.firstChild.textContent = `${severity.value} severity`;
  });
  panel.appendChild(editorField("Severity", severity));

  const labelInput = makeInput("text", rule.label, (next) => {
    rule.label = next;
    requirement.querySelector("h3").textContent = next || "Untitled requirement";
    markSpecDirty();
  });
  panel.appendChild(editorField("Human-readable title", labelInput, true));

  fieldsFor(rule).forEach((field) => {
    let control;
    if (field.kind === "lines") {
      control = document.createElement("textarea");
      control.value = (rule[field.key] || []).join("\n");
      control.addEventListener("input", () => {
        rule[field.key] = control.value.split("\n").map((value) => value.trim()).filter(Boolean);
        value.textContent = ruleDisplayValue(rule);
        markSpecDirty();
      });
    } else {
      control = makeInput(field.kind, rule[field.key], (next) => {
        rule[field.key] = field.kind === "number" ? (next === "" ? null : Number(next)) : next;
        if (next !== "" && ["within_first_seconds", "within_last_seconds"].includes(field.key)) rule.needs_review = false;
        value.textContent = ruleDisplayValue(rule);
        markSpecDirty();
      });
    }
    panel.appendChild(editorField(field.label, control, field.kind === "lines"));
  });

  const sourceInput = document.createElement("textarea");
  sourceInput.value = rule.source_quote || "";
  sourceInput.addEventListener("input", () => {
    rule.source_quote = sourceInput.value;
    source.querySelector("blockquote").textContent = sourceInput.value || "Added manually during review.";
    markSpecDirty();
  });
  panel.appendChild(editorField("Source quote", sourceInput, true));

  const actions = el("div", "editor-actions");
  const remove = el("button", "delete-rule", "Delete this rule");
  remove.type = "button";
  remove.addEventListener("click", () => {
    state.spec.rules.splice(index, 1);
    markSpecDirty();
    renderReview();
  });
  const close = el("button", "close-editor", "Done editing");
  close.type = "button";
  close.addEventListener("click", () => {
    details.open = false;
    details.querySelector("summary").focus();
  });
  actions.appendChild(remove);
  actions.appendChild(close);
  panel.appendChild(actions);
  details.appendChild(panel);
  requirement.appendChild(details);
  grid.appendChild(requirement);
  card.appendChild(grid);
  return card;
}

function renderReview() {
  if (!state.spec) return;
  $("brief-display").textContent = state.briefText;
  const host = $("review-rows");
  host.innerHTML = "";
  state.spec.rules.forEach((rule, index) => host.appendChild(renderRuleCard(rule, index)));

  const manual = state.spec.manual_review || [];
  const manualHost = $("manual-list");
  manualHost.innerHTML = "";
  if (!manual.length) manualHost.appendChild(el("p", "manual-empty", "No visual or manual requirements in this brief."));
  manual.forEach((item, index) => {
    const row = el("article", "manual-item");
    const copy = el("div");
    copy.appendChild(el("h3", null, item.reason));
    copy.appendChild(el("blockquote", null, `“${item.source_quote}”`));
    row.appendChild(copy);
    const confirmation = el("label", "manual-confirm");
    const checkbox = document.createElement("input");
    const confirmationText = document.createTextNode(item.confirmed ? "Confirmed" : "Confirm manually");
    checkbox.type = "checkbox";
    checkbox.checked = Boolean(item.confirmed);
    checkbox.addEventListener("change", () => {
      state.spec.manual_review[index].confirmed = checkbox.checked;
      confirmationText.textContent = checkbox.checked ? "Confirmed" : "Confirm manually";
      markSpecDirty();
      renderReviewCounts();
    });
    confirmation.appendChild(checkbox);
    confirmation.appendChild(confirmationText);
    row.appendChild(confirmation);
    manualHost.appendChild(row);
  });
  renderReviewCounts();
}

function clearRuleErrors() {
  document.querySelectorAll(".rule-card.is-invalid").forEach((card) => card.classList.remove("is-invalid"));
}

function markRuleErrors(message) {
  clearRuleErrors();
  const indices = [...String(message).matchAll(/rules\s*->\s*(\d+)/gi)].map((match) => Number(match[1]));
  const ids = [...String(message).matchAll(/\b(r\d+)\s*:/gi)].map((match) => match[1].toLowerCase());
  const cards = [];
  indices.forEach((index) => {
    const card = document.querySelectorAll(".rule-card")[index];
    if (card) cards.push(card);
  });
  ids.forEach((id) => {
    const card = document.querySelector(`[data-rule-id="${CSS.escape(id)}"]`);
    if (card) cards.push(card);
  });
  [...new Set(cards)].forEach((card) => {
    card.classList.add("is-invalid");
    const details = card.querySelector("details");
    if (details) details.open = true;
  });
  if (cards[0]) cards[0].scrollIntoView({ behavior: "smooth", block: "center" });
  return cards.length;
}

function renderReviewCounts() {
  const rules = state.spec?.rules || [];
  const manual = state.spec?.manual_review || [];
  const unresolved = manual.filter((item) => !item.confirmed).length;
  $("review-count").textContent = `${rules.length} rules · ${unresolved} human check${unresolved === 1 ? "" : "s"}`;
  $("approve").innerHTML = `Approve ${rules.length} rules &amp; continue <span aria-hidden="true">→</span>`;
}

$("review-back").addEventListener("click", () => navigate("upload"));
$("add-rule").addEventListener("click", () => {
  const used = new Set(state.spec.rules.map((rule) => rule.id));
  let number = 1;
  while (used.has(`r${number}`)) number += 1;
  state.spec.rules.push({
    id: `r${number}`,
    type: "MUST_SAY",
    label: "New requirement",
    source_quote: "Added manually during approval.",
    severity: "error",
    needs_review: false,
    phrases: [""],
  });
  markSpecDirty();
  renderReview();
  window.setTimeout(() => document.querySelector(`[data-rule-id="r${number}"] summary`)?.focus(), 40);
});

$("approve").addEventListener("click", async () => {
  clearError();
  clearRuleErrors();
  const button = $("approve");
  button.disabled = true;
  button.textContent = "Approving specification…";
  try {
    const data = await call("/api/spec/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ spec: state.spec }),
    });
    state.specId = data.spec_id;
    state.maxStep = Math.max(state.maxStep, 2);
    $("approval-status").textContent = `${data.rules} rules approved`;
    $("approved-rule-count").textContent = `${data.rules} approved rules`;
    renderTakes();
    show("processing");
  } catch (error) {
    const marked = markRuleErrors(error.message);
    fail(`${error.message}\n${marked ? "Review the highlighted requirement" : "Review the approval set"} and try again.`);
  } finally {
    button.disabled = false;
    renderReviewCounts();
  }
});

/* ============================================================= Check */

function setSelectedTake(takeId) {
  state.lastTake = takeId;
  $("take").value = takeId;
  $("video-file").value = "";
  $("video-file-name").textContent = "Real faster-whisper transcription";
  document.querySelectorAll(".take-option").forEach((item) => {
    const selected = item.dataset.takeId === takeId;
    item.classList.toggle("is-selected", selected);
    item.querySelector("input").checked = selected;
  });
  const selectedTake = state.takes.find((take) => take.id === takeId);
  $("check-summary").textContent = selectedTake?.label || "Choose a take";
  $("run-check").innerHTML = `Verify ${takeId ? takeId.toUpperCase() : "selected cut"} <span aria-hidden="true">→</span>`;
  persistState();
}

function renderTakes() {
  const select = $("take");
  const host = $("take-options");
  select.innerHTML = "";
  host.innerHTML = "";

  if (!state.takes.length) {
    const option = el("option", null, "Upload your media");
    option.value = "";
    select.appendChild(option);
    host.appendChild(el("p", "take-empty", "This custom brief has no committed sample takes. Upload the sponsor cut below."));
    state.lastTake = "";
    $("check-summary").textContent = "No media selected";
    return;
  }

  if (!state.takes.some((take) => take.id === state.lastTake)) state.lastTake = state.takes[0].id;
  state.takes.forEach((take) => {
    const option = el("option", null, take.label);
    option.value = take.id;
    option.selected = take.id === state.lastTake;
    select.appendChild(option);

    const card = el("label", "take-option");
    card.dataset.takeId = take.id;
    card.classList.toggle("is-selected", take.id === state.lastTake);
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "take-card";
    radio.value = take.id;
    radio.checked = take.id === state.lastTake;
    radio.addEventListener("change", () => setSelectedTake(take.id));
    card.appendChild(radio);
    card.appendChild(el("span", "take-index", take.id.toUpperCase()));
    const copy = el("span", "take-copy");
    copy.appendChild(el("strong", null, take.id === "v1" ? "Original cut" : "Corrected cut"));
    copy.appendChild(el("small", null, take.id === "v1" ? "Baseline Aegis VPN sponsor read" : "Revised read after SponsorLint findings"));
    card.appendChild(copy);
    card.appendChild(el("span", "take-state", take.id === "v1" ? "First pass" : "Revision"));
    host.appendChild(card);
  });
  setSelectedTake(state.lastTake);
}

function renderSteps(items) {
  const host = $("steps");
  host.innerHTML = "";
  items.forEach((item) => {
    const row = el("li");
    row.dataset.state = item.state;
    row.appendChild(el("span", "glyph", { done: "✓", active: "◐", pending: "·" }[item.state]));
    row.appendChild(document.createTextNode(item.text));
    host.appendChild(row);
  });
  $("progress-panel").hidden = false;
}

$("back-to-review").addEventListener("click", () => navigate("review"));

$("video-file").addEventListener("change", () => {
  const file = $("video-file").files[0];
  $("video-file-name").textContent = file?.name || "Real faster-whisper transcription";
  if (file) {
    state.lastTake = "";
    document.querySelectorAll(".take-option").forEach((item) => item.classList.remove("is-selected"));
    $("check-summary").textContent = file.name;
    $("run-check").innerHTML = 'Transcribe &amp; verify upload <span aria-hidden="true">→</span>';
    persistState();
  }
});

$("run-check").addEventListener("click", async () => {
  clearError();
  const video = $("video-file").files[0];
  const take = state.lastTake || $("take").value;
  if (!video && !take) {
    fail("Choose V1, V3, or upload a sponsor cut before running verification.");
    return;
  }
  if (!state.specId) {
    fail("The specification needs approval again. Return to Review and approve the current rules.");
    return;
  }

  const form = new FormData();
  form.append("spec_id", state.specId);
  if (video) form.append("video", video);
  else form.append("take", take);

  $("run-state-title").textContent = video ? "Transcribing sponsor cut" : "Verifying committed take";
  renderSteps([
    { state: "done", text: `${state.spec.rules.length} approved requirements loaded` },
    { state: "active", text: video ? "Uploading and transcribing real media" : "Loading committed raw transcript" },
    { state: "pending", text: "Building the evidence report" },
  ]);
  const stopIndicator = animateResolveIndicator();
  const button = $("run-check");
  button.disabled = true;
  button.textContent = "Verification running…";

  try {
    const data = await call("/api/verify", { method: "POST", body: form });
    renderSteps([
      { state: "done", text: `${state.spec.rules.length} approved requirements loaded` },
      { state: "done", text: video ? "Media transcribed with faster-whisper" : "Committed transcript loaded" },
      { state: "done", text: "Evidence report built deterministically" },
    ]);
    state.lastTake = video ? "upload" : take;
    state.lastReport = data.report;
    state.lastReportId = data.report_id;
    state.maxStep = 3;
    renderReport(data.report);
    show("report");
  } catch (error) {
    $("progress-panel").hidden = true;
    fail(`${error.message}\nYour selection and approved rules are preserved. Fix the issue and retry.`);
  } finally {
    stopIndicator();
    button.disabled = false;
    button.innerHTML = 'Verify selected cut <span aria-hidden="true">→</span>';
  }
});

/* ============================================================= Report */

function scoreWithPadding(score) {
  return score.split("/").map((part) => part.padStart(2, "0")).join("/");
}

function renderReport(report) {
  if (!report) return;
  $("report-context").textContent = state.lastTake === "upload" ? "Uploaded sponsor cut" : `${String(state.lastTake).toUpperCase()} / Aegis VPN sample`;
  const verdict = $("verdict");
  verdict.innerHTML = "";
  const banner = el("section", `verdict verdict--${report.state_class}`);
  const main = el("div", "verdict-main");
  const kicker = el("div", "verdict-kicker");
  kicker.appendChild(el("span", "icon", report.icon));
  kicker.appendChild(document.createTextNode(report.status === "DO_NOT_SEND" ? "Blocking send decision" : "Sponsor readiness decision"));
  main.appendChild(kicker);
  main.appendChild(el("h2", null, report.label));
  main.appendChild(el("p", null, report.subline));
  banner.appendChild(main);

  const stats = el("div", "verdict-stats");
  const score = el("div", "verdict-stat");
  score.appendChild(el("strong", null, scoreWithPadding(report.score)));
  score.appendChild(el("span", null, "Automated rules passed"));
  stats.appendChild(score);
  const gate = el("div", "verdict-stat");
  const blockers = Number(report.summary.fail || 0) + Number(report.summary.warn || 0);
  const manualOpen = Number(report.summary.manual_review || 0);
  gate.appendChild(el("strong", null, String(blockers || manualOpen)));
  gate.appendChild(el("span", null, blockers ? "Blocking findings" : manualOpen ? "Human check remaining" : "Open requirements"));
  stats.appendChild(gate);
  banner.appendChild(stats);
  verdict.appendChild(banner);

  const host = $("findings");
  host.innerHTML = "";
  const failures = report.results.filter((result) => ["FAIL", "WARN"].includes(result.status));
  const passes = report.results.filter((result) => result.status === "PASS");

  if (failures.length) {
    const heading = el("div", "findings-heading");
    heading.appendChild(el("h3", null, "Fix these before sending"));
    heading.appendChild(el("span", null, `${failures.length} blocker${failures.length === 1 ? "" : "s"} · strongest evidence first`));
    host.appendChild(heading);
    failures.forEach((result) => host.appendChild(resultCard(result)));
  }

  if (report.manual_review.length) {
    host.appendChild(el("p", "section-label", "◇ Human check · never automated"));
    report.manual_review.forEach((item, index) => host.appendChild(manualReportCard(item, index)));
  }

  if (passes.length) {
    const details = el("details", "passes");
    const summary = el("summary");
    summary.appendChild(document.createTextNode(`${String(passes.length).padStart(2, "0")} automated checks passed`));
    summary.appendChild(el("span", null, "+"));
    details.appendChild(summary);
    const list = el("ul", "pass-list");
    passes.forEach((result) => {
      const row = el("li", "pass-row");
      row.appendChild(el("span", null, "✓"));
      row.appendChild(el("strong", null, result.title));
      row.appendChild(el("small", null, result.timecode || result.detected || "clear"));
      list.appendChild(row);
    });
    details.appendChild(list);
    host.appendChild(details);
  }
}

function resultCard(result) {
  const card = el("article", `result result--${result.chip}`);
  card.appendChild(el("p", "finding-code", `${String(result.rule_id).toUpperCase()} / ${String(result.rule_type).replaceAll("_", " ")}`));
  const head = el("div", "result-head");
  head.appendChild(el("span", "status-word", result.word));
  head.appendChild(el("h3", null, result.title));
  if (result.timecode) head.appendChild(timecodeButton(result.timecode));
  card.appendChild(head);

  if (result.expected || result.detected) {
    const comparison = el("div", "comparison");
    if (result.expected) {
      const expected = el("div");
      expected.appendChild(el("span", null, "Expected"));
      expected.appendChild(el("strong", null, result.expected));
      comparison.appendChild(expected);
    }
    if (result.detected) {
      const detected = el("div", "detected-bad");
      detected.appendChild(el("span", null, "Detected"));
      detected.appendChild(el("strong", null, result.detected));
      comparison.appendChild(detected);
    }
    card.appendChild(comparison);
  }

  if (result.evidence_html) {
    const quote = el("blockquote", "evidence-quote");
    quote.innerHTML = `“${result.evidence_html}”`;
    card.appendChild(quote);
  }
  if (result.advisory) card.appendChild(el("p", "advisory", result.advisory));

  const source = el("dl", "source-grounding");
  source.appendChild(el("dt", null, "Source / brief"));
  source.appendChild(el("dd", null, `“${result.source_quote}”`));
  card.appendChild(source);
  return card;
}

function manualReportCard(item, index) {
  const card = el("article", "result result--manual");
  card.appendChild(el("p", "finding-code", "◇ HUMAN CHECK / VISUAL"));
  const head = el("div", "result-head");
  head.appendChild(el("span", "status-word", item.confirmed ? "CONFIRMED" : "REVIEW"));
  head.appendChild(el("h3", null, item.reason));
  card.appendChild(head);
  const quote = el("blockquote", "evidence-quote", `“${item.source_quote}”`);
  card.appendChild(quote);
  card.appendChild(el("p", "advisory", item.confirmed
    ? "Confirmed by a human during this campaign session."
    : "SponsorLint cannot verify this from the audio transcript or duration."));

  if (!item.confirmed) {
    const action = el("div", "manual-confirm-report");
    action.appendChild(el("p", null, "Inspect the actual video first. Confirmation changes the readiness verdict."));
    const button = el("button", "button button--primary", "Confirm manually");
    button.type = "button";
    button.addEventListener("click", () => confirmManualFromReport(index, button));
    action.appendChild(button);
    card.appendChild(action);
  }
  return card;
}

async function confirmManualFromReport(index, button) {
  clearError();
  if (!state.spec?.manual_review?.[index]) return;
  if (!state.lastReportId) {
    fail("This report is no longer attached to a saved verification run. Check the cut again before confirming the visual item.");
    return;
  }
  const previous = Boolean(state.spec.manual_review[index].confirmed);
  state.spec.manual_review[index].confirmed = true;
  button.disabled = true;
  button.textContent = "Confirming and rechecking…";
  try {
    const data = await call(`/api/report/${encodeURIComponent(state.lastReportId)}/confirm-manual`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ spec: state.spec, index }),
    });
    state.specId = data.spec_id;
    state.lastReportId = data.report_id;
    state.lastReport = data.report;
    renderReport(data.report);
    persistState();
    $("report-title").focus({ preventScroll: true });
  } catch (error) {
    state.spec.manual_review[index].confirmed = previous;
    fail(`${error.message}\nThe manual confirmation was not saved. Retry when the verifier is available.`);
    renderReport(state.lastReport);
  }
}

function timecodeButton(timecode) {
  const button = el("button", "timecode", timecode);
  button.type = "button";
  button.title = "Copy this timecode";
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(timecode);
      button.textContent = "copied";
      window.setTimeout(() => (button.textContent = timecode), 900);
    } catch (_) {
      /* The timecode remains visible when clipboard access is unavailable. */
    }
  });
  return button;
}

$("report-back").addEventListener("click", () => navigate("processing"));
$("check-another").addEventListener("click", () => navigate("processing"));
$("recheck").addEventListener("click", () => navigate("review"));

/* ============================================================= shell UX */

document.querySelectorAll("[data-nav-step]").forEach((button) => {
  button.addEventListener("click", () => navigate(button.dataset.navStep));
});

document.querySelector(".brand").addEventListener("click", (event) => {
  event.preventDefault();
  navigate("upload");
});

window.addEventListener("popstate", (event) => {
  const requested = event.state?.step || HASH_STEP[location.hash.slice(1)] || "upload";
  if (!show(requested, { historyMode: "none" })) show(state.current, { historyMode: "replace", focus: false });
});

const resetDialog = $("reset-dialog");
$("reset-global").addEventListener("click", () => resetDialog.showModal());
$("confirm-reset").addEventListener("click", (event) => {
  event.preventDefault();
  sessionStorage.removeItem(SESSION_KEY);
  resetDialog.close();
  window.location.replace(`${location.pathname}#brief`);
  window.location.reload();
});

function setupDropZone(zoneId, inputId) {
  const zone = $(zoneId);
  const input = $(inputId);
  ["dragenter", "dragover"].forEach((eventName) => {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.add("is-dragging");
    });
  });
  ["dragleave", "drop"].forEach((eventName) => {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.remove("is-dragging");
    });
  });
  zone.addEventListener("drop", (event) => {
    if (!event.dataTransfer?.files?.length) return;
    input.files = event.dataTransfer.files;
    input.dispatchEvent(new Event("change", { bubbles: true }));
  });
}

$("brief-file").addEventListener("change", () => {
  const file = $("brief-file").files[0];
  $("brief-file-name").textContent = file?.name || "or choose PDF, MD, or TXT · up to 10 MiB";
});
setupDropZone("brief-drop-zone", "brief-file");
setupDropZone("video-drop-zone", "video-file");

/* ============================================================= bootstrap */

restoreState();
runTyper();
initGlyphField();

if (state.customBriefOpen) {
  $("custom-brief-panel").hidden = false;
  $("show-custom-brief").setAttribute("aria-expanded", "true");
}
if (state.spec) renderReview();
if (state.specId) renderTakes();
if (state.lastReport) renderReport(state.lastReport);

const requestedStep = HASH_STEP[location.hash.slice(1)] || state.current || "upload";
const initialStep = canAccess(requestedStep) ? requestedStep : canAccess(state.current) ? state.current : "upload";
show(initialStep, { historyMode: "replace", focus: false });

if (window.location.protocol === "file:") {
  const notice = $("error");
  notice.className = "notice notice--info";
  notice.textContent = "Static preview only. Run `python -m sponsorlint serve`, then open http://127.0.0.1:8000 for the working campaign flow.";
  notice.hidden = false;
  ["load-sample", "compile", "run-check", "approve"].forEach((id) => ($(id).disabled = true));
}
