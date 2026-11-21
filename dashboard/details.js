/* Details page: everything found inside the library. Plain JS, no build step.
   Tabs: Everything, People, Faces, Screenshots, Money, Documents, Videos. Data comes from /api/details. */
const $ = id => document.getElementById(id);
const DEMO = new URLSearchParams(location.search).has("demo") || !!window.STATIC_DEMO;  // made-up library, no server
const BASE = DEMO ? "demo/" : "data/";
const fmt = n => n == null ? "" : Math.round(n).toLocaleString("en-US");
const money = n => n == null ? "" : n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const size = b => b >= 1e9 ? (b / 1e9).toFixed(1) + " GB" : b >= 1e6 ? (b / 1e6).toFixed(1) + " MB" : Math.round(b / 1e3) + " KB";
const pid = n => "P" + String(n).padStart(4, "0");
const fid = n => "F" + String(n).padStart(5, "0");
const el = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (k === "style") e.style.cssText = v;
    else if (v !== false && v != null) e.setAttribute(k, v === true ? "" : v);
  }
  for (const k of kids.flat()) if (k != null && k !== false) e.append(k.nodeType ? k : document.createTextNode(k));
  return e;
};
const ICONS = {
  sort: '<path d="M4 20h16"/><path d="m6 16 3-8 3 8"/><path d="M7 13h4"/><path d="M15 8h5l-5 8h5"/>',
  library: '<path d="m16 6 4 14"/><path d="M12 6v14"/><path d="M8 8v12"/><path d="M4 4v16"/>',
  share: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4"/><path d="m15.4 6.5-6.8 4"/>',
  grid: '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9"/><path d="M16 3.1a4 4 0 0 1 0 7.8"/>',
  scan: '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><path d="M9 9h.01"/><path d="M15 9h.01"/>',
  home: '<path d="M3 10.2 12 3l9 7.2V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  pulse: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
  party: '<path d="M5.8 11.3 2 22l10.7-3.8"/><path d="M4 3h.01"/><path d="M22 8h.01"/><path d="M15 2h.01"/><path d="M22 20h.01"/><path d="M11 13c1.9 1.9 2.8 4.1 2 4.9-.8.8-3-.1-4.9-2-1.9-1.9-2.8-4.1-2-4.9.8-.8 3 .1 4.9 2Z"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  phone: '<rect width="14" height="20" x="5" y="2" rx="2"/><path d="M12 18h.01"/>',
  wallet: '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
  file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/>',
  film: '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18"/><path d="M3 12h18"/><path d="M17 3v18"/>',
  shield: '<path d="M20 13c0 5-3.5 7.5-7.7 9a1 1 0 0 1-.6 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.7a1.2 1.2 0 0 1 1.6 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1z"/>',
  bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>',
  images: '<rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>',
  left: '<path d="m15 18-6-6 6-6"/>', x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
  moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
  reveal: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
};
const svg = n => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[n]}</svg>`;
const icon = n => { const s = el("span", { "data-icon": n }); s.innerHTML = svg(n); return s; };
const paintIcons = (root = document) => root.querySelectorAll("[data-icon]").forEach(e => { if (!e.firstChild) e.innerHTML = svg(e.dataset.icon); });
function toast(t) { const e = $("toast"); e.textContent = t; e.classList.add("on"); clearTimeout(e.t); e.t = setTimeout(() => e.classList.remove("on"), 3200); }
async function api(path, body) {
  if (DEMO) return demoApi(path, body);
  const r = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : { cache: "no-store" });
  const j = await r.json();
  if (j && j.error) { toast(j.error); throw new Error(j.error); }
  return j;
}

/* theme, shared with the sorting page */
function setTheme(t) {
  document.documentElement.dataset.theme = t;
  $("theme").innerHTML = svg(t === "dark" ? "sun" : "moon");
  try { localStorage.setItem("theme", t); } catch (e) {}
}
let theme = "light";
try { theme = localStorage.getItem("theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"); } catch (e) {}
setTheme(theme);
$("theme").onclick = () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");

/* ---------- data ---------- */
let D = { files: [], faces: [], people: [] }, byFile = {}, byPerson = {}, byFace = {};
const ui = { tab: "all", q: "", sort: null, desc: false, shown: 200, kind: "", minPhotos: 1, merge: null, who: [], mood: "" };
try { Object.assign(ui, JSON.parse(sessionStorage.getItem("details-ui") || "{}"), { merge: null, shown: 200 }); } catch (e) {}
const remember = () => { try { sessionStorage.setItem("details-ui", JSON.stringify({ tab: ui.tab, minPhotos: ui.minPhotos, who: ui.who, mood: ui.mood, tag: ui.tag, tl: ui.tl })); } catch (e) {} };

/* ---------- moods: estimated emotions per face, summed up per photo ---------- */
const EMOJI = { happy: "😊", neutral: "😐", surprised: "😮", sad: "😢", angry: "😠", disgusted: "🤢", scared: "😨", contempt: "😒" };
function feelings(f) { return f.face_ids.map(i => byFace[i]).filter(x => x && x.emotion); }
function mood(f) {  // the most common emotion among the faces in this file (estimated)
  const fs = feelings(f);
  if (!fs.length) return "";
  const n = {};
  fs.forEach(x => n[x.emotion] = (n[x.emotion] || 0) + 1);
  return Object.entries(n).sort((a, b) => b[1] - a[1] || (a[0] === "happy" ? -1 : 1))[0][0];
}
function moodTag(f) {
  const m = mood(f), fs = feelings(f);
  if (!m) return f.face_ids.length ? el("span", { class: "tag un" }, "faces too small") : "";
  const k = fs.filter(x => x.emotion === m).length;
  return el("span", { class: "tag mood", title: "Estimated by a computer model" }, `${EMOJI[m] || ""} ${m}${fs.length > 1 ? ` (${k} of ${fs.length})` : ""}`);
}
const whoFeels = f => feelings(f).map(x => `${x.person}: ${EMOJI[x.emotion] || ""} ${x.emotion}`).join(" · ");

async function load() {
  if (DEMO && D.people.length) { indexes(); kpis(); tabs(); render(); return; }  // the demo keeps edits in memory
  fromHash();
  try { D = DEMO ? await fetch(BASE + "details.json").then(r => r.json()) : await api("/api/details"); }
  catch (e) { $("view").replaceChildren(el("p", { class: "mx-empty" }, "Nothing to show yet. Go back and sort a folder first.")); return; }
  indexes(); D._events = null;
  $("source").textContent = (D.source.source || "").replace(/^\/Users\/[^/]+/, "~") + (DEMO ? " · demo: drawn pictures, made-up people" : "");
  kpis(); tabs(); render();
}
function indexes() {
  byFile = Object.fromEntries(D.files.map(f => [f.id, f]));
  byPerson = Object.fromEntries(D.people.map(p => [p.person_id, p]));
  byFace = Object.fromEntries(D.faces.map(f => [f.face_id, f]));
}
const thumb = f => `${BASE}thumbs/${f.id}.jpg`;
const faceImg = id => `${BASE}faces/${id}.jpg`;
const personName = id => byPerson[id] ? byPerson[id].display : "";

function kpis() {
  const k = { photo: 0, video: 0, doc: 0 };
  D.files.forEach(f => k[f.kind]++);
  const un = D.files.filter(f => f.people === "un").length;
  const items = [["Files", D.files.length, size(D.files.reduce((s, f) => s + f.bytes, 0))], ["Photos", k.photo], ["Videos", k.video],
    ["Documents", k.doc], ["People", D.people.length, `${D.people.filter(p => p.name).length} named`], ["Faces", D.faces.length],
    ["Screenshots", D.files.filter(f => f.screenshot).length], ["No face (un)", un]];
  $("kpis").replaceChildren(...items.map(([h, v, s]) => el("div", { class: "mx-kpi" }, el("h3", {}, h), el("b", {}, fmt(v)), el("small", {}, s || " "))));
}

/* sections: [key, link name (#everything...), label, icon, count, group] */
const TABS = [
  ["all", "everything", "Everything", "grid", () => D.files.length, "Library"],
  ["shots", "screenshots", "Screenshots", "phone", () => D.files.filter(f => f.screenshot).length, "Library"],
  ["money", "money", "Money", "wallet", () => D.files.filter(f => f.amount && !f.duplicate_of).length, "Library"],
  ["docs", "documents", "Documents", "file", () => D.files.filter(f => f.kind === "doc").length, "Library"],
  ["videos", "videos", "Videos", "film", () => D.files.filter(f => f.kind === "video").length, "Library"],
  ["people", "people", "People", "users", () => D.people.length, "People"],
  ["faces", "faces", "Faces", "scan", () => D.faces.length, "People"],
  ["family", "family", "Family", "home", () => D.people.filter(p => p.family).length, "People"],
  ["timeline", "timeline", "Timeline", "pulse", () => D.people.filter(p => p.name).length, "People"],
  ["events", "events", "Events", "party", () => events().length, "People"],
  ["search", "face-search", "Face search", "search", () => "", "People"],
  ["requests", "requests", "Requests & alerts", "bell", () => (D.requests || []).filter(r => r.status === "pending").length + (D.alerts || []).filter(a => !a.seen && a.kind !== "delete request").length || "", "Sharing"],
  ["privacy", "privacy", "Privacy", "shield", () => (D.alerts || []).filter(a => !a.seen && a.kind === "delete request").length || "", "Sharing"],
];
const TAB = Object.fromEntries(TABS.map(t => [t[0], t]));
function tabs() {
  const groups = [...new Set(TABS.map(t => t[5]))];
  $("tabs").replaceChildren(...groups.map(g => el("div", { class: "side-group" }, el("h4", {}, g),
    TABS.filter(t => t[5] === g).map(([k, slug, label, ic, n]) => {
      const c = n();
      return el("a", { href: "#" + slug, class: "side-item" + ((k === "requests" || k === "privacy") && c ? " alert" : ""), "aria-current": ui.tab === k ? "page" : false, onclick: e => {
        e.preventDefault();
        Object.assign(ui, { tab: k, sort: null, desc: false, shown: 200, q: "", fam: null, ev: null }); remember(); tabs(); render();
        document.querySelector(".side-item[aria-current]")?.scrollIntoView({ block: "nearest", inline: "nearest" });
      } }, icon(ic), el("span", { class: "side-label" }, label), c === "" ? null : el("em", {}, fmt(c)));
    }))),
    el("div", { class: "side-group side-links" }, el("h4", {}, "Also"),
      el("a", { class: "side-item", href: "share.html", target: "_blank", rel: "noopener" }, icon("share"), el("span", { class: "side-label" }, "Open the sharing app"), el("em", {}, "↗")),
      el("a", { class: "side-item", href: "./" }, icon("sort"), el("span", { class: "side-label" }, "Sort more photos"))));
  $("title").textContent = TAB[ui.tab] ? TAB[ui.tab][2] : "Library";
  document.title = `${$("title").textContent} · Library`;
  paintIcons($("tabs"));
}

/* links: #everything, #family/3, #timeline/5, #events/0 ... the back button and bookmarks work */
const SUB = { family: "fam", timeline: "tl", events: "ev" };
function hashFor() {
  const t = TAB[ui.tab]; if (!t) return "";
  const sub = SUB[ui.tab] && ui[SUB[ui.tab]] != null ? "/" + ui[SUB[ui.tab]] : "";
  return "#" + t[1] + sub;
}
function setHash() { const h = hashFor(); if (h && location.hash !== h) history.pushState(null, "", h); }
function fromHash() {
  const [slug, sub] = decodeURIComponent(location.hash.slice(1)).split("/");
  const t = TABS.find(x => x[1] === slug);
  if (!t) return false;
  ui.tab = t[0];
  if (SUB[ui.tab]) ui[SUB[ui.tab]] = sub == null || sub === "" ? null : sub === "unsure" ? "unsure" : +sub;
  return true;
}
addEventListener("popstate", () => { if (fromHash() && D.files.length) { remember(); tabs(); render(); } });

/* ---------- toolbar ---------- */
function toolbar(extra = [], note = null) {
  const q = el("input", { class: "field", type: "search", placeholder: "Search names, people, companies, text…", value: ui.q });
  q.oninput = () => { ui.q = q.value; ui.shown = 200; renderBody(); };
  $("toolbar").replaceChildren(q, ...extra, el("span", { class: "spacer" }), note || "");
  return q;
}
const match = (f, q) => !q || [f.name, f.people, f.company, f.content, f.tags, f.folder, f.text, f.camera, f.txn_ids,
  ...(f.people_ids || []).map(pid), ...(f.face_ids || []).map(fid)].join(" ").toLowerCase().includes(q.toLowerCase());

/* ---------- generic sortable table ---------- */
function table(rows, cols) {
  if (ui.sort != null) {
    const c = cols.find(c => c.k === ui.sort);
    if (c) {
      const v = r => c.v ? c.v(r) : r[c.k];
      rows = rows.slice().sort((a, b) => { const x = v(a), y = v(b); return (x == null || x === "") - (y == null || y === "") || (x < y ? -1 : x > y ? 1 : 0) * (ui.desc ? -1 : 1); });
    }
  }
  const head = el("tr", {}, cols.map(c => el("th", { onclick: () => { if (!c.k) return; ui.desc = ui.sort === c.k ? !ui.desc : false; ui.sort = c.k; renderBody(); } },
    c.h, ui.sort === c.k ? el("span", { class: "arr" }, ui.desc ? "↓" : "↑") : null)));
  const body = rows.slice(0, ui.shown).map(r => el("tr", {}, cols.map(c => {
    const td = el("td", { class: c.cls || "" });
    const v = c.r ? c.r(r) : r[c.k];
    if (v != null) td.append(...[v].flat().map(x => x && x.nodeType ? x : document.createTextNode(x)));
    if (typeof v === "string" && v.length > 30) td.title = v;
    return td;
  })));
  const wrap = el("div", { class: "tbl-wrap" }, el("table", { class: "dtable" }, el("thead", {}, head), el("tbody", {}, body)));
  const parts = [wrap];
  if (rows.length > ui.shown) parts.push(el("div", { class: "more-row" }, el("button", { class: "mx-btn small", onclick: () => { ui.shown += 500; renderBody(); } }, `Show more (${fmt(rows.length - ui.shown)} left)`)));
  if (!rows.length) parts.splice(0, 1, el("p", { class: "mx-empty" }, "Nothing here."));
  return parts;
}
const T = {  // reusable columns
  thumb: { h: "", r: f => el("img", { class: "thumb", src: thumb(f), loading: "lazy", alt: "", onclick: () => viewer(f) }) },
  id: { h: "ID", k: "id", cls: "num" },
  name: { h: "Name", k: "name" },
  kind: { h: "Type", k: "kind" },
  folder: { h: "Folder", k: "folder" },
  taken: { h: "Date", k: "taken" },
  people: { h: "People", k: "people", r: f => f.people === "un" ? el("span", { class: "tag un" }, "un") : f.people_ids.map(i => el("span", { class: "tag" }, personName(i))) },
  pids: { h: "Person IDs", k: "pids", v: f => f.people_ids.join(","), r: f => f.people_ids.length ? f.people_ids.map(pid).join(", ") : "un" },
  fids: { h: "Face IDs", k: "fids", v: f => f.face_ids.length, r: f => f.face_ids.map(fid).join(", ") },
  labels: { h: "Tags", k: "labels", v: f => (f.labels || []).join(" "), cls: "tags-cell", r: f => (f.labels || []).slice(0, 8).map(t =>
    el("button", { class: "tag tagbtn" + (ui.tag === t ? " on" : ""), onclick: e => { e.stopPropagation(); ui.tag = ui.tag === t ? "" : t; remember(); render(); } }, t)) },
  mood: { h: "Mood (est.)", k: "mood", v: f => mood(f), r: moodTag },
  feels: { h: "Who feels what (est.)", k: "feels", v: whoFeels, r: whoFeels },
  ests: { h: "Age · gender · emotion (est.)", r: f => f.face_ids.map(i => byFace[i]).filter(x => x && x.age).map(x => `${x.age} ${x.gender || ""} ${x.emotion || ""}`).join(" | ") },
  tags: { h: "Things in it", k: "tags" },
  company: { h: "Company / app", k: "company" },
  content: { h: "What it is", k: "content" },
  amount: { h: "Amount", k: "amount", cls: "num", r: f => f.amount == null ? "" : el("span", { class: f.direction }, (f.direction === "out" ? "−" : f.direction === "in" ? "+" : "") + money(f.amount) + (f.currency ? " " + f.currency : "")) },
  txn: { h: "Transaction / order IDs", k: "txn_ids" },
  camera: { h: "Camera / phone", k: "camera" },
  size: { h: "Size", k: "bytes", cls: "num", r: f => size(f.bytes) },
  gps: { h: "GPS", k: "lat", r: f => f.lat == null ? "" : el("a", { href: `https://maps.google.com/?q=${f.lat},${f.lon}`, target: "_blank", rel: "noopener" }, `${f.lat.toFixed(4)}, ${f.lon.toFixed(4)}`) },
  dup: { h: "Duplicate of", k: "duplicate_of" },
  text: { h: "Text (start)", k: "text", cls: "wrap", r: f => (f.text || "").slice(0, 160) },
  length: { h: "Length", k: "duration", cls: "num", r: f => f.duration ? Math.round(f.duration) + " s" : "" },
};

