const $ = (sel) => document.querySelector(sel);

const state = { file: null, pack: null, themes: [], theme: null, instructor: null };

const el = {
  target: $("#target-lang"),
  native: $("#native-lang"),
  level: $("#level"),
  drop: $("#dropzone"),
  input: $("#file-input"),
  preview: $("#preview"),
  dropText: $("#dropzone-text"),
  scan: $("#scan-btn"),
  status: $("#status"),
  results: $("#results"),
  title: $("#pack-title"),
  aiStatus: $("#ai-status"),
  themePicker: $("#theme-picker"),
  charPicker: $("#char-picker"),
  mascotLeft: $("#mascot-left"),
  instructor: $("#instructor"),
  instructorImg: $("#instructor-img"),
  bubble: $("#instructor-bubble"),
};

const themeToggle = $("#theme-toggle");

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  themeToggle.textContent = theme === "dark" ? "Light mode" : "Dark mode";
  localStorage.setItem("theme", theme);
}

applyTheme(localStorage.getItem("theme") || "light");
themeToggle.addEventListener("click", () =>
  applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark")
);

function setStatus(message, isError = false, busy = false) {
  el.status.hidden = !message;
  el.status.className = "status" + (isError ? " error" : "");
  el.status.innerHTML = busy ? `<span class="spinner"></span>${message}` : message;
}

function speak(text, lang) {
  if (!text || !window.speechSynthesis) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = { ja: "ja-JP", zh: "zh-CN", ko: "ko-KR", es: "es-ES", fr: "fr-FR", de: "de-DE",
    it: "it-IT", pt: "pt-PT", ru: "ru-RU", hi: "hi-IN", ar: "ar-SA", en: "en-US" }[lang] || "en-US";
  utterance.rate = 0.85;
  speechSynthesis.cancel();
  speechSynthesis.speak(utterance);
}

function applyWorld(themeId, charId) {
  const theme = state.themes.find((t) => t.id === themeId) || state.themes[0];
  if (!theme) return;
  state.theme = theme;
  const character = theme.characters.find((c) => c.id === charId) || theme.characters[0];
  state.instructor = character;
  localStorage.setItem("world", theme.id);
  localStorage.setItem("instructor", character.id);

  document.documentElement.style.setProperty("--bg-image", `url("${theme.background}")`);
  el.instructorImg.src = character.image;
  el.bubble.textContent = `${character.name} (${character.title}): ${character.greeting}`;
  el.instructor.hidden = false;

  const buddy = theme.characters.find((c) => c.id !== character.id);
  el.mascotLeft.src = buddy ? buddy.image : "";
  el.mascotLeft.hidden = !buddy;

  el.themePicker.querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.id === theme.id));
  renderCharPicker();
}

function renderCharPicker() {
  el.charPicker.innerHTML = state.theme.characters
    .map(
      (c) => `<button type="button" data-id="${c.id}" class="pick${c.id === state.instructor.id ? " on" : ""}">
        <img src="${c.image}" alt="" /><span>${escapeHtml(c.name)}<small>${escapeHtml(c.title)}</small></span></button>`
    )
    .join("");
  el.charPicker.querySelectorAll("button").forEach((btn) =>
    btn.addEventListener("click", () => applyWorld(state.theme.id, btn.dataset.id))
  );
}

function renderThemePicker() {
  el.themePicker.innerHTML = state.themes
    .map(
      (t) => `<button type="button" data-id="${t.id}" class="pick wide">
        <img src="${t.background}" alt="" /><span>${escapeHtml(t.name)}</span></button>`
    )
    .join("");
  el.themePicker.querySelectorAll("button").forEach((btn) =>
    btn.addEventListener("click", () => applyWorld(btn.dataset.id, null))
  );
}

async function loadConfig() {
  const cfg = await fetch("/api/config").then((r) => r.json());
  state.themes = cfg.themes || [];
  if (state.themes.length) {
    renderThemePicker();
    applyWorld(localStorage.getItem("world"), localStorage.getItem("instructor"));
  }
  for (const lang of cfg.languages) {
    el.target.add(new Option(lang.name, lang.code));
    el.native.add(new Option(lang.name, lang.code));
  }
  el.target.value = localStorage.getItem("target") || "ja";
  el.native.value = localStorage.getItem("native") || "en";
  el.level.value = localStorage.getItem("level") || "beginner";
  el.aiStatus.textContent = cfg.ai_enabled
    ? `AI analysis on · ${cfg.model}`
    : "Demo mode — no API key configured, local OCR only";
  el.aiStatus.classList.toggle("warn", !cfg.ai_enabled);
}

