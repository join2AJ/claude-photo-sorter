/* Sharing app: people see the photos they're in. Plain JS, no build step.
   Screens: welcome -> phone -> code -> selfie -> (pending | blocked | not found) -> consent -> photos.
   ?demo (or the public demo site): runs on made-up data with sample faces; nothing is sent anywhere. */
const DEMO = new URLSearchParams(location.search).has("demo") || !!window.STATIC_DEMO;
const $ = id => document.getElementById(id);
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
const ICON = {
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>', left: '<path d="m15 18-6-6 6-6"/>', right: '<path d="m9 18 6-6-6-6"/>',
  camera: '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3Z"/><circle cx="12" cy="13" r="3"/>',
};
const svg = n => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICON[n]}</svg>`;
function toast(t) { const e = $("toast"); e.textContent = t; e.classList.add("on"); clearTimeout(e.t); e.t = setTimeout(() => e.classList.remove("on"), 3400); }
const niceDate = s => s ? new Date(s.replace(" ", "T")).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "";
const monthName = s => new Date(s.slice(0, 7) + "-01T00:00").toLocaleDateString("en-GB", { month: "long", year: "numeric" });

/* theme */
function setTheme(t) { document.documentElement.dataset.theme = t; $("theme").innerHTML = svg(t === "dark" ? "sun" : "moon"); try { localStorage.setItem("theme", t); } catch (e) {} }
let th = "light"; try { th = localStorage.getItem("theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"); } catch (e) {}
setTheme(th);
$("theme").onclick = () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
$("menu").innerHTML = svg("gear");

/* ---------- the server, or the demo stand-in ---------- */
const server = {
  async call(path, body) {
    const r = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), credentials: "same-origin" } : { cache: "no-store", credentials: "same-origin" });
    const j = await r.json().catch(() => ({ error: "Something went wrong. Try again." }));
    if (j.error) throw new Error(j.error);
    return j;
  },
  me: () => server.call("/share/api/me"),
  code: mobile => server.call("/share/api/code", { mobile }),
  verify: (mobile, code) => server.call("/share/api/verify", { mobile, code }),
  selfie: frames => server.call("/share/api/selfie", { frames }),
  consent: b => server.call("/share/api/consent", b),
  forget: () => server.call("/share/api/forget", {}),
  logout: () => server.call("/share/api/logout", {}),
  thumb: async p => `/share/api/thumb/${p.id}`,
  photo: async p => `/share/api/photo/${p.id}`,
};
const demo = (() => {  // made-up library; blurring is drawn in the page here (the real app blurs on the server)
  let D, st = { stage: "signed-out" };
  try { st = JSON.parse(sessionStorage.getItem("share-demo")) || st; } catch (e) {}
  const save = () => { try { sessionStorage.setItem("share-demo", JSON.stringify(st)); } catch (e) {} };
  const data = async () => D || (D = await fetch("demo/details.json").then(r => r.json()));
  const people = () => Object.fromEntries(D.people.map(p => [p.person_id, p]));
  const visible = (viewer, pid, P) => {
    if (pid === viewer) return true;
    const p = P[pid];
    if (!p || !p.mobile_verified || p.consent !== "yes") return false;
    const hide = (p.hide_from || "").split(",").filter(Boolean).map(Number), share = (p.share_with || "").split(",").filter(Boolean).map(Number);
    return !hide.includes(viewer) && (!share.length || share.includes(viewer));
  };
  async function me() {
    await data();
    const out = { stage: st.stage, mobile: st.mobile, test_mode: true, demo: true };
    if (st.stage !== "approved") return out;
    const P = people(), pid = st.person, faces = Object.fromEntries(D.faces.map(f => [f.face_id, f]));
    const photos = [], others = {};
    D.files.filter(f => f.people_ids.includes(pid) && !f.duplicate_of).forEach(f => {
      const fs = f.face_ids.map(i => faces[i]).filter(Boolean), hidden = fs.filter(x => !visible(pid, x.person_id, P));
      if (f.kind === "video" && hidden.length) return;
      photos.push({ id: f.id, kind: f.kind, taken: f.taken, faces: fs.length, blurred: hidden.length, boxes: hidden.map(x => [x.x, x.y, x.w, x.h]),
        labels: (f.labels || []).filter(t => !P[t]) });
      fs.forEach(x => { const q = P[x.person_id]; if (x.person_id !== pid && q && q.mobile_verified && q.name) others[x.person_id] = q.display; });
    });
    photos.sort((a, b) => (b.taken || "").localeCompare(a.taken || ""));
    const p = P[pid];
    return { ...out, person: { id: pid, name: p.display, consent: p.consent, share_with: p.share_with || "", hide_from: p.hide_from || "" }, photos,
      others: Object.entries(others).map(([id, name]) => ({ id: +id, name })).sort((a, b) => a.name.localeCompare(b.name)) };
  }
  async function draw(p, size) {
    const img = new Image();
    img.src = `demo/thumbs/${p.id}.jpg`;
    await img.decode();
    const c = document.createElement("canvas"), W = img.naturalWidth, s = size / W;
    c.width = c.height = size;
    const ctx = c.getContext("2d");
    ctx.drawImage(img, 0, 0, size, size);
    const small = document.createElement("canvas"), sx = small.getContext("2d");
    (p.boxes || []).forEach(([x, y, w, h]) => {  // pixelate each face that isn't shared
      const m = 0.25, X = (x - w * m) * s, Y = (y - h * m) * s, Wd = w * (1 + 2 * m) * s, Ht = h * (1 + 2 * m) * s;
      small.width = 5; small.height = Math.max(2, Math.round(5 * Ht / Wd));  // a handful of cells: nothing recognisable left
      sx.drawImage(c, X, Y, Wd, Ht, 0, 0, small.width, small.height);
      ctx.imageSmoothingEnabled = true; ctx.drawImage(small, 0, 0, small.width, small.height, X, Y, Wd, Ht);
    });
    return c.toDataURL("image/jpeg", .85);
  }
  return {
    me,
    code: async mobile => { if (!/^\+?\d[\d\s-]{8,}$/.test(mobile)) throw new Error("Enter your mobile number with the country code, like +91 98765 43210."); st.mobile = mobile.replace(/\s/g, "").replace(/^(\d{10})$/, "+91$1"); save(); return { mobile: st.mobile, test_code: "123456" }; },
    verify: async (mobile, code) => { if (code !== "123456") throw new Error("That code isn't right. In the demo it is 123456."); st.stage = "verified"; save(); return me(); },
    selfie: async pick => {
      await data();
      await new Promise(r => setTimeout(r, 1400));
      if (pick === "impostor") st.stage = "blocked";
      else if (pick === "nobody") st.stage = "notfound";
      else { const p = people()[pick]; st.person = pick; st.stage = p.mobile_verified ? "approved" : "pending"; if (!p.mobile_verified) setTimeout(() => { st.stage = "approved"; save(); }, 4000); }
      save(); return me();
    },
    consent: async b => { const p = people()[st.person]; Object.assign(p, { consent: b.consent, mobile_verified: 1, share_with: b.share_with.join(","), hide_from: b.hide_from.join(",") }); st.consented = true; save(); return me(); },
    forget: async () => { people()[st.person].consent = "no"; return me(); },
    logout: async () => { st = { stage: "signed-out" }; save(); return { stage: "signed-out" }; },
    thumb: p => draw(p, 360), photo: p => draw(p, 900),
    samples: async () => { await data(); return D.people.filter(p => p.name).slice(0, 5); },
  };
})();
const api = DEMO ? demo : server;

/* ---------- screens ---------- */
const S = { me: null, mobile: "", filter: "all" };
const STEPS = ["phone", "code", "selfie", "choice"];
function frame(step, ...kids) {
  $("steps").replaceChildren(...STEPS.map((s, i) => el("li", { class: i < STEPS.indexOf(step) ? "done" : s === step ? "now" : "" })));
  $("steps").hidden = !step;
  const sc = el("main", { id: "screen", class: "screen" }, ...kids);
  $("screen").replaceWith(sc);
  document.querySelector(".shell").classList.toggle("wide", !!sc.querySelector(".grid"));
  scrollTo(0, 0);
  return sc;
}
function route(me) {
  S.me = me;
  $("test").hidden = !me.test_mode;
  $("test").textContent = DEMO ? "Demo" : "Test mode";
  $("menu").hidden = me.stage !== "approved";
  stopCamera();
  const screens = { "signed-out": welcome, verified: selfie, notfound: notFound, pending, blocked, denied,
    approved: () => (me.person.consent === "pending" && !S.skipConsent ? consent() : gallery()) };
  (screens[me.stage] || welcome)();
}

function welcome() {
  const face = (bg, blur) => el("i", { class: "p" + (blur ? " blur" : ""), style: `background:${bg}` });
  frame(null,
    el("div", { class: "hero", "aria-hidden": "true" },
      el("div", { class: "card-photo c1" }, face("#b98a62", 1), face("#7a5641", 1)),
      el("div", { class: "card-photo c2" }, face("#8c6a52", 1), face("#d9a77f"), face("#5e4334", 1)),
      el("div", { class: "card-photo c3" }, face("#c69872", 1), face("#9b7158", 1)),
      el("span", { class: "you" }, "You")),
    el("h1", {}, "See the photos you're in"), el("p", { class: "lead" }, "From the album you were invited to. It takes about a minute."),
    el("ul", { class: "points" },
      el("li", {}, el("span", { class: "ico" }, "📱"), el("div", {}, el("b", {}, "Your number, then a quick selfie"), el("span", {}, "So we know it's really you."))),
      el("li", {}, el("span", { class: "ico" }, "🙂"), el("div", {}, el("b", {}, "Your face, your choice"), el("span", {}, "Show it to others in your photos, or keep it blurred."))),
      el("li", {}, el("span", { class: "ico" }, "🫥"), el("div", {}, el("b", {}, "Others are blurred unless they agree"), el("span", {}, "Change your mind any time.")))),
    el("div", { class: "grow" }),
    el("button", { class: "btn primary", onclick: phone }, "Get started"));
}

function phone() {
  const cc = el("select", { class: "input cc", "aria-label": "Country code" }, [["+91", "🇮🇳 +91"], ["+1", "🇺🇸 +1"], ["+44", "🇬🇧 +44"], ["+971", "🇦🇪 +971"], ["+65", "🇸🇬 +65"], ["+61", "🇦🇺 +61"]].map(([v, t]) => el("option", { value: v }, t)));
  const num = el("input", { class: "input", type: "tel", inputmode: "tel", autocomplete: "tel-national", placeholder: "98765 43210", "aria-label": "Mobile number" });
  const err = el("p", { class: "err", role: "alert" });
  const go = el("button", { class: "btn primary", type: "submit" }, "Send code");
  const form = el("form", { class: "screen-form", onsubmit: async e => {
    e.preventDefault(); err.textContent = ""; go.disabled = true; go.textContent = "Sending…";
    const mobile = num.value.trim().startsWith("+") ? num.value.trim() : cc.value + num.value.replace(/\D/g, "");
    try { const r = await api.code(mobile); S.mobile = r.mobile; S.testCode = r.test_code; code(); }
    catch (ex) { err.textContent = ex.message; go.disabled = false; go.textContent = "Send code"; }
  } });
  frame("phone", el("h1", {}, "Your mobile number"), el("p", { class: "lead" }, "We'll text you a 6-digit code to check it's yours."),
    form);
  form.append(el("div", { class: "field-row" }, cc, num), err, el("div", { style: "height:8px" }), go,
    el("p", { class: "small" }, "Your number is only used to sign you in and to tell you if someone tries to use your face."));
  num.focus();
}

function code() {
  const boxes = Array.from({ length: 6 }, (_, i) => el("input", { class: "input", inputmode: "numeric", maxlength: 1, "aria-label": `Digit ${i + 1}`, autocomplete: i ? "off" : "one-time-code" }));
  const err = el("p", { class: "err", role: "alert" });
  const value = () => boxes.map(b => b.value).join("");
  const submit = async () => {
    if (value().length < 6) return;
    err.textContent = "";
    try { route(await api.verify(S.mobile, value())); }
    catch (ex) { err.textContent = ex.message; boxes.forEach(b => b.value = ""); boxes[0].focus(); }
  };
  const fill = digits => { digits.slice(0, 6).split("").forEach((d, i) => boxes[i].value = d); boxes[Math.min(5, digits.length)].focus(); submit(); };
  boxes.forEach((b, i) => {
    b.oninput = () => { b.value = b.value.replace(/\D/g, ""); if (b.value.length > 1) return fill(b.value); if (b.value && i < 5) boxes[i + 1].focus(); submit(); };
    b.onkeydown = e => { if (e.key === "Backspace" && !b.value && i) boxes[i - 1].focus(); };
    b.onpaste = e => { e.preventDefault(); fill((e.clipboardData.getData("text") || "").replace(/\D/g, "")); };
  });
  let left = 30;
  const resend = el("button", { class: "link", disabled: true, onclick: async () => {
    try { const r = await api.code(S.mobile); S.testCode = r.test_code; toast("New code sent."); code(); } catch (ex) { err.textContent = ex.message; }
  } }, "Resend in 30 s");
  const t = setInterval(() => { left--; if (!resend.isConnected) return clearInterval(t); resend.textContent = left > 0 ? `Resend in ${left} s` : "Send a new code"; resend.disabled = left > 0; if (left <= 0) clearInterval(t); }, 1000);
  frame("code", el("h1", {}, "Enter the code"), el("p", { class: "lead" }, `We sent it to ${S.mobile}.`),
    S.testCode ? el("div", { class: "hintbox" }, el("span", {}, DEMO ? "Demo code" : "Test mode: no SMS service yet. Your code"), el("b", {}, S.testCode),
      el("span", { class: "spacer" }), el("button", { class: "chip", onclick: () => fill(S.testCode) }, "Fill in")) : null,
    el("div", { class: "otp" }, boxes), err,
    el("div", { class: "center", style: "display:flex;justify-content:space-between" }, el("button", { class: "link", onclick: phone }, "Change number"), resend));
  boxes[0].focus();
}

/* live selfie: three pictures while turning the head a little */
let stream;
function stopCamera() { if (stream) stream.getTracks().forEach(t => t.stop()); stream = null; }
async function selfie() {
  if (DEMO) return demoSelfie();
  const video = el("video", { playsinline: true, autoplay: true, muted: true });
  const ring = el("div", { class: "ring" }), say = el("div", { class: "say" }, "Starting the camera…"), count = el("div", { class: "count" });
  const shots = [0, 1, 2].map(() => el("i"));
  const err = el("p", { class: "err", role: "alert" });
  const start = el("button", { class: "btn primary", disabled: true });
  start.innerHTML = svg("camera") + " Start";
  frame("selfie", el("h1", {}, "A quick selfie"), el("p", { class: "lead" }, "Fit your face in the circle. We'll take three pictures while you turn your head a little."),
    el("div", { class: "cam" }, video, el("div", { class: "mask" }), ring, count, say), el("div", { class: "shots" }, shots), err, start,
    el("p", { class: "small center" }, "Only a small face picture is kept, to match you with your photos."));
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: { ideal: 720 }, height: { ideal: 960 } }, audio: false });
    video.srcObject = stream;
    await video.play();
    say.textContent = "Look straight at the camera"; start.disabled = false;
  } catch (e) {
    say.textContent = "";
    err.textContent = "We can't use your camera. Allow camera access for this page in your browser settings, then reload.";
    return;
  }
  start.onclick = async () => {
    start.disabled = true; err.textContent = "";
    const frames = [];
    const steps = ["Look straight at the camera", "Turn your head a little to the left", "Now a little to the right"];
    for (let i = 0; i < 3; i++) {
      say.textContent = steps[i];
      for (let n = 3; n > 0; n--) { count.textContent = n; await new Promise(r => setTimeout(r, 650)); }
      count.textContent = "";
      const c = el("canvas"); c.width = video.videoWidth; c.height = video.videoHeight;
      c.getContext("2d").drawImage(video, 0, 0);
      frames.push(c.toDataURL("image/jpeg", .85));
      shots[i].style.backgroundImage = `url(${frames[i]})`; shots[i].classList.add("taken");
      ring.classList.add("ok"); setTimeout(() => ring.classList.remove("ok"), 300);
    }
    stopCamera();
    checking();
    try { route(await api.selfie(frames)); }
    catch (ex) { await selfie(); $("screen").querySelector(".err").textContent = ex.message; }
  };
}
async function demoSelfie() {
  const people = await demo.samples();
  const pick = async who => { checking(); route(await demo.selfie(who)); };
  frame("selfie", el("h1", {}, "A quick selfie"),
    el("p", { class: "lead" }, "In the app you take a live selfie and turn your head a little. In this demo, pick who you are:"),
    el("div", { class: "samples" },
      people.map(p => el("button", { class: "sample", onclick: () => pick(p.person_id) }, el("img", { src: `demo/faces/${p.cover}.jpg`, alt: "" }), p.display.split(" ")[0],
        el("small", {}, p.mobile_verified ? "registered" : "new: owner confirms"))),
      el("button", { class: "sample bad", onclick: () => pick("impostor") }, el("img", { src: `demo/faces/${people[0].cover}.jpg`, alt: "" }), "Impostor",
        el("small", {}, `uses ${people[0].display.split(" ")[0]}'s face`)),
      el("button", { class: "sample", onclick: () => pick("nobody") }, el("span", { style: "font-size:40px;line-height:64px" }, "🙂"), "Stranger", el("small", {}, "not in any photo"))),
    el("p", { class: "small" }, "Your face picture is compared with the faces in the album. Face matching can be wrong, so new people are confirmed by the album owner."));
}
function checking() { frame("selfie", el("div", { class: "spin" }), el("h2", { class: "center", style: "text-align:center" }, "Checking it's really you…"), el("p", { class: "lead", style: "text-align:center" }, "Matching your face with the album.")); }