/* ---------- views ---------- */
let renderBody = () => {};
function render() {
  $("view").replaceChildren();
  $("kpis").hidden = !["all", "shots", "money", "docs", "videos"].includes(ui.tab);
  if (!SUB[ui.tab]) setHash();
  ({ privacy: viewPrivacy, all: viewAll, family: viewFamily, timeline: viewTimeline, events: viewEvents, search: viewFaceSearch, requests: viewRequests, people: viewPeople, faces: viewFaces, shots: viewShots, money: viewMoney, docs: viewDocs, videos: viewVideos })[ui.tab]();
}
function simple(filter, cols, extra = [], note = null) {
  toolbar(extra, note);
  renderBody = () => $("view").replaceChildren(...table(D.files.filter(f => filter(f) && match(f, ui.q)), cols));
  renderBody();
}
/* filters shared by Everything and Videos: people in the photo (all of them) and mood */
const filterPeopleMood = f => (!ui.tag || (f.labels || []).includes(ui.tag)) && ui.who.every(id => f.people_ids.includes(id)) &&
  (!ui.mood || (ui.mood === "un" ? !f.face_ids.length : feelings(f).some(x => x.emotion === ui.mood)));
function peopleMoodControls() {
  const known = D.people.filter(p => (p.name || p.photos + p.videos > 1) && !ui.who.includes(p.person_id))
    .sort((a, b) => (!!b.name - !!a.name) || (b.photos + b.videos) - (a.photos + a.videos));
  const add = el("select", { class: "mx-select", "aria-label": "Show photos of a person", onchange: e => {
    if (e.target.value) { ui.who.push(+e.target.value); ui.shown = 200; remember(); render(); }
  } }, el("option", { value: "" }, ui.who.length ? "+ and also…" : "Photos of… (pick a person)"),
    known.map(p => el("option", { value: p.person_id }, `${p.display} · ${pid(p.person_id)} (${p.photos + p.videos})`)));
  const chips = ui.who.map(id => el("button", { class: "chip-btn", "aria-pressed": "true", title: "Remove", onclick: () => {
    ui.who = ui.who.filter(x => x !== id); remember(); render();
  } }, el("img", { src: byPerson[id] && byPerson[id].cover ? faceImg(byPerson[id].cover) : "", alt: "" }), personName(id) || pid(id), " ✕"));
  const moods = el("select", { class: "mx-select", "aria-label": "Mood", onchange: e => { ui.mood = e.target.value; remember(); renderBody(); } },
    [["", "Any mood"], ...Object.keys(EMOJI).map(k => [k, `${EMOJI[k]} someone ${k}`]), ["un", "No face (un)"]]
      .map(([v, t]) => el("option", { value: v, selected: ui.mood === v }, t)));
  const counts = {};
  D.files.forEach(f => (f.labels || []).forEach(t => counts[t] = (counts[t] || 0) + 1));
  const tagSel = el("select", { class: "mx-select", "aria-label": "Tag", onchange: e => { ui.tag = e.target.value; remember(); render(); } },
    el("option", { value: "" }, "Any tag"), Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([t, n]) => el("option", { value: t, selected: ui.tag === t }, `${t} (${fmt(n)})`)));
  return [add, ...chips, moods, tagSel];
}
function viewAll() {
  const kind = el("select", { class: "mx-select", "aria-label": "Type", onchange: e => { ui.kind = e.target.value; renderBody(); } },
    [["", "All types"], ["photo", "Photos"], ["video", "Videos"], ["doc", "Documents"]].map(([v, t]) => el("option", { value: v, selected: ui.kind === v }, t)));
  simple(f => (!ui.kind || f.kind === ui.kind) && filterPeopleMood(f),
    [T.thumb, T.id, T.name, T.kind, T.folder, T.taken, T.people, T.labels, T.mood, T.feels, T.pids, T.fids, T.ests, T.tags, T.company, T.content, T.amount, T.camera, T.size, T.gps, T.dup],
    [kind, ...peopleMoodControls()], el("span", { class: "meta" }, ui.who.length > 1 ? "Showing photos with all of these people together." : "Moods are estimates. \"un\" means no face was found."));
}
function viewShots() { simple(f => f.screenshot, [T.thumb, T.id, T.name, T.taken, T.company, { h: "Sector", k: "sector" }, T.content, T.amount, T.txn, T.tags, T.text, T.folder]); }
function viewDocs() { simple(f => f.kind === "doc", [T.thumb, T.id, T.name, { h: "Type", k: "ext" }, T.content, T.company, T.amount, T.txn, T.size, T.folder, T.text]); }
function viewVideos() { simple(f => f.kind === "video" && filterPeopleMood(f), [T.thumb, T.id, T.name, T.taken, T.length, T.camera, T.people, T.mood, T.feels, T.pids, T.tags, T.size, T.folder, T.gps], peopleMoodControls()); }
function viewMoney() {
  const rows = () => D.files.filter(f => f.amount && !f.duplicate_of && match(f, ui.q));
  const sums = el("span", { class: "meta" });
  toolbar([], sums);
  renderBody = () => {
    const r = rows(), tot = {};
    r.forEach(f => { const k = (f.currency || "?") + " " + (f.direction || "?"); tot[k] = (tot[k] || 0) + f.amount; });
    sums.textContent = Object.entries(tot).map(([k, v]) => `${k.replace("?", "").replace(" out", " out:").replace(" in", " in:")} ${money(v)}`).join("  ·  ") + "  (read from pictures: check important ones)";
    $("view").replaceChildren(...table(r, [T.taken, T.company, { h: "Sector", k: "sector" }, T.content, T.amount, T.txn,
      { h: "From", k: "kind", r: f => f.screenshot ? "screenshot" : f.kind }, T.thumb, T.name]));
  };
  renderBody();
}

