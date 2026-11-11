// The Reclaim plant mascot. mascotSpec() is pure (jsc-tested); draw() builds an SVG element with createElementNS
// (never innerHTML). Classic script: attaches ReclaimMascot to globalThis. Used by popup, reclaimed page, overlay.
(function (root) {
  "use strict";

  const NAMES = ["wilted", "droopy", "sprout", "growing", "blooming"];
  // droop 0..1 bends leaves downward, tilt leans the stem, mouth: -1 frown, 0 flat, 1 smile.
  const SPECS = [
    { name: "wilted", leaves: 2, droop: 1, tilt: -16, leaf: "#A39A58", flower: false, mouth: -1 },
    { name: "droopy", leaves: 2, droop: 0.55, tilt: -7, leaf: "#86A065", flower: false, mouth: -1 },
    { name: "sprout", leaves: 2, droop: 0, tilt: 0, leaf: "#7FB685", flower: false, mouth: 0 },
    { name: "growing", leaves: 4, droop: 0, tilt: 0, leaf: "#6FAE7A", flower: false, mouth: 1 },
    { name: "blooming", leaves: 6, droop: 0, tilt: 0, leaf: "#5E9E6B", flower: true, mouth: 1 },
  ];
  const clampState = (s) => (typeof s === "number" && s >= 0 && s <= 4 ? Math.floor(s) : 2);
  const mascotSpec = (state) => Object.assign({}, SPECS[clampState(state)]);

  const NS = "http://www.w3.org/2000/svg";
  function el(doc, tag, attrs, parent) {
    const e = doc.createElementNS(NS, tag);
    for (const k of Object.keys(attrs || {})) e.setAttribute(k, String(attrs[k]));
    if (parent) parent.appendChild(e);
    return e;
  }

  // 120x120 plant in a terracotta pot with a small face.
  function draw(doc, state, size) {
    const sp = mascotSpec(state);
    const svg = el(doc, "svg", { viewBox: "0 0 120 120", width: size || 96, height: size || 96, role: "img", "aria-label": "Reclaim plant, " + sp.name }, null);
    const topX = 60 + sp.tilt * 0.9, topY = 46 + sp.droop * 10;
    el(doc, "path", { d: "M60 92 Q" + (60 + sp.tilt * 0.2) + " 70 " + topX + " " + topY, stroke: "#4F7C5A", "stroke-width": 4, "stroke-linecap": "round", fill: "none" }, svg);
    const leafPath = "M0 0 C 8 -6 22 -6 28 0 C 22 6 8 6 0 0 Z";
    for (let i = 0; i < sp.leaves; i++) {
      const t = sp.leaves === 1 ? 0.5 : i / (sp.leaves - 1);
      const side = i % 2 === 0 ? 1 : -1;
      const u = 0.2 + t * 0.7; // position along the stem (quadratic curve)
      const cx = 60 + sp.tilt * 0.2;
      const x = (1 - u) * (1 - u) * 60 + 2 * (1 - u) * u * cx + u * u * topX;
      const y = (1 - u) * (1 - u) * 92 + 2 * (1 - u) * u * 70 + u * u * topY;
      const ang = side === 1 ? -25 + sp.droop * 70 : 205 - sp.droop * 70;
      const scale = 0.75 + (1 - t) * 0.35;
      el(doc, "path", { d: leafPath, fill: sp.leaf, stroke: "#4F7C5A", "stroke-width": 1, transform: "translate(" + x.toFixed(1) + " " + y.toFixed(1) + ") rotate(" + ang + ") scale(" + scale.toFixed(2) + ")" }, svg);
    }
    if (sp.flower) {
      const g = el(doc, "g", { transform: "translate(" + topX + " " + (topY - 6) + ")" }, svg);
      for (let k = 0; k < 5; k++) el(doc, "circle", { cx: (Math.cos((k * 72 - 90) * Math.PI / 180) * 7).toFixed(1), cy: (Math.sin((k * 72 - 90) * Math.PI / 180) * 7).toFixed(1), r: 5, fill: "#D9825B" }, g);
      el(doc, "circle", { cx: 0, cy: 0, r: 4, fill: "#F7E3A1" }, g);
    }
    // pot
    el(doc, "path", { d: "M36 92 H84 L79 114 Q78 117 75 117 H45 Q42 117 41 114 Z", fill: "#D9825B" }, svg);
    el(doc, "rect", { x: 32, y: 88, width: 56, height: 9, rx: 4, fill: "#C9714B" }, svg);
    // face
    el(doc, "circle", { cx: 51, cy: 103, r: 2, fill: "#2F3A33" }, svg);
    el(doc, "circle", { cx: 69, cy: 103, r: 2, fill: "#2F3A33" }, svg);
    const m = sp.mouth;
    const d = m > 0 ? "M54 108 Q60 113 66 108" : m < 0 ? "M54 111 Q60 106 66 111" : "M55 109 H65";
    el(doc, "path", { d, stroke: "#2F3A33", "stroke-width": 1.8, "stroke-linecap": "round", fill: "none" }, svg);
    return svg;
  }

  root.ReclaimMascot = { NAMES, mascotSpec, draw };
})(globalThis);