for (const key of ["target", "native", "level"]) {
  el[key].addEventListener("change", () => localStorage.setItem(key, el[key].value));
}

function pickFile(file) {
  if (!file) return;
  state.file = file;
  el.scan.disabled = false;
  if (file.type.startsWith("image/")) {
    el.preview.src = URL.createObjectURL(file);
    el.preview.hidden = false;
  } else {
    el.preview.hidden = true;
  }
  el.dropText.innerHTML = `<strong>${file.name}</strong><span>${Math.round(file.size / 1024)} KB — click to change</span>`;
  setStatus("");
}

el.drop.addEventListener("click", () => el.input.click());
el.drop.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") el.input.click();
});
el.input.addEventListener("change", (e) => pickFile(e.target.files[0]));
["dragenter", "dragover"].forEach((ev) =>
  el.drop.addEventListener(ev, (e) => {
    e.preventDefault();
    el.drop.classList.add("dragging");
  })
);
["dragleave", "drop"].forEach((ev) =>
  el.drop.addEventListener(ev, (e) => {
    e.preventDefault();
    el.drop.classList.remove("dragging");
  })
);
el.drop.addEventListener("drop", (e) => pickFile(e.dataTransfer.files[0]));
document.addEventListener("paste", (e) => {
  const item = [...(e.clipboardData?.files || [])][0];
  if (item) pickFile(item);
});

el.scan.addEventListener("click", async () => {
  if (!state.file) return;
  el.scan.disabled = true;
  setStatus("Scanning and building your study pack…", false, true);
  const body = new FormData();
  body.append("file", state.file);
  body.append("target_lang", el.target.value);
  body.append("native_lang", el.native.value);
  body.append("level", el.level.value);
  body.append("instructor", state.instructor?.id || "");
  try {
    const res = await fetch("/api/scan", { method: "POST", body });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Scan failed");
    state.pack = data;
    render(data);
    setStatus("");
    el.results.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    el.scan.disabled = false;
  }
});

document.querySelectorAll(".tab").forEach((tab) =>
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === tab));
    document.querySelectorAll(".panel").forEach((p) => {
      p.hidden = p.id !== `panel-${tab.dataset.tab}`;
    });
  })
);

const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const list = (items) => `<ul>${items.map((i) => `<li>${escapeHtml(i)}</li>`).join("")}</ul>`;