function stateScreen(ico, cls, title, text, ...actions) {
  frame(null, el("div", { class: `state-ico ${cls}` }, ico), el("h1", { style: "text-align:center" }, title),
    el("p", { class: "lead", style: "text-align:center" }, text), el("div", { class: "grow" }), ...actions);
}
function pending() {
  stateScreen("⏳", "wait", "Almost there", "We found you in the album. The album owner will confirm it's you, then your photos appear here.",
    el("button", { class: "btn primary", onclick: async () => route(await api.me()) }, "Check again"),
    el("button", { class: "btn ghost", onclick: signOut }, "Sign out"));
  clearInterval(S.poll);
  S.poll = setInterval(async () => { if (!$("screen").querySelector(".state-ico.wait")) return clearInterval(S.poll); const m = await api.me(); if (m.stage !== "pending") { clearInterval(S.poll); route(m); } }, 4000);
}
function blocked() {
  stateScreen("⚠️", "bad", "This face is already registered", "It belongs to someone who signed up with another number. If this is really you, contact the album owner. They have been told about this attempt.",
    el("button", { class: "btn", onclick: signOut }, "Sign out"));
}
function denied() {
  stateScreen("✋", "bad", "Not confirmed", "The album owner didn't confirm this sign-up. Contact them if you think it's a mistake.",
    el("button", { class: "btn", onclick: selfie }, "Try the selfie again"), el("button", { class: "btn ghost", onclick: signOut }, "Sign out"));
}
function notFound() {
  stateScreen("🔍", "wait", "We couldn't find you", "You don't seem to be in any photo of this album yet, or your face was too small or turned away.",
    el("button", { class: "btn primary", onclick: selfie }, "Try the selfie again"), el("button", { class: "btn ghost", onclick: signOut }, "Sign out"));
}