/* people */
function viewPeople() {
  const min = el("select", { class: "mx-select", "aria-label": "Show people seen in", onchange: e => { ui.minPhotos = +e.target.value; remember(); renderBody(); } },
    [[1, "Everyone"], [2, "Seen in 2+ files"], [5, "Seen in 5+ files"], [0, "Named only"]].map(([v, t]) => el("option", { value: v, selected: ui.minPhotos === v }, t)));
  const mergeBtn = el("button", { class: "mx-btn small", onclick: () => { ui.merge = ui.merge ? null : new Set(); renderBody(); } });
  toolbar([min, mergeBtn], el("span", { class: "meta" }, "Same person twice? Press Merge, tick both, then Merge selected."));
  renderBody = () => {
    mergeBtn.textContent = ui.merge ? "Cancel merge" : "Merge people";
    const list = D.people.filter(p => (ui.minPhotos === 0 ? p.name : p.photos + p.videos >= ui.minPhotos)
      && (!ui.q || `${p.display} ${pid(p.person_id)} ${p.mobile || ""}`.toLowerCase().includes(ui.q.toLowerCase())));
    const parts = [];
    if (ui.merge) parts.push(el("div", { class: "toolbar" }, el("span", { class: "meta" }, `${ui.merge.size} selected. The first one you ticked keeps its number.`),
      el("button", { class: "mx-btn small solid", disabled: ui.merge.size < 2, onclick: doMerge }, "Merge selected")));
    parts.push(list.length ? el("div", { class: "people" }, list.slice(0, ui.shown).map(personCard)) : el("p", { class: "mx-empty" }, "No people found yet."));
    if (list.length > ui.shown) parts.push(el("div", { class: "more-row" }, el("button", { class: "mx-btn small", onclick: () => { ui.shown += 300; renderBody(); } }, "Show more")));
    $("view").replaceChildren(...parts);
  };
  renderBody();
}
function personCard(p) {
  const sel = ui.merge && ui.merge.has(p.person_id);
  return el("div", { class: "pcard" + (sel ? " sel" : ""), onclick: () => {
      if (ui.merge) { sel ? ui.merge.delete(p.person_id) : ui.merge.add(p.person_id); renderBody(); } else personDrawer(p);
    } },
    ui.merge ? el("input", { type: "checkbox", class: "pick", checked: sel, "aria-label": "Select" }) : null,
    el("img", { src: p.cover ? faceImg(p.cover) : "", alt: "", loading: "lazy" }),
    el("b", {}, p.display), el("span", { class: "pid" }, pid(p.person_id)),
    el("span", { class: "stats" }, `${fmt(p.photos)} photos · ${fmt(p.videos)} videos`),
    p.age_est != null ? el("span", { class: "est" }, `~${p.age_est} yrs · ${p.gender_est} · usually ${p.emotion_usual} (est.)`) : null,
    el("div", { class: "badges" }, p.name ? el("span", { class: "tag yes" }, "registered") : el("span", { class: "tag" }, "not registered"),
      p.mobile ? el("span", { class: "tag" }, "📱 " + p.mobile) : null,
      p.consent !== "pending" ? el("span", { class: "tag " + p.consent }, p.consent === "yes" ? "sharing ok" : "blur me") : null));
}
async function doMerge() {
  const ids = [...ui.merge];
  if (!confirm(`Merge ${ids.length} people into ${pid(ids[0])}? Their faces become one person.`)) return;
  try { await api("/api/merge", { into: ids[0], people: ids.slice(1) }); } catch (e) { return; }
  ui.merge = null; toast("Merged."); await load();
}

function personDrawer(p) {
  const faces = D.faces.filter(f => f.person_id === p.person_id);
  const files = p.files.map(i => byFile[i]).filter(Boolean);
  const others = D.people.filter(o => o.person_id !== p.person_id && (o.name || o.photos + o.videos > 1)).slice(0, 60);
  const draft = { name: p.name || "", mobile: p.mobile || "", notes: p.notes || "", consent: p.consent, family: !!p.family, aliases: p.aliases || "",
    share_with: new Set((p.share_with || "").split(",").filter(Boolean).map(Number)),
    hide_from: new Set((p.hide_from || "").split(",").filter(Boolean).map(Number)) };
  const name = el("input", { class: "field", value: draft.name, placeholder: `Person ${p.person_id}`, oninput: e => draft.name = e.target.value });
  const mobile = el("input", { class: "field", value: draft.mobile, placeholder: "+91 98765 43210", inputmode: "tel", oninput: e => draft.mobile = e.target.value });
  const family = el("label", { class: "check-line" }, el("input", { type: "checkbox", checked: draft.family, onchange: e => draft.family = e.target.checked }),
    " Family member: keep their IDs, certificates, insurance and medical papers in their own folders");
  const aliases = el("input", { class: "field", value: draft.aliases, placeholder: "e.g. AJAY K SHARMA, A. Kumar", oninput: e => draft.aliases = e.target.value });
  const notes = el("input", { class: "field", value: draft.notes, placeholder: "e.g. cousin, office team", oninput: e => draft.notes = e.target.value });
  const consent = el("select", { class: "mx-select", onchange: e => draft.consent = e.target.value },
    [["pending", "Not asked yet (blurred for others)"], ["yes", "Yes, others in the photo may see my face"], ["no", "No, blur my face for others"]]
      .map(([v, t]) => el("option", { value: v, selected: draft.consent === v }, t)));
  const chipSet = (set, cls) => el("div", { class: "pchips" }, others.length ? others.map(o => {
    const b = el("button", { class: "chip-btn " + cls, "aria-pressed": set.has(o.person_id), onclick: () => {
      set.has(o.person_id) ? set.delete(o.person_id) : set.add(o.person_id); b.setAttribute("aria-pressed", set.has(o.person_id));
    } }, el("img", { src: o.cover ? faceImg(o.cover) : "", alt: "" }), o.display);
    return b;
  }) : el("span", { class: "hint" }, "Name more people to choose from."));
  const save = async () => {
    try {
      await api("/api/person", { person_id: p.person_id, name: draft.name, mobile: draft.mobile, notes: draft.notes, consent: draft.consent,
        family: draft.family, aliases: draft.aliases,
        share_with: [...draft.share_with], hide_from: [...draft.hide_from] });
    } catch (e) { return; }
    toast("Saved."); close(); await load();
  };
  const faceRow = f => el("div", { class: "fcard" },
    el("img", { src: faceImg(f.face_id), alt: "", loading: "lazy", onclick: () => byFile[f.file_ids[0]] && viewer(byFile[f.file_ids[0]]) }),
    el("span", { class: "fid" }, fid(f.face_id)),
    el("span", {}, f.age ? `${f.age} · ${f.gender} · ${f.emotion}` : "small face"),
    el("select", { class: "mx-select", "aria-label": "Not this person? Move the face", onchange: async e => {
      try { await api("/api/face", { face_id: f.face_id, person_id: e.target.value }); } catch (err) { return; }
      toast("Face moved."); close(); await load(); personDrawer(byPerson[p.person_id] || p);
    } }, el("option", { value: "" + p.person_id, selected: true }, "This person"), el("option", { value: "new" }, "Not them: new person"),
      others.map(o => el("option", { value: o.person_id }, "Move to " + o.display))));
  const scrim = el("div", { class: "drawer-scrim", onclick: e => e.target === scrim && close() },
    el("div", { class: "drawer", role: "dialog", "aria-label": p.display },
      el("div", { class: "toolbar" }, el("h2", {}, el("img", { src: p.cover ? faceImg(p.cover) : "", alt: "" }), p.display, el("span", { class: "pid" }, pid(p.person_id))),
        el("span", { class: "spacer" }), el("button", { class: "mx-icon", "aria-label": "Close", onclick: () => close() }, icon("x"))),
      el("p", { class: "hint" }, `${fmt(p.photos)} photos, ${fmt(p.videos)} videos, ${fmt(p.faces)} faces. `,
        p.age_est != null ? `Estimated about ${p.age_est} years, ${p.gender_est}, usually ${p.emotion_usual}. Estimates are often wrong.` : "",
        p.first ? ` Seen ${p.first.slice(0, 10)} to ${p.last.slice(0, 10)}.` : ""),
      el("div", { class: "form" },
        el("label", {}, "Name"), name,
        el("label", {}, "Mobile number"), el("div", {}, mobile, el("p", { class: "hint" }, p.mobile_verified ? "Verified." : "Not verified yet. Verifying by SMS and logging in come with the sharing app (part 2).")),
        el("label", {}, "Family"), family,
        el("label", {}, "Names on their documents"), el("div", {}, aliases, el("p", { class: "hint" }, "Their full name above is used too. Use the full name as printed (first name and surname): one first name alone is too easy to mix up.")),
        el("label", {}, "Notes"), notes,
        el("label", {}, "Their face in group photos"), consent,
        el("label", {}, "Show my face to"), chipSet(draft.share_with, ""),
        el("label", {}, "Hide my face from"), chipSet(draft.hide_from, "hide")),
      el("p", { class: "hint" }, "Until this person says yes, their face stays blurred for everyone else in the sharing app. Every change is logged with the date."),
      el("div", { class: "toolbar" }, el("button", { class: "mx-btn solid", onclick: save }, "Save"), el("button", { class: "mx-btn ghost", onclick: () => close() }, "Cancel")),
      el("div", { class: "danger-zone" }, el("div", {}, el("b", {}, "Delete their face data"),
        el("p", { class: "hint" }, "Removes their face codes, face pictures, name, number and sign-ups. Their faces stay in the photos as unknown faces, blurred for everyone in the sharing app.")),
        el("button", { class: "mx-btn small danger", onclick: () => deletePerson(p, close) }, "Delete")),
      el("h3", {}, `Faces (${faces.length})`), el("p", { class: "hint" }, "A face that isn't them? Use its menu to move it."),
      el("div", { class: "faces" }, faces.slice(0, 120).map(faceRow)),
      el("div", { class: "toolbar" }, el("h3", {}, `Photos & videos (${files.length})`), el("span", { class: "spacer" }),
        el("button", { class: "mx-btn small", onclick: () => { close(); Object.assign(ui, { tab: "timeline", tl: p.person_id }); remember(); tabs(); render(); scrollTo(0, 0); } }, "Timeline"),
        el("button", { class: "mx-btn small", onclick: () => { close(); Object.assign(ui, { tab: "all", who: [p.person_id], mood: "", q: "", shown: 200 }); remember(); tabs(); render(); scrollTo(0, 0); } }, "Show in the table")),
      el("div", { class: "photos" }, files.slice(0, 300).map(f => el("img", { src: thumb(f), alt: f.name, loading: "lazy", onclick: () => viewer(f) })))));
  function close() { scrim.remove(); }
  $("overlay").replaceChildren(scrim); paintIcons(scrim); name.focus();
}