function render(pack) {
  el.results.hidden = false;
  el.title.textContent = pack.title || "Study pack";

  $("#panel-summary").innerHTML = `
    <h3>Summary</h3><p>${escapeHtml(pack.summary)}</p>
    ${pack.key_points?.length ? `<h3>Key points</h3>${list(pack.key_points)}` : ""}
    ${
      pack.grammar?.length
        ? `<h3>Grammar in this material</h3>${pack.grammar
            .map(
              (g) =>
                `<li><strong>${escapeHtml(g.pattern)}</strong> — ${escapeHtml(g.explanation)}<br /><em>${escapeHtml(
                  g.example
                )}</em></li>`
            )
            .join("")}`
        : ""
    }`;

  $("#panel-notes").innerHTML = `
    <h3>Copy these into your notebook</h3>
    ${(pack.notes || [])
      .map((n, i) => `<div class="note-line"><span class="num">${i + 1}.</span><span>${escapeHtml(n)}</span></div>`)
      .join("") || "<p>No notes generated.</p>"}
    <button class="option" id="copy-notes" style="margin-top:14px">Copy all notes</button>`;
  $("#copy-notes")?.addEventListener("click", (e) => {
    navigator.clipboard.writeText((pack.notes || []).join("\n"));
    e.target.textContent = "Copied!";
  });

  $("#panel-vocab").innerHTML = pack.vocabulary?.length
    ? `<h3>Vocabulary</h3><table><thead><tr><th>Word</th><th>Meaning</th><th>Example</th></tr></thead><tbody>
      ${pack.vocabulary
        .map(
          (v) =>
            `<tr><td class="term">${escapeHtml(v.term)}${
              v.reading ? `<span class="reading">${escapeHtml(v.reading)}</span>` : ""
            }<button class="say" data-word="${escapeHtml(
              v.term
            )}">&#128266;</button></td><td>${escapeHtml(v.meaning)}</td><td>${escapeHtml(v.example)}</td></tr>`
        )
        .join("")}</tbody></table>`
    : "<p>No vocabulary extracted.</p>";
  wireSay($("#panel-vocab"));

  renderQuiz(pack.questions || []);
  renderSpelling(pack.vocabulary || []);

  $("#panel-source").innerHTML = `<h3>Text read from your upload</h3><pre class="source">${escapeHtml(
    pack.detected_text || "(empty)"
  )}</pre>`;
}

async function spellCard(word) {
  const res = await fetch("/api/spell", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ word, target_lang: el.target.value }),
  });
  const data = await res.json();
  return `<div class="spell-word">
      <div class="spell-head"><strong>${escapeHtml(data.word)}</strong>
        <button class="say" data-word="${escapeHtml(data.word)}">&#128266; Say it</button></div>
      <div class="letters">${data.letters
        .map(
          (l) => `<span class="letter ${escapeHtml(l.script)}"><b>${escapeHtml(l.char)}</b>
            <small>${escapeHtml(l.reading)}</small></span>`
        )
        .join("")}</div>
      ${data.romaji ? `<p class="romaji">Sounds like: ${escapeHtml(data.romaji)}</p>` : ""}
      <p class="tip">${escapeHtml(data.tip)}</p>
    </div>`;
}

function wireSay(container) {
  container.querySelectorAll(".say").forEach((btn) =>
    btn.addEventListener("click", () => speak(btn.dataset.word, el.target.value))
  );
}

async function renderSpelling(vocabulary) {
  const panel = $("#panel-spell");
  if (!vocabulary.length) {
    panel.innerHTML = "<p>No words to spell yet.</p>";
    return;
  }
  panel.innerHTML = '<h3>How to write &amp; say each word</h3><p class="tip">Loading…</p>';
  const cards = await Promise.all(vocabulary.slice(0, 12).map((v) => spellCard(v.term)));
  panel.innerHTML = "<h3>How to write &amp; say each word</h3>" + cards.join("");
  wireSay(panel);
}

async function runSpellLookup() {
  const word = $("#spell-input").value.trim();
  if (!word) return;
  const out = $("#spell-out");
  out.innerHTML = '<p class="tip"><span class="spinner"></span>Looking it up…</p>';
  out.innerHTML = await spellCard(word);
  wireSay(out);
}

$("#spell-btn").addEventListener("click", runSpellLookup);
$("#spell-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") runSpellLookup();
});

function renderQuiz(questions) {
  const panel = $("#panel-quiz");
  if (!questions.length) {
    panel.innerHTML = "<p>No questions generated.</p>";
    return;
  }
  panel.innerHTML = `<h3>Practice questions</h3>${questions
    .map(
      (q, i) => `
      <div class="question" data-i="${i}">
        <div class="prompt">${i + 1}. ${escapeHtml(q.prompt)}</div>
        ${
          q.type === "mcq"
            ? `<div class="options">${(q.options || [])
                .map((o) => `<button class="option" data-value="${escapeHtml(o)}">${escapeHtml(o)}</button>`)
                .join("")}</div>`
            : `<div class="answer-row"><input type="text" class="answer" placeholder="Type your answer…" />
               <button class="check">Check</button></div>`
        }
        <div class="feedback" hidden></div>
      </div>`
    )
    .join("")}`;

  panel.querySelectorAll(".question").forEach((node) => {
    const q = questions[Number(node.dataset.i)];
    const feedback = node.querySelector(".feedback");

    node.querySelectorAll(".option").forEach((btn) =>
      btn.addEventListener("click", () => {
        const correct = btn.dataset.value === q.answer;
        node.querySelectorAll(".option").forEach((b) => {
          b.classList.toggle("correct", b.dataset.value === q.answer);
          b.classList.toggle("wrong", b === btn && !correct);
        });
        feedback.hidden = false;
        feedback.className = "feedback " + (correct ? "good" : "bad");
        feedback.textContent = (correct ? "Correct! " : "Not quite. ") + (q.explanation || "");
      })
    );

    node.querySelector(".check")?.addEventListener("click", async (e) => {
      const given = node.querySelector(".answer").value.trim();
      if (!given) return;
      e.target.disabled = true;
      feedback.hidden = false;
      feedback.className = "feedback";
      feedback.innerHTML = '<span class="spinner"></span>Checking…';
      try {
        const res = await fetch("/api/grade", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: q.prompt,
            expected: q.answer,
            given,
            target_lang: el.target.value,
            native_lang: el.native.value,
          }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Grading failed");
        feedback.className = "feedback " + (data.correct ? "good" : "bad");
        feedback.textContent = `${data.correct ? "Correct" : "Needs work"} (${data.score}/100) — ${data.feedback}`;
      } catch (err) {
        feedback.className = "feedback bad";
        feedback.textContent = err.message;
      } finally {
        e.target.disabled = false;
      }
    });
  });
}

loadConfig();
