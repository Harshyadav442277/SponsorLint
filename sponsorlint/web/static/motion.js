/*
 * SponsorLint motion lab.
 *
 * Rendering and lifecycle techniques are adapted from Arlan Marat's MIT
 * licensed Vault experiments: Fade Motion, Dia Gradient, Chromatic Glow, and
 * Kinetic Typography. See /THIRD_PARTY_NOTICES.md. This is a framework-free
 * port using SponsorLint's own text, composition, and palette.
 */

(() => {
  "use strict";

  const reducedQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  const finePointer = window.matchMedia("(pointer: fine)");
  const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
  const lerp = (a, b, amount) => a + (b - a) * amount;

  const pointer = {
    x: 0.5,
    y: 0.42,
    tx: 0.5,
    ty: 0.42,
    active: false,
    lastMove: 0,
  };

  document.addEventListener("pointermove", (event) => {
    pointer.tx = clamp(event.clientX / Math.max(1, window.innerWidth));
    pointer.ty = clamp(event.clientY / Math.max(1, window.innerHeight));
    pointer.active = true;
    pointer.lastMove = performance.now();
  }, { passive: true });

  document.addEventListener("pointerleave", () => {
    pointer.active = false;
  });

  function setupCanvas(canvas, width, height) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const pixelWidth = Math.max(1, Math.round(width * dpr));
    const pixelHeight = Math.max(1, Math.round(height * dpr));
    if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
      canvas.width = pixelWidth;
      canvas.height = pixelHeight;
    }
    return { dpr, width: pixelWidth, height: pixelHeight };
  }

  /* Adapted from Fade Motion's text-mask.ts. The word is rasterized once; all
     animation samples this transparent mask instead of laying out text again. */
  function makeWordMask(word, width, height, fontFamily, weight = 800, anchorY = 0.39) {
    const output = document.createElement("canvas");
    output.width = Math.max(1, Math.round(width));
    output.height = Math.max(1, Math.round(height));
    const context = output.getContext("2d");
    const text = String(word || "").trim();
    if (!context || !text) return output;

    let size = output.height * 0.36;
    const setFont = () => {
      context.font = `${weight} ${size}px ${fontFamily}`;
    };
    setFont();
    const maxWidth = output.width * 0.9;
    const measured = context.measureText(text).width;
    if (measured > maxWidth) {
      size *= maxWidth / measured;
      setFont();
    }

    const metrics = context.measureText(text);
    const ascent = metrics.actualBoundingBoxAscent || size * 0.75;
    const descent = metrics.actualBoundingBoxDescent || size * 0.25;
    const inkMidpoint = (ascent - descent) / 2;
    context.fillStyle = "#fff";
    context.textAlign = "center";
    context.textBaseline = "alphabetic";
    context.fillText(text, output.width / 2, output.height * anchorY + inkMidpoint);
    return output;
  }

  function observeLoop(element, draw, drawStatic) {
    let frame = 0;
    let visible = true;
    let destroyed = false;

    const tick = (now) => {
      if (destroyed) return;
      if (visible && !document.hidden && !reducedQuery.matches) draw(now);
      frame = requestAnimationFrame(tick);
    };

    const observer = new IntersectionObserver((entries) => {
      visible = entries.some((entry) => entry.isIntersecting);
      if (visible && reducedQuery.matches) drawStatic();
    }, { rootMargin: "180px" });
    observer.observe(element);

    const onVisibility = () => {
      if (!document.hidden && reducedQuery.matches) drawStatic();
    };
    document.addEventListener("visibilitychange", onVisibility);
    frame = requestAnimationFrame(tick);
    if (reducedQuery.matches) drawStatic();

    return () => {
      destroyed = true;
      cancelAnimationFrame(frame);
      observer.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }

  class FadeLogo {
    constructor(canvas) {
      this.canvas = canvas;
      this.context = canvas.getContext("2d");
      this.mask = null;
      this.width = 0;
      this.height = 0;
      this.hover = false;
      this.local = { x: 0.5, y: 0.4 };
      this.start = performance.now();
      this.resizeObserver = new ResizeObserver(() => this.resize());
      this.resizeObserver.observe(canvas);

      canvas.addEventListener("pointermove", (event) => {
        const rect = canvas.getBoundingClientRect();
        this.local.x = clamp((event.clientX - rect.left) / Math.max(1, rect.width));
        this.local.y = clamp((event.clientY - rect.top) / Math.max(1, rect.height));
        this.hover = true;
      });
      canvas.addEventListener("pointerleave", () => { this.hover = false; });
      canvas.addEventListener("pointercancel", () => { this.hover = false; });

      this.resize();
      this.stopLoop = observeLoop(canvas, (now) => this.draw(now), () => this.draw(this.start));
    }

    resize() {
      const rect = this.canvas.getBoundingClientRect();
      if (!rect.width || !rect.height || !this.context) return;
      const size = setupCanvas(this.canvas, rect.width, rect.height);
      this.width = size.width;
      this.height = size.height;
      const family = getComputedStyle(document.documentElement).getPropertyValue("--sans") || "system-ui";
      this.mask = makeWordMask("SponsorLint", this.width, this.height, family, 850, 0.36);
    }

    draw(now) {
      const context = this.context;
      if (!context || !this.mask || !this.width || !this.height) return;
      const seconds = (now - this.start) / 1000;
      const ghostX = 0.5 + Math.sin(seconds * 0.73) * 0.27;
      const ghostY = 0.36 + Math.cos(seconds * 0.47) * 0.17;
      const targetX = this.hover ? this.local.x : ghostX;
      const targetY = this.hover ? this.local.y : ghostY;
      const pullX = (targetX - 0.5) * this.width * 0.11;
      const pullY = (targetY - 0.38) * this.height * 0.08;
      const copies = reducedQuery.matches ? 28 : 74;

      context.clearRect(0, 0, this.width, this.height);
      context.save();
      context.globalCompositeOperation = "lighter";

      for (let index = copies - 1; index >= 1; index -= 1) {
        const progress = index / copies;
        const recession = 1 - progress * 0.17;
        const wave = Math.sin(seconds * 1.6 + progress * 10.0) * this.height * 0.012 * progress;
        const x = pullX * progress * progress + wave;
        const y = this.height * 0.42 * progress + pullY * progress;
        const width = this.width * recession;
        const height = this.height * recession;
        context.globalAlpha = 0.008 + (1 - progress) * 0.008;
        context.drawImage(this.mask, (this.width - width) / 2 + x, y, width, height);
      }

      const split = (this.hover ? 1.8 : 1.0) * this.canvas.width / Math.max(1, this.canvas.clientWidth);
      context.globalAlpha = 0.25;
      context.filter = `blur(${Math.max(1, this.height * 0.025)}px)`;
      context.drawImage(this.mask, -split + pullX * 0.04, 0);
      context.globalCompositeOperation = "source-atop";
      context.fillStyle = "#ff705e";
      context.fillRect(0, 0, this.width, this.height);
      context.globalCompositeOperation = "lighter";
      context.globalAlpha = 0.24;
      context.drawImage(this.mask, split - pullX * 0.04, 0);
      context.globalCompositeOperation = "source-atop";
      context.fillStyle = "#c6ff52";
      context.fillRect(0, 0, this.width, this.height);

      context.globalCompositeOperation = "source-over";
      context.globalAlpha = 1;
      context.filter = "none";
      context.drawImage(this.mask, 0, 0);
      context.globalCompositeOperation = "source-in";
      context.fillStyle = "#f3f0e8";
      context.fillRect(0, 0, this.width, this.height);
      context.restore();
    }
  }

  /* Adapted from Kinetic Typography's tile engine. The text is drawn once,
     sliced into a grid, and each tile samples an offset source rectangle from
     two interfering sine waves. */
  class KineticTitle {
    constructor(canvas) {
      this.canvas = canvas;
      this.context = canvas.getContext("2d");
      this.mask = document.createElement("canvas");
      this.maskContext = this.mask.getContext("2d", { willReadFrequently: true });
      this.warp = document.createElement("canvas");
      this.warpContext = this.warp.getContext("2d");
      this.scratch = document.createElement("canvas");
      this.scratchContext = this.scratch.getContext("2d");
      this.width = 0;
      this.height = 0;
      this.dpr = 1;
      this.frame = 0;
      this.box = { x0: 0, y0: 0, x1: 0, y1: 0 };
      this.local = null;
      this.resizeObserver = new ResizeObserver(() => this.resize());
      this.resizeObserver.observe(canvas);
      canvas.addEventListener("pointermove", (event) => {
        const rect = canvas.getBoundingClientRect();
        this.local = {
          x: clamp((event.clientX - rect.left) / Math.max(1, rect.width)),
          y: clamp((event.clientY - rect.top) / Math.max(1, rect.height)),
        };
      });
      canvas.addEventListener("pointerleave", () => { this.local = null; });
      this.resize();
      this.stopLoop = observeLoop(canvas, () => this.renderFrame(), () => this.renderFrame(true));
    }

    resize() {
      const rect = this.canvas.getBoundingClientRect();
      if (!rect.width || !rect.height || !this.context || !this.maskContext || !this.warpContext) return;
      const size = setupCanvas(this.canvas, rect.width, rect.height);
      this.dpr = size.dpr;
      this.width = size.width;
      this.height = size.height;
      for (const canvas of [this.mask, this.warp, this.scratch]) {
        canvas.width = this.width;
        canvas.height = this.height;
      }
      this.drawText();
    }

    drawText() {
      const context = this.maskContext;
      if (!context) return;
      const width = this.width;
      const height = this.height;
      context.clearRect(0, 0, width, height);
      let fontSize = Math.round(height * 0.67);
      const family = getComputedStyle(document.documentElement).getPropertyValue("--sans") || "system-ui";
      const setFont = () => { context.font = `650 ${fontSize}px ${family}`; };
      setFont();
      const text = "Make it executable.";
      while (context.measureText(text).width > width * 0.97 && fontSize > 16) {
        fontSize -= 2;
        setFont();
      }
      context.fillStyle = "#fff";
      context.textAlign = "left";
      context.textBaseline = "middle";
      context.fillText(text, width * 0.01, height * 0.53);
      this.measureBox();
    }

    measureBox() {
      const context = this.maskContext;
      if (!context) return;
      try {
        const data = context.getImageData(0, 0, this.width, this.height).data;
        let x0 = this.width;
        let y0 = this.height;
        let x1 = 0;
        let y1 = 0;
        for (let y = 0; y < this.height; y += 3) {
          for (let x = 0; x < this.width; x += 3) {
            if (data[(y * this.width + x) * 4 + 3] > 20) {
              x0 = Math.min(x0, x);
              y0 = Math.min(y0, y);
              x1 = Math.max(x1, x);
              y1 = Math.max(y1, y);
            }
          }
        }
        this.box = x1 < x0 ? { x0: 0, y0: 0, x1: this.width, y1: this.height } : { x0, y0, x1, y1 };
      } catch (_) {
        this.box = { x0: 0, y0: 0, x1: this.width, y1: this.height };
      }
    }

    compositeTinted(color, offsetX, alpha) {
      const scratch = this.scratchContext;
      const context = this.context;
      if (!scratch || !context) return;
      scratch.globalCompositeOperation = "source-over";
      scratch.globalAlpha = 1;
      scratch.clearRect(0, 0, this.width, this.height);
      scratch.drawImage(this.warp, 0, 0);
      scratch.globalCompositeOperation = "source-in";
      scratch.fillStyle = color;
      scratch.fillRect(0, 0, this.width, this.height);
      context.globalAlpha = alpha;
      context.drawImage(this.scratch, offsetX, 0);
      context.globalAlpha = 1;
    }

    renderFrame(still = false) {
      const context = this.context;
      const warp = this.warpContext;
      if (!context || !warp || !this.width || !this.height) return;
      if (!still) this.frame += 1;
      const local = this.local || {
        x: 0.5 + Math.sin(this.frame * 0.009) * 0.28,
        y: 0.5 + Math.cos(this.frame * 0.007) * 0.22,
      };
      const energy = this.local ? 1.15 : 0.62;
      const offset = this.height * 0.065 * energy;
      const tilesX = this.width < 700 ? 24 : 34;
      const tilesY = Math.max(5, Math.round(tilesX / 5.8));
      const tileWidth = Math.floor(this.width / tilesX);
      const tileHeight = Math.floor(this.height / tilesY);

      warp.clearRect(0, 0, this.width, this.height);
      const cx0 = Math.max(0, Math.floor(this.box.x0 / tileWidth) - 1);
      const cy0 = Math.max(0, Math.floor(this.box.y0 / tileHeight) - 1);
      const cx1 = Math.min(tilesX - 1, Math.ceil(this.box.x1 / tileWidth) + 1);
      const cy1 = Math.min(tilesY - 1, Math.ceil(this.box.y1 / tileHeight) + 1);
      const time = still ? 0.8 : this.frame * 0.022;

      for (let y = cy0; y <= cy1; y += 1) {
        for (let x = cx0; x <= cx1; x += 1) {
          const phase = x * y;
          const waveA = Math.sin(time + phase * 0.025 + local.x * 2.4);
          const waveB = Math.sin(time * 0.7 + (x + y) * 0.047 + local.y * 2.1 + 1.3);
          const mix = waveA * 0.65 + waveB * 0.45;
          const waveX = Math.round(mix * offset + (local.x - 0.5) * offset * 0.45);
          const waveY = Math.round(Math.sin(time * 0.9 + phase * 0.015) * offset * 0.48);
          const sourceX = x * tileWidth + waveX;
          const sourceY = y * tileHeight + waveY;
          const destX = x * tileWidth;
          const destY = y * tileHeight;
          const drawWidth = x === tilesX - 1 ? this.width - destX : tileWidth;
          const drawHeight = y === tilesY - 1 ? this.height - destY : tileHeight;
          if (drawWidth <= 0 || drawHeight <= 0) continue;
          if (sourceX + drawWidth <= 0 || sourceY + drawHeight <= 0 || sourceX >= this.width || sourceY >= this.height) continue;
          warp.globalAlpha = 0.82 + Math.min(1, Math.abs(mix)) * 0.18;
          warp.drawImage(this.mask, sourceX, sourceY, drawWidth, drawHeight, destX, destY, drawWidth, drawHeight);
        }
      }
      warp.globalAlpha = 1;

      context.clearRect(0, 0, this.width, this.height);
      context.globalCompositeOperation = "lighter";
      const split = Math.round((this.local ? 5 : 3) * this.dpr);
      context.filter = `blur(${Math.max(0.6, this.dpr * 0.55)}px)`;
      this.compositeTinted("#ff705e", split, 0.34);
      this.compositeTinted("#c6ff52", -split, 0.42);
      context.filter = `blur(${Math.max(1, this.dpr * 1.8)}px)`;
      this.compositeTinted("#c6ff52", 0, 0.16);
      context.filter = "none";
      context.globalCompositeOperation = "source-over";
      this.compositeTinted("#c5c2b9", 0, 1);
    }
  }

  /* Copied and ported from DiaGradient.tsx: a power-falloff bell makes the
     center bars tallest while keeping the edges deliberately substantial. */
  function bellHeights(count, peak, valley, height) {
    const output = [];
    const midpoint = (count - 1) / 2;
    for (let index = 0; index < count; index += 1) {
      const distance = midpoint === 0 ? 0 : Math.abs(index - midpoint) / midpoint;
      const eased = 1 - Math.pow(distance, 1.24);
      output.push(peak * height * (valley + (1 - valley) * eased));
    }
    return output;
  }

  class AmbientAurora {
    constructor(host) {
      this.host = host;
      this.start = performance.now();
      this.build();
      this.frame = requestAnimationFrame((now) => this.draw(now));
    }

    build() {
      const namespace = "http://www.w3.org/2000/svg";
      const width = 1271;
      const height = 599;
      const bars = 9;
      const svg = document.createElementNS(namespace, "svg");
      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      svg.setAttribute("preserveAspectRatio", "none");
      const defs = document.createElementNS(namespace, "defs");
      const gradient = document.createElementNS(namespace, "linearGradient");
      gradient.id = "sponsorlint-aurora-gradient";
      gradient.setAttribute("x1", "0");
      gradient.setAttribute("y1", "1");
      gradient.setAttribute("x2", "0");
      gradient.setAttribute("y2", "0");
      [
        [0, "#101b0b"],
        [0.18, "#315c25"],
        [0.34, "#c6ff52"],
        [0.5, "#f3f0e8"],
        [0.66, "#e0b05e"],
        [0.82, "#ff705e"],
        [1, "#ff705e00"],
      ].forEach(([offset, color]) => {
        const stop = document.createElementNS(namespace, "stop");
        stop.setAttribute("offset", String(offset));
        stop.setAttribute("stop-color", color);
        gradient.appendChild(stop);
      });
      const filter = document.createElementNS(namespace, "filter");
      filter.id = "sponsorlint-aurora-blur";
      filter.setAttribute("x", "-30%");
      filter.setAttribute("y", "-30%");
      filter.setAttribute("width", "160%");
      filter.setAttribute("height", "160%");
      const blur = document.createElementNS(namespace, "feGaussianBlur");
      blur.setAttribute("stdDeviation", "18");
      filter.appendChild(blur);
      defs.appendChild(gradient);
      defs.appendChild(filter);
      svg.appendChild(defs);

      const heights = bellHeights(bars, 0.98, 0.53, height);
      const columnWidth = width / bars;
      heights.forEach((barHeight, index) => {
        const rect = document.createElementNS(namespace, "rect");
        rect.setAttribute("x", String(index * columnWidth - 7));
        rect.setAttribute("y", String(height - barHeight));
        rect.setAttribute("width", String(columnWidth + 14));
        rect.setAttribute("height", String(barHeight));
        rect.setAttribute("fill", "url(#sponsorlint-aurora-gradient)");
        rect.setAttribute("filter", "url(#sponsorlint-aurora-blur)");
        svg.appendChild(rect);
      });
      this.host.replaceChildren(svg);
    }

    draw = (now) => {
      const seconds = (now - this.start) / 1000;
      pointer.x = lerp(pointer.x, pointer.tx, 0.075);
      pointer.y = lerp(pointer.y, pointer.ty, 0.075);
      const rise = reducedQuery.matches ? 0.7 : 1 - Math.exp(-seconds * 2.8);
      const breathe = reducedQuery.matches ? 0 : Math.sin(seconds * 0.62) * 0.045;
      const shift = (pointer.x - 0.5) * 34;
      const lean = (pointer.x - 0.5) * 2.6;
      this.host.style.setProperty("--aurora-rise", String(clamp(rise + breathe, 0, 1.06)));
      this.host.style.setProperty("--aurora-shift", `${shift}px`);
      this.host.style.setProperty("--aurora-lean", `${lean}deg`);
      this.frame = requestAnimationFrame(this.draw);
    };
  }

  class SpectralCursor {
    constructor(element) {
      this.element = element;
      this.x = window.innerWidth / 2;
      this.y = window.innerHeight * 0.42;
      this.frame = requestAnimationFrame(() => this.draw());
    }

    draw = () => {
      const targetX = pointer.active ? pointer.tx * window.innerWidth : window.innerWidth * (0.5 + Math.sin(performance.now() * 0.00019) * 0.18);
      const targetY = pointer.active ? pointer.ty * window.innerHeight : window.innerHeight * 0.62;
      this.x = lerp(this.x, targetX, pointer.active ? 0.16 : 0.025);
      this.y = lerp(this.y, targetY, pointer.active ? 0.16 : 0.025);
      this.element.style.transform = `translate3d(${this.x}px, ${this.y}px, 0)`;
      this.element.classList.toggle("is-active", pointer.active && finePointer.matches && !reducedQuery.matches);
      this.frame = requestAnimationFrame(this.draw);
    };
  }

  function init() {
    const logo = document.getElementById("brand-fade");
    const kinetic = document.getElementById("kinetic-title");
    const aurora = document.getElementById("ambient-aurora");
    const cursor = document.getElementById("spectral-cursor");
    if (logo) new FadeLogo(logo);
    if (kinetic) new KineticTitle(kinetic);
    if (aurora) new AmbientAurora(aurora);
    if (cursor) new SpectralCursor(cursor);
  }

  window.SponsorLintMotion = { pointer, reducedQuery };
  init();
})();