/* faces */
function viewFaces() {
  const sel = el("select", { class: "mx-select", "aria-label": "Person", onchange: e => { ui.person = e.target.value; renderBody(); } },
    el("option", { value: "" }, "Everyone"), D.people.filter(p => p.faces > 1 || p.name).map(p => el("option", { value: p.person_id, selected: String(ui.person) === String(p.person_id) }, `${p.display} (${p.faces})`)));
  const moods = el("select", { class: "mx-select", "aria-label": "Emotion", onchange: e => { ui.mood = e.target.value; renderBody(); } },
    [["", "Any emotion"], ...Object.keys(EMOJI).map(k => [k, `${EMOJI[k]} ${k}`])].map(([v, t]) => el("option", { value: v, selected: ui.mood === v }, t)));
  toolbar([sel, moods], el("span", { class: "meta" }, "Every face has its own number (F…). Faces of one person share a person number (P…). Emotions are estimates."));
  renderBody = () => {
    const list = D.faces.filter(f => (!ui.person || String(f.person_id) === String(ui.person)) && (!ui.mood || ui.mood === "un" || f.emotion === ui.mood) &&
      (!ui.q || `${fid(f.face_id)} ${pid(f.person_id)} ${f.person} ${f.file} ${f.emotion} ${f.gender} ${f.age}`.toLowerCase().includes(ui.q.toLowerCase())));
    $("view").replaceChildren(el("div", { class: "faces" }, list.slice(0, ui.shown).map(f => el("div", { class: "fcard" },
      el("img", { src: faceImg(f.face_id), alt: "", loading: "lazy", onclick: () => byFile[f.file_ids[0]] && viewer(byFile[f.file_ids[0]]) }),
      el("span", { class: "fid" }, `${fid(f.face_id)} · ${pid(f.person_id)}`),
      el("b", {}, f.person),
      el("span", {}, f.age ? `${f.age} · ${f.gender} · ${EMOJI[f.emotion] || ""} ${f.emotion}` : "small face")))),
      list.length > ui.shown ? el("div", { class: "more-row" }, el("button", { class: "mx-btn small", onclick: () => { ui.shown += 400; renderBody(); } }, "Show more")) : "");
  };
  renderBody();
}

/* ---------- viewer: the file, its faces with boxes, and every detail ---------- */
async function viewer(f) {
  const src = DEMO ? thumb(f) : `/api/file/${f.id}`;
  const faces = f.face_ids.map(i => byFace[i]).filter(Boolean);
  const pic = el("div", { class: "pic" });
  if (f.kind === "video" && !DEMO) pic.append(el("video", { src, controls: true, autoplay: true, playsinline: true, poster: thumb(f) }));
  else if (f.kind === "doc" && f.ext === ".pdf" && !DEMO) pic.append(el("iframe", { src, title: f.name }));
  else {
    const img = el("img", { src: f.kind === "doc" ? thumb(f) : src, alt: f.name });
    pic.append(img);
    if (f.kind === "photo") faces.forEach(x => pic.append(el("div", { class: "box", title: `${fid(x.face_id)} ${x.person}`,
      style: `left:${x.x / x.img_w * 100}%;top:${x.y / x.img_h * 100}%;width:${x.w / x.img_w * 100}%;height:${x.h / x.img_h * 100}%` },
      el("span", {}, x.person))));
  }
  const row = (k, v) => v || v === 0 ? [el("dt", {}, k), el("dd", {}, v)] : [];
  const text = el("pre", {}, (f.text || "").slice(0, 600));
  const aside = el("aside", {},
    el("h3", {}, f.name), el("span", { class: "pid" }, `File ID ${f.id}`),
    el("dl", {},
      row("Type", f.kind + (f.screenshot ? " (screenshot)" : "")), row("Folder", f.folder), row("Date", f.taken), row("Camera", f.camera),
      row("Size", `${size(f.bytes)}${f.width ? ` · ${f.width}×${f.height}` : ""}${f.duration ? ` · ${Math.round(f.duration)} s` : ""}`),
      row("GPS", f.lat != null ? el("a", { href: `https://maps.google.com/?q=${f.lat},${f.lon}`, target: "_blank", rel: "noopener" }, `${f.lat.toFixed(5)}, ${f.lon.toFixed(5)}`) : ""),
      row("Tags", (f.labels || []).join(", ")), row("People", f.people), row("Mood (est.)", mood(f) ? `${EMOJI[mood(f)] || ""} ${mood(f)}` : ""), row("Who feels what", whoFeels(f)), row("Things in it", f.tags), row("Company / app", f.company), row("What it is", f.content),
      row("Amount", f.amount != null ? `${f.direction === "out" ? "paid " : f.direction === "in" ? "received " : ""}${money(f.amount)} ${f.currency}` : ""),
      row("IDs", f.txn_ids), row("Duplicate of", f.duplicate_of)),
    faces.length ? el("h3", {}, `Faces (${faces.length})`) : null,
    faces.length ? el("div", { class: "faces" }, faces.map(x => el("div", { class: "fcard" }, el("img", { src: faceImg(x.face_id), alt: "" }),
      el("span", { class: "fid" }, `${fid(x.face_id)} · ${pid(x.person_id)}`), el("b", {}, x.person),
      el("span", {}, x.age ? `${x.age} · ${x.gender} · ${x.emotion}` : "small face", x.frame_s != null ? ` · at ${x.frame_s}s` : "")))) : null,
    f.text ? el("h3", {}, "Text found") : null, f.text ? text : null,
    DEMO ? null : el("div", { class: "toolbar" }, el("button", { class: "mx-btn small", onclick: () => api("/api/open", { id: f.id }).catch(() => {}) }, icon("reveal"), "Show original")));
  const box = el("div", { class: "viewer", role: "dialog", "aria-label": f.name },
    el("div", { class: "vstage", onclick: e => e.target === e.currentTarget && close() }, pic,
      el("button", { class: "mx-icon close", "aria-label": "Close", onclick: () => close() }, icon("x"))), aside);
  const keys = e => { if (e.key === "Escape") close(); };
  function close() { box.remove(); document.removeEventListener("keydown", keys); }
  document.addEventListener("keydown", keys);
  document.body.append(box); paintIcons(box);
  if (!DEMO && f.text && f.text.length >= 600) api(`/api/text/${f.id}`).then(r => text.textContent = r.text).catch(() => {});
}

$("excel").onclick = e => {
  e.preventDefault();
  if (DEMO) { location.href = BASE + "Library%20details%20(demo).xlsx"; return; }
  toast("Making the Excel file…"); location.href = "/api/excel";
};
if (DEMO) document.querySelectorAll('a[href="./"]').forEach(a => a.href = window.STATIC_DEMO ? "./" : "./?demo");

/* The demo has no server: changes are kept in this page only, until it is reloaded. */
async function demoApi(path, body) {
  if (path === "/api/person") {
    const p = D.people.find(x => x.person_id === body.person_id);
    const mobile = (body.mobile || "").replace(/[\s\-()]/g, "");
    if (mobile && !/^\+?\d{7,15}$/.test(mobile)) { toast("A mobile number has 7 to 15 digits, optionally starting with +."); throw new Error("mobile"); }
    if (body.family !== !!p.family || (body.aliases || "") !== (p.aliases || "")) toast("Demo: family papers are pre-sorted. In the app, marking family files their papers.");
    Object.assign(p, { name: body.name.trim() || null, mobile: mobile || null, notes: body.notes, consent: body.consent,
      share_with: body.share_with.join(","), hide_from: body.hide_from.join(",") });
    p.display = p.name || `Person ${p.person_id}`;
    D.faces.forEach(f => { if (f.person_id === p.person_id) f.person = p.display; });
    D.files.forEach(f => { if (f.people_ids.length) f.people = f.people_ids.map(i => (D.people.find(x => x.person_id === i) || {}).display).join(", "); });
    toast("Demo: saved in this page only.");
    return { ok: true };
  }
  if (path === "/api/settings") { Object.assign(D.settings = D.settings || {}, body); return D.settings; }
  if (path === "/api/person-delete") { toast("Not in the demo: deleting needs the app."); throw new Error("demo"); }
  toast("Not in the demo. Install the app to merge people and move faces.");
  throw new Error("demo");
}
paintIcons();
load();

