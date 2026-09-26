const $ = (sel) => document.querySelector(sel);

const state = { file: null, pack: null };

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
};

function setStatus(message, isError = false, busy = false) {
  el.status.hidden = !message;
  el.status.className = "status" + (isError ? " error" : "");
  el.status.innerHTML = busy ? `<span class="spinner"></span>${message}` : message;
}

async function loadConfig() {
  const cfg = await fetch("/api/config").then((r) => r.json());
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
            }</td><td>${escapeHtml(v.meaning)}</td><td>${escapeHtml(v.example)}</td></tr>`
        )
        .join("")}</tbody></table>`
    : "<p>No vocabulary extracted.</p>";

  renderQuiz(pack.questions || []);

  $("#panel-source").innerHTML = `<h3>Text read from your upload</h3><pre class="source">${escapeHtml(
    pack.detected_text || "(empty)"
  )}</pre>`;
}

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
