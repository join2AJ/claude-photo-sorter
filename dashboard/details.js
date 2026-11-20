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
const remember = () => { try { sessionStorage.setItem("details-ui", JSON.stringify({ tab: ui.tab, minPhotos: ui.minPhotos, who: ui.who, mood: ui.mood })); } catch (e) {} };

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
  try { D = DEMO ? await fetch(BASE + "details.json").then(r => r.json()) : await api("/api/details"); }
  catch (e) { $("view").replaceChildren(el("p", { class: "mx-empty" }, "Nothing to show yet. Go back and sort a folder first.")); return; }
  indexes();
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

const TABS = [
  ["all", "Everything", () => D.files.length], ["people", "People", () => D.people.length], ["faces", "Faces", () => D.faces.length],
  ["shots", "Screenshots", () => D.files.filter(f => f.screenshot).length], ["money", "Money", () => D.files.filter(f => f.amount && !f.duplicate_of).length],
  ["family", "Family", () => D.people.filter(p => p.family).length],
  ["docs", "Documents", () => D.files.filter(f => f.kind === "doc").length], ["videos", "Videos", () => D.files.filter(f => f.kind === "video").length],
];
function tabs() {
  $("tabs").replaceChildren(...TABS.map(([k, label, n]) => el("button", { role: "tab", "aria-selected": ui.tab === k, onclick: () => {
    Object.assign(ui, { tab: k, sort: null, desc: false, shown: 200, q: "" }); remember(); tabs(); render();
  } }, label, el("em", {}, fmt(n())))));
}

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
  ({ all: viewAll, family: viewFamily, people: viewPeople, faces: viewFaces, shots: viewShots, money: viewMoney, docs: viewDocs, videos: viewVideos })[ui.tab]();
}
function simple(filter, cols, extra = [], note = null) {
  toolbar(extra, note);
  renderBody = () => $("view").replaceChildren(...table(D.files.filter(f => filter(f) && match(f, ui.q)), cols));
  renderBody();
}
/* filters shared by Everything and Videos: people in the photo (all of them) and mood */
const filterPeopleMood = f => ui.who.every(id => f.people_ids.includes(id)) &&
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
  return [add, ...chips, moods];
}
function viewAll() {
  const kind = el("select", { class: "mx-select", "aria-label": "Type", onchange: e => { ui.kind = e.target.value; renderBody(); } },
    [["", "All types"], ["photo", "Photos"], ["video", "Videos"], ["doc", "Documents"]].map(([v, t]) => el("option", { value: v, selected: ui.kind === v }, t)));
  simple(f => (!ui.kind || f.kind === ui.kind) && filterPeopleMood(f),
    [T.thumb, T.id, T.name, T.kind, T.folder, T.taken, T.people, T.mood, T.feels, T.pids, T.fids, T.ests, T.tags, T.company, T.content, T.amount, T.camera, T.size, T.gps, T.dup],
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
      el("h3", {}, `Faces (${faces.length})`), el("p", { class: "hint" }, "A face that isn't them? Use its menu to move it."),
      el("div", { class: "faces" }, faces.slice(0, 120).map(faceRow)),
      el("div", { class: "toolbar" }, el("h3", {}, `Photos & videos (${files.length})`), el("span", { class: "spacer" }),
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
      row("People", f.people), row("Mood (est.)", mood(f) ? `${EMOJI[mood(f)] || ""} ${mood(f)}` : ""), row("Who feels what", whoFeels(f)), row("Things in it", f.tags), row("Company / app", f.company), row("What it is", f.content),
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
  toast("Not in the demo. Install the app to merge people and move faces.");
  throw new Error("demo");
}
paintIcons();
load();

/* ---------- Family: each family member's papers in folders (Certificates, ID, Insurance, Medical...) ---------- */
const FOLDER_ICON = { certificates: "📜", resume: "💼", dna: "🧬", id: "🪪", insurance: "🛡️", medical: "🩺", education: "🎓",
  finance: "💰", property: "🏠", vehicle: "🚗", travel: "✈️", other: "📁" };
const ALWAYS = ["certificates", "resume", "dna", "id", "insurance", "medical"];  // shown even when empty
const niceDate = s => s ? new Date(s.replace(" ", "T")).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "";
const newest = fs => fs.map(f => f.modified || "").sort().pop() || "";
function viewFamily() {
  const papers = D.files.filter(f => f.vault);
  const members = D.people.filter(p => p.family);
  const unsure = papers.filter(f => !f.vault.person_id || !byPerson[f.vault.person_id]);
  const back = (label, fn) => el("button", { class: "mx-btn ghost small", onclick: fn }, icon("left"), label);
  toolbar([], el("span", { class: "meta" }, "Found by the name printed in the paper, or the face in it. You can always change whose it is."));
  $("toolbar").querySelector("input").hidden = !ui.famFolder;
  renderBody = () => {
    if (ui.fam == null) {
      if (!members.length) return $("view").replaceChildren(el("div", { class: "empty-help" },
        el("h3", {}, "No family members yet"),
        el("p", { class: "hint" }, "Open a person on the People tab, give their full name (as printed on their documents) and tick Family member. Their IDs, certificates, resume, insurance, medical papers and passport-size photos get their own folders here and in the sorted copies (Family/<Name>/…)."),
        el("button", { class: "mx-btn solid small", onclick: () => { ui.tab = "people"; remember(); tabs(); render(); } }, "Go to People")));
      const card = (img, title, sub, n, when, fn) => el("div", { class: "pcard", onclick: fn },
        img, el("b", {}, title), sub ? el("span", { class: "pid" }, sub) : null,
        el("span", { class: "stats" }, `${fmt(n)} papers`), when ? el("span", { class: "est" }, `Modified ${niceDate(when)}`) : null);
      return $("view").replaceChildren(el("div", { class: "people" },
        members.map(p => { const fs = papers.filter(f => f.vault.person_id === p.person_id);
          return card(el("img", { src: p.cover ? faceImg(p.cover) : "", alt: "" }), p.name || p.display, pid(p.person_id), fs.length, newest(fs),
            () => { ui.fam = p.person_id; ui.famFolder = null; renderBody(); }); }),
        unsure.length ? card(el("div", { class: "folder-ico" }, "❓"), "Not sure whose", "", unsure.length, newest(unsure),
          () => { ui.fam = "unsure"; ui.famFolder = null; renderBody(); }) : null));
    }
    const who = ui.fam === "unsure" ? null : byPerson[ui.fam];
    const mine = ui.fam === "unsure" ? unsure : papers.filter(f => f.vault.person_id === ui.fam);
    const title = who ? (who.name || who.display) : "Not sure whose";
    if (!ui.famFolder) {
      const keys = D.vault_folders.filter(v => ALWAYS.includes(v.key) || mine.some(f => f.vault.folder === v.key));
      return $("view").replaceChildren(
        el("div", { class: "toolbar" }, back("Family", () => { ui.fam = null; renderBody(); }), el("h3", { class: "crumb" }, title)),
        el("div", { class: "folders" }, keys.map(v => {
          const fs = mine.filter(f => f.vault.folder === v.key);
          return el("button", { class: "folder" + (fs.length ? "" : " empty"), onclick: () => { ui.famFolder = v.key; renderBody(); } },
            el("span", { class: "folder-ico" }, FOLDER_ICON[v.key] || "📁"),
            el("span", { class: "folder-txt" }, el("b", {}, v.name), el("small", {}, v.what),
              el("small", { class: "when" }, fs.length ? `${fmt(fs.length)} · Modified ${niceDate(newest(fs))}` : "Empty")));
        })));
    }
    const folder = D.vault_folders.find(v => v.key === ui.famFolder) || { name: "" };
    const rows = mine.filter(f => f.vault.folder === ui.famFolder && match(f, ui.q));
    const whose = f => el("select", { class: "mx-select", "aria-label": "Whose is it?", onchange: async e => {
      try { await api("/api/vault", { file_id: f.id, person_id: e.target.value, folder: f.vault.folder }); } catch (err) { return; }
      toast("Saved. The sorted copy moves the next time you sort."); await load();
    } }, el("option", { value: "" }, "Whose is it?"), members.map(p => el("option", { value: p.person_id, selected: f.vault.person_id === p.person_id }, p.name || p.display)),
      el("option", { value: "none" }, "Not a family paper"), el("option", { value: "auto" }, "Decide automatically"));
    $("view").replaceChildren(
      el("div", { class: "toolbar" }, back(title, () => { ui.famFolder = null; renderBody(); }), el("h3", { class: "crumb" }, `${FOLDER_ICON[ui.famFolder] || ""} ${folder.name}`)),
      ...table(rows, [T.thumb, T.name, { h: "Type", k: "sub", v: f => f.vault.sub, r: f => f.vault.sub },
        { h: "Modified", k: "modified", r: f => niceDate(f.modified) },
        { h: "Found by", k: "by", v: f => f.vault.by, r: f => ({ name: "name in it", face: "face in it", you: "you chose" })[f.vault.by] || "" },
        T.company, T.amount, { h: "Whose", r: whose }]));
  };
  renderBody();
}