/* ---------- Family: each member's folder tree, like a file browser (size and newest date per folder) ---------- */
const niceDate = s => s ? new Date(s.replace(" ", "T")).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "";
const newest = fs => fs.map(f => f.modified || "").sort().pop() || "";
function familyTree(fs) {
  const root = { name: "", kids: new Map(), files: [] };
  const at = path => path.split("/").reduce((n, part) => {
    if (!n.kids.has(part)) n.kids.set(part, { name: part, kids: new Map(), files: [] });
    return n.kids.get(part);
  }, root);
  D.vault_tree.tree.forEach(at);
  fs.forEach(f => at(f.vault.path).files.push(f));
  const co = root.kids.get("4. Company");
  if (co) co.kids.forEach(c => D.vault_tree.company.forEach(sub => { if (!c.kids.has(sub)) c.kids.set(sub, { name: sub, kids: new Map(), files: [] }); }));
  const total = n => { const all = n.files.concat(...[...n.kids.values()].map(total)); n.all = all; return all; };
  total(root);
  return root;
}
function viewFamily() {
  const papers = D.files.filter(f => f.vault);
  const members = D.people.filter(p => p.family);
  const unsure = papers.filter(f => !f.vault.person_id || !byPerson[f.vault.person_id]);
  ui.open = ui.open || {};
  toolbar([], el("span", { class: "meta" }, "Papers are found by the name printed in them or the face in them; photos they're in are added to 2. Photos. You can change whose a paper is."));
  renderBody = () => {
    setHash();
    if (ui.fam == null) {
      if (!members.length) return $("view").replaceChildren(el("div", { class: "empty-help" },
        el("h3", {}, "No family members yet"),
        el("p", { class: "hint" }, "Open a person on the People tab, give their full name (as printed on their documents) and tick Family member. They get the full folder tree: Documents, Photos, Medical, Company and Miscellaneous, filled with their papers."),
        el("button", { class: "mx-btn solid small", onclick: () => { ui.tab = "people"; remember(); tabs(); render(); } }, "Go to People")));
      const card = (img, title, sub, fs, fn) => el("div", { class: "pcard", onclick: fn },
        img, el("b", {}, title), sub ? el("span", { class: "pid" }, sub) : null,
        el("span", { class: "stats" }, `${fmt(fs.filter(f => !f.vault.extra).length)} papers · ${fmt(fs.filter(f => f.vault.extra).length)} photos`),
        fs.length ? el("span", { class: "est" }, `${size(fs.reduce((a, f) => a + f.bytes, 0))} · Modified ${niceDate(newest(fs))}`) : null);
      return $("view").replaceChildren(el("div", { class: "people" },
        members.map(p => { const fs = papers.filter(f => f.vault.person_id === p.person_id || (f.vault.also || []).includes(p.person_id));
          return card(el("img", { src: p.cover ? faceImg(p.cover) : "", alt: "" }), p.name || p.display, pid(p.person_id), fs,
            () => { ui.fam = p.person_id; renderBody(); }); }),
        unsure.length ? card(el("div", { class: "folder-ico" }, "❓"), "Not sure whose", "", unsure, () => { ui.fam = "unsure"; renderBody(); }) : null));
    }
    const who = ui.fam === "unsure" ? null : byPerson[ui.fam];
    const mine = ui.fam === "unsure" ? unsure : papers.filter(f => f.vault.person_id === ui.fam || (f.vault.also || []).includes(ui.fam));
    const title = who ? (who.name || who.display) : "Not sure whose";
    const tree = familyTree(mine);
    const whose = f => el("select", { class: "mx-select small", "aria-label": "Whose is it?", onclick: e => e.stopPropagation(), onchange: async e => {
      try { await api("/api/vault", { file_id: f.id, person_id: e.target.value, folder: f.vault.extra ? null : f.vault.path }); } catch (err) { return; }
      toast("Saved. The sorted copy moves the next time you sort."); await load();
    } }, el("option", { value: "" }, "Whose?"), members.map(p => el("option", { value: p.person_id, selected: f.vault.person_id === p.person_id }, p.name || p.display)),
      el("option", { value: "none" }, "Not a family paper"), el("option", { value: "auto" }, "Decide automatically"));
    const rows = [];
    const walk = (n, depth, key) => {
      for (const k of [...n.kids.values()]) {
        const id = key + "/" + k.name, open = ui.open[id] ?? depth < 1;
        rows.push(el("div", { class: "trow folder-row" + (k.all.length ? "" : " empty"), style: `--d:${depth}`, onclick: () => { ui.open[id] = !open; renderBody(); } },
          el("span", { class: "tname" }, el("span", { class: "caret" }, k.kids.size || k.files.length ? (open ? "▾" : "▸") : ""), "📁 ", k.name),
          el("span", { class: "tnum" }, k.all.length ? fmt(k.all.length) : ""),
          el("span", { class: "tsize" }, size(k.all.reduce((a, f) => a + f.bytes, 0)) || "0 KB"),
          el("span", { class: "tdate" }, k.all.length ? niceDate(newest(k.all)) : "—")));
        if (open) {
          walk(k, depth + 1, id);
          k.files.sort((a, b) => (b.modified || "").localeCompare(a.modified || "")).forEach(f => rows.push(el("div", { class: "trow file-row", style: `--d:${depth + 1}`, onclick: () => viewer(f) },
            el("span", { class: "tname" }, el("img", { src: thumb(f), alt: "", loading: "lazy" }), f.name,
              f.vault.by ? el("span", { class: "tag" }, { name: "name in it", face: "face in it", you: "you chose" }[f.vault.by]) : null),
            el("span", { class: "tnum" }, f.vault.extra ? "" : whose(f)),
            el("span", { class: "tsize" }, size(f.bytes)), el("span", { class: "tdate" }, niceDate(f.modified)))));
        }
      }
    };
    walk(tree, 0, String(ui.fam));
    $("view").replaceChildren(
      el("div", { class: "toolbar" }, el("button", { class: "mx-btn ghost small", onclick: () => { ui.fam = null; renderBody(); } }, icon("left"), "Family"),
        el("h3", { class: "crumb" }, `Family › ${title}`), el("span", { class: "spacer" }),
        el("button", { class: "mx-btn small", onclick: () => { Object.keys(ui.open).forEach(k => { if (k.startsWith(ui.fam + "/")) delete ui.open[k]; }); walkAll(tree, String(ui.fam)); renderBody(); } }, "Open all"),
        who ? el("button", { class: "mx-btn small", onclick: () => { Object.assign(ui, { tab: "timeline", tl: who.person_id }); remember(); tabs(); render(); } }, "Timeline") : null),
      el("div", { class: "ftree" }, el("div", { class: "trow thead" }, el("span", { class: "tname" }, "Name"), el("span", { class: "tnum" }, "Files"),
        el("span", { class: "tsize" }, "Size"), el("span", { class: "tdate" }, "Modified")), rows));
    paintIcons($("view"));
  };
  const walkAll = (n, key) => n.kids.forEach(k => { ui.open[key + "/" + k.name] = true; walkAll(k, key + "/" + k.name); });
  renderBody();
}

/* ---------- Timeline: one person's life in the library: map, phones, photos per month, moods ---------- */
const MOODS = [["happy", "😊"], ["neutral", "😐"], ["surprised", "😮"], ["sad", "😢"], ["other", "😠"]];  // other: angry, scared, disgusted, contempt
const moodKey = e => MOODS.some(m => m[0] === e) ? e : "other";
const monthOf = s => (s || "").slice(0, 7);
const monthName = m => new Date(m + "-01T00:00").toLocaleDateString("en-GB", { month: "short", year: "2-digit" });
function months(from, to) { const out = []; let [y, m] = from.split("-").map(Number); const [ty, tm] = to.split("-").map(Number);
  while (y < ty || (y === ty && m <= tm)) { out.push(`${y}-${String(m).padStart(2, "0")}`); if (++m > 12) { m = 1; y++; } } return out; }