/* consent: show my face to others, or blur it */
function consentForm(onSave, saveText) {
  const p = S.me.person;
  const draft = { consent: p.consent === "pending" ? "" : p.consent,
    share_with: new Set(p.share_with.split(",").filter(Boolean).map(Number)), hide_from: new Set(p.hide_from.split(",").filter(Boolean).map(Number)) };
  const save = el("button", { class: "btn primary", disabled: !draft.consent, onclick: async () => {
    save.disabled = true;
    try { await onSave({ consent: draft.consent, share_with: [...draft.share_with], hide_from: [...draft.hide_from] }); }
    catch (ex) { toast(ex.message); save.disabled = false; }
  } }, saveText);
  const opt = (v, title, text, blur) => {
    const b = el("button", { class: "choice", role: "radio", "aria-checked": draft.consent === v, onclick: () => {
      draft.consent = v; b.parentElement.querySelectorAll(".choice").forEach(x => x.setAttribute("aria-checked", x === b)); save.disabled = false; more.hidden = v !== "yes";
    } }, el("span", { class: "demo-face" + (blur ? " blur" : "") }, el("i")), el("span", {}, el("b", {}, title), el("span", {}, text)), el("span", { class: "dot" }));
    return b;
  };
  const pickList = (set, cls) => el("div", { class: "people-pick " + cls }, S.me.others.length ? S.me.others.map(o => {
    const b = el("button", { "aria-pressed": set.has(o.id), onclick: () => { set.has(o.id) ? set.delete(o.id) : set.add(o.id); b.setAttribute("aria-pressed", set.has(o.id)); } }, o.name);
    return b;
  }) : el("p", { class: "small" }, "No one else in your photos has signed up yet."));
  const more = el("details", { class: "more", hidden: draft.consent !== "yes" }, el("summary", {}, "Choose who exactly (optional)"),
    el("p", { class: "small" }, "Only show my face to:"), pickList(draft.share_with, ""),
    el("p", { class: "small" }, "Always hide my face from:"), pickList(draft.hide_from, "hide"));
  return [el("div", { class: "choices", role: "radiogroup", "aria-label": "Your face in group photos" },
    opt("yes", "Show my face", "People in the same photos can see you.", false),
    opt("no", "Blur my face", "Others see a blur where you are. You still see yourself.", true)), more, save];
}
function consent() {
  frame("choice", el("h1", {}, "Your face in group photos"),
    el("p", { class: "lead" }, `${S.me.photos.length} photos found. Do you want the other people in them to see your face?`),
    ...consentForm(async b => { S.skipConsent = true; route(await api.consent(b)); }, "Save and see my photos"),
    el("p", { class: "small" }, "You can change this any time in settings. Every change is recorded with the date."));
}

/* photos */
async function gallery() {
  const me = S.me, p = me.person;
  const counts = {};
  me.photos.forEach(x => (x.labels || []).forEach(t => { if (!/^(morning|afternoon|evening|late night|weekend|happy|neutral|sad|surprised|angry|scared|disgusted|contempt|video|screenshot|document)$/.test(t)) counts[t] = (counts[t] || 0) + 1; }));
  const tags = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 6).map(t => t[0]);
  const list = () => me.photos.filter(x => S.filter === "all" || (S.filter === "blurred" ? x.blurred : (x.labels || []).includes(S.filter)));
  const blurredN = me.photos.filter(x => x.blurred).length;
  const grid = el("div", { class: "grid" });
  const render = () => {
    const xs = list();
    grid.replaceChildren();
    if (!xs.length) { grid.append(el("p", { class: "empty", style: "grid-column:1/-1" }, "No photos here.")); return; }
    let last = "";
    xs.forEach((x, i) => {
      const m = (x.taken || "").slice(0, 7);
      if (m && m !== last && S.filter === "all") { last = m; grid.append(el("div", { class: "month", style: "grid-column:1/-1" }, monthName(m))); }
      const img = el("img", { alt: "", loading: "lazy" });
      const tile = el("button", { class: "tile", "aria-label": `Photo from ${niceDate(x.taken)}`, onclick: () => viewer(xs, i) }, img, x.blurred ? el("span", { class: "b" }, `${x.blurred} blurred`) : null);
      grid.append(tile);
      lazy(img, x);
    });
  };
  const chips = el("div", { class: "filters", role: "toolbar", "aria-label": "Filter" },
    [["all", `All ${me.photos.length}`], ...(blurredN ? [["blurred", `With blurred faces ${blurredN}`]] : []), ...tags.map(t => [t, `${t} ${counts[t]}`])].map(([k, t]) =>
      el("button", { "aria-pressed": S.filter === k, onclick: e => { S.filter = k; chips.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", b === e.currentTarget)); render(); } }, t)));
  frame(null,
    el("div", { class: "me" }, el("div", { class: "avatar" }, (p.name || "?").trim()[0]),
      el("div", { class: "who" }, el("b", {}, p.name), el("span", { class: "small" }, me.mobile),
        el("span", { class: "pill" + (p.consent === "yes" ? "" : " off") }, p.consent === "yes" ? "Your face is shown to others" : "Your face is blurred for others"))),
    el("p", { class: "lead" }, `${me.photos.length} photos you're in${blurredN ? ` · ${blurredN} have faces blurred because those people haven't agreed` : ""}.`),
    chips, grid);
  render();
}
const io = "IntersectionObserver" in window ? new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { io.unobserve(e.target); e.target._load(); } }), { rootMargin: "300px" }) : null;
function lazy(img, x) {
  img._load = async () => { try { img.src = await api.thumb(x); img.onload = () => img.classList.add("in"); } catch (e) {} };
  io ? io.observe(img) : img._load();
}
function viewer(xs, i) {
  const x = xs[i];
  const img = el("img", { alt: `Photo from ${niceDate(x.taken)}` });
  api.photo(x).then(u => img.src = u);
  const close = () => { box.remove(); removeEventListener("keydown", keys); };
  const go = d => { const j = i + d; if (j >= 0 && j < xs.length) { close(); viewer(xs, j); } };
  const keys = e => { if (e.key === "Escape") close(); if (e.key === "ArrowLeft") go(-1); if (e.key === "ArrowRight") go(1); };
  addEventListener("keydown", keys);
  let sx = null;
  const stage = el("div", { class: "stage", ontouchstart: e => sx = e.touches[0].clientX, ontouchend: e => { if (sx == null) return; const dx = e.changedTouches[0].clientX - sx; if (Math.abs(dx) > 50) go(dx < 0 ? 1 : -1); sx = null; } }, img);
  const btn = (n, label, fn) => { const b = el("button", { class: "icon-btn", "aria-label": label, onclick: fn }); b.innerHTML = svg(n); return b; };
  const box = el("div", { class: "viewer", role: "dialog", "aria-label": "Photo" },
    el("div", { class: "top" }, btn("x", "Close", close), el("span", { class: "spacer" }), el("span", { class: "small", style: "color:#bbb" }, `${i + 1} of ${xs.length}`),
      el("span", { class: "spacer" }), btn("left", "Previous", () => go(-1)), btn("right", "Next", () => go(1))),
    stage,
    el("div", { class: "info" }, el("b", {}, niceDate(x.taken) || "No date"),
      el("span", {}, `${x.faces} ${x.faces === 1 ? "face" : "faces"}${x.blurred ? ` · ${x.blurred} blurred because they haven't agreed to share` : " · everyone in it agreed"}`)));
  document.body.append(box);
}

/* settings */
function settings() {
  const close = () => scrim.remove();
  const scrim = el("div", { class: "scrim", onclick: e => e.target === scrim && close() },
    el("div", { class: "panel", role: "dialog", "aria-label": "Settings" }, el("div", { class: "grab" }),
      el("h2", {}, "Your face in group photos"),
      ...consentForm(async b => { route(await api.consent(b)); close(); toast("Saved. It applies straight away."); }, "Save"),
      el("hr", { style: "border:0;border-top:1px solid var(--hair);width:100%" }),
      el("button", { class: "btn danger", onclick: async () => {
        if (!confirm("Blur your face for everyone, and ask the album owner to delete your face data?")) return;
        route(await api.forget()); close(); toast("Done. Your face is blurred for everyone and the owner has been asked to delete your data.");
      } }, "Blur me everywhere and ask to delete my data"),
      el("button", { class: "btn ghost", onclick: () => { close(); signOut(); } }, "Sign out")));
  $("sheet").replaceChildren(scrim);
}
$("menu").onclick = settings;
async function signOut() { route(await api.logout()); }

(async () => { try { route(await api.me()); } catch (e) { welcome(); toast("Can't reach the photo sorter. Is it running?"); } })();