let tip;
function tooltip(e, html) {
  if (!tip) { tip = el("div", { class: "viz-tip", role: "tooltip" }); document.body.append(tip); }
  if (!html) { tip.hidden = true; return; }
  tip.hidden = false; tip.innerHTML = html;
  const r = tip.getBoundingClientRect();
  tip.style.left = Math.min(innerWidth - r.width - 8, e.clientX + 12) + "px";
  tip.style.top = Math.max(8, e.clientY - r.height - 12) + "px";
}
function barChart(keys, stacks, series, label) {  // drawn at the box's real width once it is on the page
  const box = el("div", { class: "viz-box" });
  const draw = () => { const w = box.clientWidth; if (!w) return requestAnimationFrame(draw); box.replaceChildren(barSvg(keys, stacks, series, label, w)); };
  requestAnimationFrame(draw);
  addEventListener("resize", () => box.isConnected && box.replaceChildren(barSvg(keys, stacks, series, label, box.clientWidth)));
  return box;
}
function barSvg(keys, stacks, series, label, W) {  // keys: months; stacks: {month: {series: n}}; one axis, counts
  const H = 220, L = 30, B = 26, T = 10, max = Math.max(1, ...keys.map(k => series.reduce((a, s) => a + (stacks[k]?.[s[0]] || 0), 0)));
  const step = (W - L) / keys.length, bw = Math.max(2, Math.min(28, step - 4));
  const y = v => H - B - (v / max) * (H - B - T);
  const NS = "http://www.w3.org/2000/svg", mk = (t, a) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); return e; };
  const svg = mk("svg", { viewBox: `0 0 ${W} ${H}`, class: "viz", role: "img", "aria-label": label });
  const ticks = [0, Math.ceil(max / 2), max];
  ticks.forEach(v => { svg.append(mk("line", { x1: L, x2: W, y1: y(v), y2: y(v), class: "grid" }));
    const t = mk("text", { x: L - 6, y: y(v) + 4, class: "axis", "text-anchor": "end" }); t.textContent = v; svg.append(t); });
  const every = Math.ceil(keys.length / Math.max(2, Math.floor(W / 70)));
  keys.forEach((k, i) => {
    const x = L + i * step + (step - bw) / 2;
    let base = 0;
    const segs = series.map(s => [s, stacks[k]?.[s[0]] || 0]).filter(([, n]) => n);
    segs.forEach(([s, n], j) => {
      const y1 = y(base + n), y0 = y(base), top = j === segs.length - 1;
      const h = Math.max(1, y0 - y1 - (j ? 2 : 0));  // 2px gap between stacked segments
      const r = top ? Math.min(4, bw / 2, h) : 0;
      const d = `M${x},${y1 + h} V${y1 + r} Q${x},${y1} ${x + r},${y1} H${x + bw - r} Q${x + bw},${y1} ${x + bw},${y1 + r} V${y1 + h} Z`;
      svg.append(mk("path", { d, class: "mark", style: `fill:var(--${s[2]})` }));
      base += n;
    });
    const hit = mk("rect", { x: L + i * step, y: T, width: step, height: H - B - T, class: "hit" });
    hit.addEventListener("mousemove", e => tooltip(e, `<b>${monthName(k)}</b>` + series.map(s => `<div><i style="background:var(--${s[2]})"></i>${s[1]} <b>${stacks[k]?.[s[0]] || 0}</b></div>`).join("")));
    hit.addEventListener("mouseleave", e => tooltip(e, null));
    svg.append(hit);
    if (i % every === 0) { const t = mk("text", { x: L + i * step + step / 2, y: H - 8, class: "axis", "text-anchor": "middle" }); t.textContent = monthName(k); svg.append(t); }
  });
  return svg;
}
function loadLeaflet() {
  if (window.L) return Promise.resolve();
  return new Promise((ok, bad) => {
    const css = el("link", { rel: "stylesheet", href: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" });
    const js = el("script", { src: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js" });
    js.onload = ok; js.onerror = bad;
    document.head.append(css, js);
  });
}
function viewTimeline() {
  const people = D.people.filter(p => p.name || p.photos + p.videos > 2);
  if (ui.tl == null || !byPerson[ui.tl]) ui.tl = (people[0] || {}).person_id;
  const sel = el("select", { class: "mx-select", "aria-label": "Person", onchange: e => { ui.tl = +e.target.value; remember(); render(); } },
    people.map(p => el("option", { value: p.person_id, selected: p.person_id === ui.tl }, `${p.display} · ${pid(p.person_id)}`)));
  toolbar([sel], el("span", { class: "meta" }, "From the date, place and phone saved in each photo. Moods are estimates."));
  $("toolbar").querySelector("input").hidden = true;
  setHash();
  const p = byPerson[ui.tl];
  if (!p) return $("view").replaceChildren(el("p", { class: "mx-empty" }, "No people yet."));
  const files = p.files.map(i => byFile[i]).filter(f => f && f.taken).sort((a, b) => a.taken.localeCompare(b.taken));
  const myFaces = D.faces.filter(x => x.person_id === p.person_id);
  const faceIn = Object.fromEntries(myFaces.map(x => [x.file_ids[0], x]));
  const ms = files.length ? months(monthOf(files[0].taken), monthOf(files[files.length - 1].taken)) : [];
  const perMonth = {}, moodMonth = {};
  files.forEach(f => { const m = monthOf(f.taken); (perMonth[m] = perMonth[m] || { n: 0 }).n++;
    const x = faceIn[f.id]; if (x && x.emotion) { const k = moodKey(x.emotion); (moodMonth[m] = moodMonth[m] || {})[k] = (moodMonth[m][k] || 0) + 1; } });
  const phones = {}; files.forEach(f => { if (f.camera) phones[f.camera] = (phones[f.camera] || 0) + 1; });
  const geo = files.filter(f => f.lat != null);
  const moodTotals = {}; Object.values(moodMonth).forEach(o => Object.entries(o).forEach(([k, n]) => moodTotals[k] = (moodTotals[k] || 0) + n));
  const series = MOODS.map(([k, e], i) => [k, `${e} ${k}`, `series-${i + 1}`]);
  const tableView = el("table", { class: "dtable small-table", hidden: true }, el("thead", {}, el("tr", {}, el("th", {}, "Month"), series.map(s => el("th", {}, s[1])))),
    el("tbody", {}, ms.filter(m => moodMonth[m]).map(m => el("tr", {}, el("td", {}, monthName(m)), series.map(s => el("td", { class: "num" }, moodMonth[m][s[0]] || 0))))));
  const chart = Object.keys(moodMonth).length ? barChart(ms, moodMonth, series, "Mood per month") : el("p", { class: "hint" }, "Their face was too small to read a mood.");
  const mapBox = el("div", { class: "map", id: "map" }, el("p", { class: "hint" }, geo.length ? "Loading the map…" : "None of their photos has a saved place."));
  const stat = (h, v, s) => el("div", { class: "mx-kpi" }, el("h3", {}, h), el("b", {}, v), el("small", {}, s || " "));
  $("view").replaceChildren(
    el("div", { class: "tl-head" }, el("img", { src: p.cover ? faceImg(p.cover) : "", alt: "" }),
      el("div", {}, el("h2", {}, p.display, " ", el("span", { class: "pid" }, pid(p.person_id))),
        el("p", { class: "hint" }, files.length ? `${niceDate(files[0].taken)} to ${niceDate(files[files.length - 1].taken)} · ${fmt(files.length)} photos and videos with a date` : "No dated photos yet."))),
    el("section", { class: "mx-kpis", style: "--n:5" },
      stat("Photos & videos", fmt(p.photos + p.videos), `${fmt(p.faces)} faces`), stat("Places", fmt(geo.length), "photos with a location"),
      stat("Phones", fmt(Object.keys(phones).length), Object.keys(phones)[0] || ""), stat("Usually", p.emotion_usual || "—", "mood (est.)"),
      stat("Age (est.)", p.age_est != null ? `~${p.age_est}` : "—", p.gender_est || "")),
    el("div", { class: "tl-grid" },
      el("div", { class: "card-box" }, el("h3", {}, "Where"), mapBox,
        el("p", { class: "hint" }, "Map tiles come from OpenStreetMap: only the map area is requested, never your photos.")),
      el("div", { class: "card-box" }, el("h3", {}, "Which phone"), Object.keys(phones).length ? el("div", { class: "hbars" },
        Object.entries(phones).sort((a, b) => b[1] - a[1]).map(([k, n]) => el("div", { class: "hbar" }, el("span", {}, k), el("b", {}, fmt(n)),
          el("i", { style: `width:${n / Math.max(...Object.values(phones)) * 100}%` })))) : el("p", { class: "hint" }, "No phone saved in their photos."))),
    el("div", { class: "card-box" }, el("h3", {}, "Photos per month"), ms.length ? barChart(ms, Object.fromEntries(ms.map(m => [m, { n: perMonth[m]?.n || 0 }])), [["n", "Photos & videos", "series-1"]], "Photos per month") : el("p", { class: "hint" }, "No dates.")),
    el("div", { class: "card-box" },
      el("div", { class: "toolbar" }, el("h3", {}, "Mood over time (estimated)"), el("span", { class: "spacer" }),
        el("button", { class: "mx-btn small", onclick: e => { tableView.hidden = !tableView.hidden; e.target.textContent = tableView.hidden ? "Show as table" : "Show as chart"; chart.hidden = !tableView.hidden; } }, "Show as table")),
      el("div", { class: "legend" }, series.map(s => el("span", {}, el("i", { style: `background:var(--${s[2]})` }), `${s[1]} ${fmt(moodTotals[s[0]] || 0)}`))),
      chart, tableView),
    el("div", { class: "card-box" }, el("h3", {}, "Month by month"),
      ...ms.filter(m => perMonth[m]).reverse().map(m => el("div", { class: "tl-month" }, el("b", {}, monthName(m)),
        el("div", { class: "photos" }, files.filter(f => monthOf(f.taken) === m).map(f => {
          const x = faceIn[f.id];
          return el("img", { src: thumb(f), alt: f.name, loading: "lazy", title: `${niceDate(f.taken)}${f.camera ? " · " + f.camera : ""}${x && x.emotion ? " · " + x.emotion : ""}`, onclick: () => viewer(f) });
        }))))));
  if (geo.length) loadLeaflet().then(() => {
    mapBox.replaceChildren();
    const map = L.map(mapBox, { scrollWheelZoom: false });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "© OpenStreetMap contributors" }).addTo(map);
    const pts = geo.map(f => [f.lat, f.lon]);
    L.polyline(pts, { color: getComputedStyle(document.body).getPropertyValue("--series-1").trim() || "#2a78d6", weight: 2, opacity: .6 }).addTo(map);
    geo.forEach(f => L.circleMarker([f.lat, f.lon], { radius: 6, weight: 2, color: "#fff", fillColor: "#2a78d6", fillOpacity: 1 })
      .bindPopup(`<img src="${thumb(f)}" width="120" alt=""><br><b>${niceDate(f.taken)}</b>${f.camera ? "<br>" + f.camera : ""}`).addTo(map));
    map.fitBounds(L.latLngBounds(pts).pad(0.3));
  }).catch(() => mapBox.replaceChildren(el("p", { class: "hint" }, "The map needs an internet connection. Places: " + geo.map(f => `${f.lat.toFixed(3)}, ${f.lon.toFixed(3)}`).slice(0, 10).join(" · "))));
}

/* ---------- Face search: find every photo of a face (compares face codes) ---------- */
function viewFaceSearch() {
  toolbar([], el("span", { class: "meta" }, "The picture you search with stays on this computer and isn't saved."));
  $("toolbar").querySelector("input").hidden = true;
  const input = el("input", { type: "file", accept: "image/*", hidden: true, onchange: e => e.target.files[0] && readFile(e.target.files[0]) });
  const drop = el("label", { class: "dropzone", tabindex: 0 },
    el("span", { class: "dz-ico" }, "🔍"), el("b", {}, "Drop a photo or selfie here"),
    el("span", { class: "hint" }, "or click to choose one. The biggest face in it is used."), input);
  drop.ondragover = e => { e.preventDefault(); drop.classList.add("over"); };
  drop.ondragleave = () => drop.classList.remove("over");
  drop.ondrop = e => { e.preventDefault(); drop.classList.remove("over"); const f = e.dataTransfer.files[0]; if (f) readFile(f); };
  const out = el("div", { class: "fs-out" });
  const samples = DEMO ? el("div", { class: "card-box" }, el("h3", {}, "Try it with a sample face"),
    el("p", { class: "hint" }, "In the demo the matching is simulated. In the app, any photo or selfie works."),
    el("div", { class: "pchips" }, D.people.filter(p => p.name).map(p => el("button", { class: "chip-btn", onclick: () => demoSearch(p) },
      el("img", { src: faceImg(p.cover), alt: "" }), p.display)))) : null;
  $("view").replaceChildren(el("div", { class: "fs-grid" }, drop, samples), out);
  function readFile(file) {
    if (DEMO) return toast("In the demo, pick a sample face below.");
    const r = new FileReader();
    r.onload = () => run(r.result);
    r.readAsDataURL(file);
  }
  async function run(dataUrl) {
    out.replaceChildren(el("div", { class: "card-box loading" }, el("span", { class: "spinner" }), "Looking at every face in the library…"));
    let res;
    try { res = await api("/api/face-search", { image: dataUrl }); } catch (e) { out.replaceChildren(); return; }
    show(res);
  }
  function demoSearch(p) {
    const others = D.people.filter(o => o.person_id !== p.person_id && o.faces > 2).slice(0, 2);
    show({ query: faceImg(p.cover), faces_in_picture: 1, estimate: { age: p.age_est ? `~${p.age_est}` : null, gender: p.gender_est, emotion: p.emotion_usual },
      people: [{ person_id: p.person_id, score: 0.93, level: "strong", face_ids: D.faces.filter(f => f.person_id === p.person_id).map(f => f.face_id) },
        ...others.map((o, i) => ({ person_id: o.person_id, score: 0.47 - i * 0.03, level: "possible", face_ids: [] }))] });
  }
  function show(res) {
    const card = r => {
      const p = byPerson[r.person_id] || { display: `Person ${r.person_id}` };
      return el("div", { class: "match " + r.level, onclick: () => { Object.assign(ui, { tab: "all", who: [r.person_id], mood: "", tag: "", q: "" }); remember(); tabs(); render(); scrollTo(0, 0); } },
        el("img", { src: p.cover ? faceImg(p.cover) : "", alt: "" }),
        el("div", { class: "m-txt" }, el("b", {}, p.display), el("span", { class: "pid" }, pid(r.person_id)),
          el("span", { class: "hint" }, `${fmt((p.photos || 0) + (p.videos || 0))} photos and videos`)),
        el("div", { class: "m-score" }, el("b", {}, `${Math.round(r.score * 100)}%`), el("span", { class: "meter" }, el("i", { style: `width:${Math.round(r.score * 100)}%` })),
          el("small", {}, r.level === "strong" ? "same person" : "maybe")));
    };
    const strong = res.people.filter(r => r.level === "strong"), maybe = res.people.filter(r => r.level !== "strong");
    const e = res.estimate || {};
    out.replaceChildren(el("div", { class: "card-box fs-result" },
      el("div", { class: "fs-query" }, el("img", { src: res.query, alt: "The face searched for" }),
        el("div", {}, el("b", {}, "The face we searched for"),
          el("span", { class: "hint" }, [e.age && `age ${e.age}`, e.gender, e.emotion].filter(Boolean).join(" · ") + " (est.)",
            res.faces_in_picture > 1 ? ` · ${res.faces_in_picture} faces in the picture, the biggest was used` : ""))),
      el("h3", {}, strong.length ? "Found" : "Not found in the library"),
      strong.length ? el("div", { class: "matches" }, strong.map(card)) : el("p", { class: "hint" }, "No one in the library looks like this person. They may be in photos where their face is too small or turned away."),
      maybe.length ? el("h3", {}, "Possible matches") : null, maybe.length ? el("div", { class: "matches" }, maybe.map(card)) : null,
      el("p", { class: "hint" }, "Click a person to see all their photos. Face matching can be wrong for twins, siblings and children.")));
  }
}

/* ---------- Events: who came, how they felt, ages and genders (all estimated) ---------- */
const ageBand = a => a == null ? null : a < 13 ? "Children (0-12)" : a < 20 ? "Teens (13-19)" : a < 36 ? "Young adults (20-35)" : a < 56 ? "Adults (36-55)" : "Seniors (56+)";
const BANDS = ["Children (0-12)", "Teens (13-19)", "Young adults (20-35)", "Adults (36-55)", "Seniors (56+)"];
function events() {
  if (D._events) return D._events;
  const fs = D.files.filter(f => f.taken && (f.kind === "photo" || f.kind === "video") && !f.screenshot && !f.duplicate_of)
    .sort((a, b) => a.taken.localeCompare(b.taken));
  const t = f => new Date(f.taken.replace(" ", "T")).getTime();
  const groups = [];
  let cur = [];
  fs.forEach(f => { if (cur.length && t(f) - t(cur[cur.length - 1]) > 3 * 3600e3) { groups.push(cur); cur = []; } cur.push(f); });
  if (cur.length) groups.push(cur);
  D._events = groups.filter(g => g.length >= 6 && new Set(g.flatMap(f => f.people_ids)).size >= 3).map((g, i) => {
    const tags = {};
    g.forEach(f => (f.labels || []).forEach(x => tags[x] = (tags[x] || 0) + 1));
    const ORDER = ["event", "family", "trip", "beach", "mountains", "landmark", "dine-out", "city", "home"];  // the first one in a fifth of the photos names it
    const kind = ORDER.find(k => (tags[k] || 0) >= g.length / 5) || "";
    const label = { "dine-out": "Meal out", trip: "Trip", family: "Family get-together", event: "Party or function", beach: "Beach day", mountains: "Mountains", city: "Day out", home: "At home", landmark: "Sightseeing" }[kind] || "Get-together";
    return { id: i, files: g, start: g[0].taken, end: g[g.length - 1].taken, label, title: D.event_names?.[g[0].taken] || label };
  }).reverse();
  return D._events;
}
function eventStats(ev) {
  const faces = ev.files.flatMap(f => f.face_ids.map(i => byFace[i]).filter(Boolean));
  const guests = {};
  faces.forEach(x => {
    const g = guests[x.person_id] = guests[x.person_id] || { id: x.person_id, faces: [], files: new Set(), first: null, last: null };
    g.faces.push(x);
    const f = byFile[x.file_ids[0]];
    g.files.add(f.id);
    g.first = !g.first || f.taken < g.first ? f.taken : g.first;
    g.last = !g.last || f.taken > g.last ? f.taken : g.last;
  });
  const list = Object.values(guests).map(g => {
    const moods = {}; g.faces.forEach(x => x.emotion && (moods[moodKey(x.emotion)] = (moods[moodKey(x.emotion)] || 0) + 1));
    const ages = g.faces.map(x => x.age_years).filter(a => a != null), gens = g.faces.map(x => x.gender).filter(Boolean);
    const p = byPerson[g.id] || {};
    return { ...g, p, moods, usual: Object.entries(moods).sort((a, b) => b[1] - a[1])[0]?.[0] || "",
      age: ages.length ? Math.round(ages.reduce((a, b) => a + b) / ages.length) : p.age_est,
      gender: gens.length ? (gens.filter(x => x === "female").length > gens.length / 2 ? "female" : "male") : p.gender_est };
  }).sort((a, b) => b.files.size - a.files.size);
  const moods = {}; faces.forEach(x => x.emotion && (moods[moodKey(x.emotion)] = (moods[moodKey(x.emotion)] || 0) + 1));
  const bands = {}; list.forEach(g => { const b = ageBand(g.age); if (b) bands[b] = (bands[b] || 0) + 1; });
  const gender = { female: list.filter(g => g.gender === "female").length, male: list.filter(g => g.gender === "male").length };
  return { list, moods, bands, gender, faces };
}
function stackBar(parts, series) {  // one part-to-whole bar with labels
  const total = Object.values(parts).reduce((a, b) => a + b, 0) || 1;
  return el("div", { class: "stack" }, el("div", { class: "stack-bar" }, series.filter(s => parts[s[0]]).map(s => {
    const seg = el("i", { style: `flex:${parts[s[0]]};background:var(--${s[2]})` });
    seg.onmousemove = e => tooltip(e, `${s[1]} <b>${parts[s[0]]}</b> (${Math.round(parts[s[0]] / total * 100)}%)`);
    seg.onmouseleave = e => tooltip(e, null);
    return seg;
  })), el("div", { class: "legend" }, series.filter(s => parts[s[0]]).map(s => el("span", {}, el("i", { style: `background:var(--${s[2]})` }), `${s[1]} ${Math.round(parts[s[0]] / total * 100)}%`))));
}
function viewEvents() {
  const evs = events();
  toolbar([], el("span", { class: "meta" }, "Photos taken close together (no gap over 3 hours) with at least 3 people. Moods, ages and genders are estimates."));
  $("toolbar").querySelector("input").hidden = true;
  const moodSeries = MOODS.map(([k, e], i) => [k, `${e} ${k}`, `series-${i + 1}`]);
  renderBody = () => {
    setHash();
    if (ui.ev == null || !evs[ui.ev]) {
      if (!evs.length) return $("view").replaceChildren(el("p", { class: "mx-empty" }, "No events found yet: an event needs at least 6 photos taken close together with 3 or more people."));
      return $("view").replaceChildren(el("div", { class: "events" }, evs.map((ev, i) => {
        const st = eventStats(ev);
        const top = Object.entries(st.moods).sort((a, b) => b[1] - a[1])[0];
        return el("button", { class: "event-card", onclick: () => { ui.ev = i; renderBody(); scrollTo(0, 0); } },
          el("div", { class: "mosaic" }, ev.files.filter(f => f.face_ids.length).slice(0, 4).map(f => el("img", { src: thumb(f), alt: "", loading: "lazy" }))),
          el("div", { class: "ev-txt" }, el("b", {}, ev.title), el("span", { class: "hint" }, niceDate(ev.start)),
            el("span", { class: "ev-meta" }, `${fmt(ev.files.length)} photos · ${fmt(st.list.length)} people`, top ? ` · mostly ${MOODS.find(m => m[0] === top[0])[1]} ${top[0]}` : "")));
      })));
    }
    const ev = evs[ui.ev], st = eventStats(ev);
    const known = st.list.filter(g => g.p.name).length;
    const hours = (new Date(ev.end.replace(" ", "T")) - new Date(ev.start.replace(" ", "T"))) / 3600e3;
    const avgAge = st.list.filter(g => g.age != null);
    const csv = () => {
      const rows = [["Person ID", "Name", "Photos", "First seen", "Last seen", "Usual mood (est.)", ...MOODS.map(m => m[0]), "Age (est.)", "Gender (est.)"],
        ...st.list.map(g => [pid(g.id), g.p.display || "", g.files.size, g.first, g.last, g.usual, ...MOODS.map(m => g.moods[m[0]] || 0), g.age ?? "", g.gender || ""])];
      const a = el("a", { href: URL.createObjectURL(new Blob([rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n")], { type: "text/csv" })),
        download: `${ev.title} ${ev.start.slice(0, 10)} guests.csv` });
      a.click();
    };
    const stat = (h, v, s) => el("div", { class: "mx-kpi" }, el("h3", {}, h), el("b", {}, v), el("small", {}, s || " "));
    $("view").replaceChildren(
      el("div", { class: "toolbar" }, el("button", { class: "mx-btn ghost small", onclick: () => { ui.ev = null; renderBody(); } }, icon("left"), "Events"),
        el("h3", { class: "crumb" }, `${ev.title} · ${niceDate(ev.start)}`), el("span", { class: "spacer" }),
        el("button", { class: "mx-btn small", onclick: csv }, icon("download"), "Guest list (CSV)")),
      el("section", { class: "mx-kpis", style: "--n:5" },
        stat("Photos", fmt(ev.files.length), `${ev.start.slice(11, 16)}–${ev.end.slice(11, 16)}${hours >= 1 ? ` · ${Math.round(hours)} h` : ""}`),
        stat("People", fmt(st.list.length), `${known} named · ${st.list.length - known} not named`),
        stat("Mostly", (() => { const t = Object.entries(st.moods).sort((a, b) => b[1] - a[1])[0]; return t ? `${MOODS.find(m => m[0] === t[0])[1]} ${t[0]}` : "—"; })(), "mood (est.)"),
        stat("Average age", avgAge.length ? `~${Math.round(avgAge.reduce((a, g) => a + g.age, 0) / avgAge.length)}` : "—", "estimated"),
        stat("Women · men", `${st.gender.female} · ${st.gender.male}`, "estimated")),
      el("div", { class: "tl-grid three" },
        el("div", { class: "card-box" }, el("h3", {}, "Mood of everyone (est.)"), Object.keys(st.moods).length ? stackBar(st.moods, moodSeries) : el("p", { class: "hint" }, "Faces too small to read a mood.")),
        el("div", { class: "card-box" }, el("h3", {}, "Ages (est.)"), el("div", { class: "hbars" }, BANDS.filter(b => st.bands[b]).map(b => el("div", { class: "hbar" }, el("span", {}, b), el("b", {}, fmt(st.bands[b])),
          el("i", { style: `width:${st.bands[b] / Math.max(...Object.values(st.bands)) * 100}%` }))))),
        el("div", { class: "card-box" }, el("h3", {}, "Women and men (est.)"), stackBar(st.gender, [["female", "Women", "series-5"], ["male", "Men", "series-1"]]))),
      el("div", { class: "card-box" }, el("h3", {}, "Who was there"),
        el("div", { class: "tbl-wrap flat" }, el("table", { class: "dtable" },
          el("thead", {}, el("tr", {}, ["", "Person", "Photos", "First seen", "Last seen", "Mood (est.)", "Usual", "Age (est.)", "Gender (est.)"].map(h => el("th", {}, h)))),
          el("tbody", {}, st.list.map(g => el("tr", { onclick: () => byPerson[g.id] && personDrawer(byPerson[g.id]) },
            el("td", {}, el("img", { class: "face", src: g.p.cover ? faceImg(g.p.cover) : faceImg(g.faces[0].face_id), alt: "" })),
            el("td", {}, el("b", {}, g.p.display || `Person ${g.id}`), " ", el("span", { class: "pid" }, pid(g.id))),
            el("td", { class: "num" }, fmt(g.files.size)), el("td", {}, g.first.slice(11, 16)), el("td", {}, g.last.slice(11, 16)),
            el("td", {}, Object.keys(g.moods).length ? el("div", { class: "mini-stack" }, MOODS.filter(m => g.moods[m[0]]).map((m, i) => el("i", { title: `${m[0]} ${g.moods[m[0]]}`, style: `flex:${g.moods[m[0]]};background:var(--series-${MOODS.indexOf(m) + 1})` }))) : "—"),
            el("td", {}, g.usual ? `${MOODS.find(m => m[0] === g.usual)[1]} ${g.usual}` : "—"),
            el("td", { class: "num" }, g.age != null ? `~${g.age}` : "—"), el("td", {}, g.gender || "—"))))))),
      el("div", { class: "card-box" }, el("h3", {}, "Photos"), el("div", { class: "photos" }, ev.files.map(f => el("img", { src: thumb(f), alt: f.name, loading: "lazy", onclick: () => viewer(f) })))));
    paintIcons($("view"));
  };
  renderBody();
}

/* ---------- Requests: sign-ups from the sharing app waiting for you, and alerts ---------- */
function viewRequests() {
  toolbar([], el("span", { class: "meta" }, "People who signed up in the sharing app with their mobile number and a live selfie."));
  $("toolbar").querySelector("input").hidden = true;
  const reqs = D.requests || [], alerts = D.alerts || [];
  const label = { pending: ["Waiting for you", "warn"], conflict: ["Blocked: face belongs to another number", "bad"], approved: ["Approved", "ok"],
    denied: ["Denied", ""], none: ["Not found in any photo", ""] };
  const decide = async (r, action, person_id) => {
    try { await api("/api/enrollment", { id: r.id, action, person_id }); } catch (e) { return; }
    toast(action === "approve" ? "Approved. They can now see their photos." : "Denied."); await load();
  };
  $("view").replaceChildren(
    alerts.length ? el("div", { class: "card-box" }, el("h3", {}, "Alerts"), alerts.map(a => el("div", { class: "alert " + (a.kind === "impersonation" ? "bad" : "warn") },
      el("span", { class: "a-ico" }, a.kind === "impersonation" ? "⚠️" : "🗑️"),
      el("div", {}, el("b", {}, a.kind === "impersonation" ? "Someone tried to use another person's face" : "Asked to be deleted"),
        el("p", { class: "hint" }, a.detail), el("small", { class: "hint" }, a.at))))) : null,
    el("div", { class: "card-box" }, el("h3", {}, "Sign-up requests"),
      reqs.length ? reqs.map(r => {
        const p = byPerson[r.person_id];
        const [txt, cls] = label[r.status] || [r.status, ""];
        const pick = el("select", { class: "mx-select small", "aria-label": "Who is this?" }, el("option", { value: "" }, "Who is this?"),
          D.people.filter(q => q.name || q.photos + q.videos > 1).map(q => el("option", { value: q.person_id, selected: q.person_id === r.person_id }, `${q.display} · ${pid(q.person_id)}`)));
        return el("div", { class: "req" },
          el("div", { class: "req-faces" }, el("figure", {}, el("img", { src: r.selfie || "", alt: "" }), el("figcaption", {}, "Live selfie")),
            el("span", { class: "vs" }, r.score ? `${Math.round(r.score * 100)}%` : "?"),
            el("figure", {}, el("img", { src: p && p.cover ? faceImg(p.cover) : "", alt: "" }), el("figcaption", {}, p ? p.display : "No match"))),
          el("div", { class: "req-txt" }, el("b", {}, r.mobile), el("span", { class: "status " + cls }, txt), el("small", { class: "hint" }, r.at)),
          r.status === "pending" ? el("div", { class: "req-acts" }, pick,
            el("button", { class: "mx-btn small solid", onclick: () => decide(r, "approve", pick.value || r.person_id) }, "Approve"),
            el("button", { class: "mx-btn small", onclick: () => decide(r, "deny") }, "Deny")) : null);
      }) : el("p", { class: "hint" }, "No sign-ups yet. People sign up at /share.html with their mobile number and a live selfie.")),
    el("p", { class: "hint" }, "Approve only people you know. A face match is not proof of identity: twins, siblings and printed photos can fool it."));
}

/* ---------- Privacy: estimates switch, deletion requests, consent record, what is kept ---------- */
async function deletePerson(p, after) {
  if (!confirm(`Delete ${p.display}'s face data? Their face codes, face pictures, name, number and sign-ups are removed. This can't be undone.`)) return;
  try { const r = await api("/api/person-delete", { person_id: p.person_id }); toast(`Deleted ${fmt(r.faces)} face codes and pictures.`); }
  catch (e) { return; }
  after && after(); await load();
}
function viewPrivacy() {
  toolbar([], el("span", { class: "meta" }, "What is kept about the people in your photos, and the record of what they agreed to."));
  $("toolbar").querySelector("input").hidden = true;
  const st = D.settings || { estimates: true };
  const log = D.consent_log || [];
  const dels = (D.alerts || []).filter(a => a.kind === "delete request" && !a.seen);
  const sw = el("input", { type: "checkbox", role: "switch", checked: st.estimates, onchange: async e => {
    try { D.settings = await api("/api/settings", { estimates: e.target.checked }); } catch (err) { e.target.checked = !e.target.checked; return; }
    toast(e.target.checked ? "Estimates on. New files get age, gender and mood guesses." : "Estimates off. They're hidden now and never computed for new files.");
    await load();
  } });
  const csv = () => {
    const rows = [["When", "Person ID", "Name", "What", "Details"], ...log.map(r => [r.at, r.person_id ? pid(r.person_id) : "", byPerson[r.person_id]?.display || "", r.action, r.detail || ""])];
    el("a", { href: URL.createObjectURL(new Blob([rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n")], { type: "text/csv" })), download: "consent record.csv" }).click();
  };
  $("view").replaceChildren(
    el("div", { class: "tl-grid" },
      el("div", { class: "card-box" }, el("h3", {}, "Age, gender and mood estimates"),
        el("label", { class: "switch-row" }, sw, el("span", {}, st.estimates ? "On: shown as estimates" : "Off: never computed or shown")),
        el("p", { class: "hint" }, "These are guesses by a computer model and are often wrong. The EU bans emotion recognition at workplaces and schools, which can include company events. Turn them off if you sell or share the app, until a lawyer says otherwise.")),
      el("div", { class: "card-box" }, el("h3", {}, "Documents"),
        el("a", { class: "doc-link", href: "share-privacy.html", target: "_blank", rel: "noopener" }, "📄 Privacy notice people agree to ", el("span", { class: "pid" }, D.policy_version || "draft")),
        el("p", { class: "hint" }, "Questions for a privacy lawyer: docs/legal-checklist.md in the app folder. Both are drafts until a lawyer checks them."))),
    el("div", { class: "card-box" }, el("h3", {}, `Deletion requests${dels.length ? ` (${dels.length})` : ""}`),
      dels.length ? dels.map(a => { const p = byPerson[a.person_id];
        return el("div", { class: "req" }, el("img", { class: "face", src: p && p.cover ? faceImg(p.cover) : "", alt: "", style: "width:48px;height:48px;border-radius:50%" }),
          el("div", { class: "req-txt" }, el("b", {}, p ? p.display : pid(a.person_id)), el("span", { class: "hint" }, a.detail), el("small", { class: "hint" }, a.at)),
          el("button", { class: "mx-btn small danger", onclick: () => p && deletePerson(p) }, "Delete their face data")); })
        : el("p", { class: "hint" }, "No one has asked to be deleted. People can ask from the sharing app (Settings → Blur me everywhere).")),
    el("div", { class: "card-box" }, el("h3", {}, "What is kept, and for how long"),
      el("div", { class: "keep" }, [
        ["Face codes (128 numbers per face)", "Until you delete the person", "To group faces into people and find photos"],
        ["Mobile numbers", "Until you delete the person", "Sign-in and impersonation alerts"],
        ["Live selfies from sign-ups", "30 days, then deleted automatically", "So you can check who signed up"],
        ["Face codes of rejected sign-ups", "30 days", "To spot repeated impersonation"],
        ["One-time codes", "About an hour", "Sign-in"],
        ["Sign-ins", "30 days", "Staying signed in"],
        ["Consent record", "Kept", "Proof of what people agreed to"],
      ].map(([a, b, c]) => el("div", { class: "keep-row" }, el("b", {}, a), el("span", {}, b), el("span", { class: "hint" }, c))))),
    logCard());
  function logCard() {
    const head = el("div", { class: "toolbar" }, el("h3", {}, `Consent record (${fmt(log.length)})`), el("span", { class: "spacer" }),
      log.length ? el("button", { class: "mx-btn small", onclick: csv }, icon("download"), "Download CSV") : null);
    if (!log.length) return el("div", { class: "card-box" }, head, el("p", { class: "hint" }, "Nothing recorded yet."));
    const row = r => el("tr", {}, el("td", {}, r.at),
      el("td", {}, r.person_id ? `${byPerson[r.person_id]?.display || "deleted"} · ${pid(r.person_id)}` : "—"),
      el("td", {}, r.action), el("td", { class: "wrap" }, r.detail || ""));
    const tbl = el("table", { class: "dtable" }, el("thead", {}, el("tr", {}, ["When", "Person", "What", "Details"].map(h => el("th", {}, h)))),
      el("tbody", {}, log.slice(0, 300).map(row)));
    return el("div", { class: "card-box" }, head, el("div", { class: "tbl-wrap flat" }, tbl));
  }
  paintIcons($("view"));
}
