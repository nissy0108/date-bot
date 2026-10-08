(() => {
  const views = {
    login: document.getElementById("view-login"),
    main: document.getElementById("view-main"),
    results: document.getElementById("view-results"),
  };
  const loadingEl = document.getElementById("loading");
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("login-error");
  const chatLog = document.getElementById("chat-log");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const slotsForm = document.getElementById("slots-form");
  const globalSlotsSummary = document.getElementById("global-slots-summary");
  const tabChat = document.getElementById("tab-chat");
  const tabSlots = document.getElementById("tab-slots");
  const panelChat = document.getElementById("panel-chat");
  const panelSlots = document.getElementById("panel-slots");
  const btnHistoryToggle = document.getElementById("btn-history-toggle");
  const resultsSlots = document.getElementById("results-slots");
  const planCards = document.getElementById("plan-cards");
  const historyPanel = document.getElementById("history-panel");
  const historyList = document.getElementById("history-list");
  const historyEmpty = document.getElementById("history-empty");
  const toastEl = document.getElementById("toast");
  const btnExportResults = document.getElementById("btn-export-results");

  let state = {
    slots: {},
    messages: [],
    last_plans: null,
    plan_history: [],
    slot_options: null,
  };
  let resultsExportId = null;
  let toastTimer = null;
  let activeMainTab = "chat";
  let historyExpanded = false;

  const HISTORY_COLLAPSE_AFTER = 3;
  const HISTORY_COLLAPSED_MAX = 2;

  const chipHosts = {
    budget: document.getElementById("budget-options"),
    time_slot: document.getElementById("time-options"),
    area: document.getElementById("area-options"),
    mood: document.getElementById("mood-options"),
    avoid_areas: document.getElementById("avoid-options"),
  };
  const otherInputs = {
    budget: document.getElementById("budget-other"),
    time_slot: document.getElementById("time-other"),
    area: document.getElementById("area-other"),
    mood: document.getElementById("mood-other"),
    avoid_areas: document.getElementById("avoid-other"),
  };

  function showView(name) {
    Object.entries(views).forEach(([key, el]) => {
      el.hidden = key !== name;
    });
  }

  function setMainTab(name) {
    activeMainTab = name === "slots" ? "slots" : "chat";
    const chatOn = activeMainTab === "chat";
    if (tabChat) {
      tabChat.classList.toggle("is-active", chatOn);
      tabChat.setAttribute("aria-selected", chatOn ? "true" : "false");
    }
    if (tabSlots) {
      tabSlots.classList.toggle("is-active", !chatOn);
      tabSlots.setAttribute("aria-selected", chatOn ? "false" : "true");
    }
    if (panelChat) panelChat.hidden = !chatOn;
    if (panelSlots) panelSlots.hidden = chatOn;
    if (chatOn && chatInput) {
      chatInput.focus({ preventScroll: true });
    }
  }

  function setLoading(on) {
    loadingEl.hidden = !on;
    document.querySelectorAll("button[type='submit'], #btn-edit-slots").forEach((b) => {
      b.disabled = on;
    });
  }

  function apiErrorMessage(data, status) {
    const d = data?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d.map((x) => x.msg || x.message || JSON.stringify(x)).join(", ");
    }
    return data?.message || `HTTP ${status}`;
  }

  async function api(path, options = {}) {
    const res = await fetch(path, {
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    if (res.status === 401 && path !== "/api/login") {
      showView("login");
      throw new Error("login required");
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(apiErrorMessage(data, res.status));
    }
    return data;
  }

  function renderMessages(messages) {
    chatLog.innerHTML = "";
    (messages || []).forEach((m) => {
      const isUser = m.role === "user";
      const row = document.createElement("div");
      row.className = `msg msg-${isUser ? "user" : "bot"}`;

      const meta = document.createElement("div");
      meta.className = "msg-meta";

      const avatar = document.createElement("div");
      avatar.className = `avatar avatar-${isUser ? "user" : "bot"}`;
      avatar.setAttribute("aria-hidden", "true");
      avatar.innerHTML = isUser
        ? '<svg viewBox="0 0 24 24" width="22" height="22"><circle cx="12" cy="8.5" r="3.5" fill="currentColor"/><path d="M5 19.5c1.8-3.2 4-4.5 7-4.5s5.2 1.3 7 4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
        : '<svg viewBox="0 0 32 28" width="20" height="18"><path d="M16 26 C16 26 2 16 2 9 C2 4.5 5.5 2 9 2 C12 2 14.5 4 16 6.5 C17.5 4 20 2 23 2 C26.5 2 30 4.5 30 9 C30 16 16 26 16 26 Z" fill="currentColor"/></svg>';

      const name = document.createElement("span");
      name.className = "msg-name";
      name.textContent = isUser ? "あなた" : "デートBot";

      meta.appendChild(avatar);
      meta.appendChild(name);

      const bubble = document.createElement("div");
      bubble.className = `bubble bubble-${isUser ? "user" : "bot"}`;
      bubble.textContent = m.content;

      row.appendChild(meta);
      row.appendChild(bubble);
      chatLog.appendChild(row);
    });
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function selectedValues(key) {
    const host = chipHosts[key];
    const mode = host.dataset.mode;
    const pressed = [...host.querySelectorAll('.chip[aria-pressed="true"]')].map(
      (b) => b.dataset.value
    );
    const other = (otherInputs[key].value || "").trim();
    if (mode === "single") {
      if (other) return other;
      return pressed[0] || null;
    }
    const list = [...pressed];
    if (other) {
      other.split(/[、,/]+/).forEach((p) => {
        const t = p.trim();
        if (t && !list.includes(t)) list.push(t);
      });
    }
    return list;
  }

  function syncChipsFromSlots(slots) {
    Object.entries(chipHosts).forEach(([key, host]) => {
      const mode = host.dataset.mode;
      let current = slots?.[key];
      if (key === "mood" && typeof current === "string") {
        current = current.split(/[、,/]+/).map((s) => s.trim()).filter(Boolean);
      }
      if (key === "budget" && current != null) current = String(current);

      [...host.querySelectorAll(".chip")].forEach((btn) => {
        const v = btn.dataset.value;
        if (mode === "single") {
          btn.setAttribute("aria-pressed", current === v ? "true" : "false");
        } else {
          const arr = Array.isArray(current) ? current : [];
          btn.setAttribute("aria-pressed", arr.includes(v) ? "true" : "false");
        }
      });

      // if current is custom (not in options), put into other
      const opts = [...host.querySelectorAll(".chip")].map((b) => b.dataset.value);
      if (mode === "single") {
        if (current && !opts.includes(String(current))) {
          otherInputs[key].value = String(current);
        } else {
          otherInputs[key].value = "";
        }
      } else {
        const arr = Array.isArray(current) ? current : [];
        const customs = arr.filter((v) => !opts.includes(v));
        otherInputs[key].value = customs.join("、");
      }
    });
  }

  function buildChipRows(options) {
    if (!options) return;
    const map = {
      budget: options.budget,
      time_slot: options.time_slot,
      area: options.area,
      mood: options.mood,
      avoid_areas: options.avoid_areas,
    };
    Object.entries(map).forEach(([key, list]) => {
      const host = chipHosts[key];
      host.innerHTML = "";
      (list || []).forEach((value) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "chip";
        btn.dataset.value = value;
        btn.textContent = key === "budget" ? `${value}円` : value;
        btn.setAttribute("aria-pressed", "false");
        btn.addEventListener("click", () => {
          if (host.dataset.mode === "single") {
            [...host.querySelectorAll(".chip")].forEach((b) =>
              b.setAttribute("aria-pressed", b === btn ? "true" : "false")
            );
            otherInputs[key].value = "";
          } else {
            const on = btn.getAttribute("aria-pressed") === "true";
            btn.setAttribute("aria-pressed", on ? "false" : "true");
          }
        });
        host.appendChild(btn);
      });
    });
  }

  function renderPlans(plans, container) {
    const host = container || planCards;
    host.innerHTML = "";
    (plans || []).forEach((p, i) => {
      const card = document.createElement("article");
      card.className = "plan-card";
      card.innerHTML = `
        <p class="plan-label">案${i + 1}</p>
        <p class="plan-body"></p>
        <p class="plan-reason"></p>
      `;
      card.querySelector(".plan-body").textContent = p.plan || "";
      card.querySelector(".plan-reason").textContent = p.reason
        ? `理由: ${p.reason}`
        : "";
      host.appendChild(card);
    });
  }

  function showToast(message, durationMs = 2400) {
    if (toastEl) {
      toastEl.textContent = message;
      toastEl.hidden = false;
      if (toastTimer) clearTimeout(toastTimer);
      toastTimer = setTimeout(() => {
        toastEl.hidden = true;
      }, durationMs);
    } else {
      alert(message);
    }
  }

  function notifyUser(message) {
    showToast(message, 3200);
  }

  /** 条件タブ等ではチャットが隠れるため、Bot 返答を見せる */
  function revealBotFeedback(data) {
    if (data.view_hint === "login") return;
    if (data.view_hint === "results" && data.last_plans?.length) return;
    const msgs = data.messages || [];
    if (!msgs.length) return;
    setMainTab("chat");
    requestAnimationFrame(() => {
      chatLog.scrollTop = chatLog.scrollHeight;
    });
  }

  function notifyFromLastBotMessage(data) {
    const msgs = data.messages || [];
    const last = msgs[msgs.length - 1];
    if (last?.role !== "bot") return;
    const line = String(last.content || "").split("\n")[0].trim();
    if (line) notifyUser(line.length > 72 ? `${line.slice(0, 69)}…` : line);
  }

  function latestPlanHistoryId() {
    const history = state.plan_history || [];
    if (!history.length) return null;
    return history[history.length - 1].id;
  }

  async function fetchExportText(planHistoryId) {
    const formatted = await api("/api/export/format", {
      method: "POST",
      body: JSON.stringify({ plan_history_id: planHistoryId }),
    });
    return formatted.text || "";
  }

  function copyTextWithFallback(text) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.top = "0";
    ta.style.left = "0";
    ta.style.width = "2em";
    ta.style.height = "2em";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    ta.setSelectionRange(0, text.length);
    let ok = false;
    try {
      ok = document.execCommand("copy");
    } catch {
      ok = false;
    }
    document.body.removeChild(ta);
    return ok;
  }

  async function copyExportText(_planHistoryId, textPromise) {
    if (window.ClipboardItem && navigator.clipboard?.write) {
      try {
        const item = new ClipboardItem({
          "text/plain": textPromise.then(
            (t) => new Blob([t], { type: "text/plain" })
          ),
        });
        await navigator.clipboard.write([item]);
        return await textPromise;
      } catch {
        /* fall through */
      }
    }
    const text = await textPromise;
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        return text;
      } catch {
        /* fall through */
      }
    }
    if (copyTextWithFallback(text)) return text;
    throw new Error("コピーに失敗したよ。ブラウザの権限を確認してね");
  }

  async function exportPlanSet(planHistoryId) {
    const id = Number(planHistoryId);
    if (!id) {
      alert("コピーする候補セットが見つからないよ");
      return;
    }
    const textPromise = fetchExportText(id);
    setLoading(true);
    try {
      const text = await copyExportText(id, textPromise);
      await api("/api/export/log", {
        method: "POST",
        body: JSON.stringify({ plan_history_id: id, text }),
      });
      showToast("コピーしたよ");
    } catch (err) {
      alert(err.message || "エクスポートに失敗したよ");
    } finally {
      setLoading(false);
    }
  }

  function formatHistoryTime(ts) {
    if (!ts) return "";
    try {
      const d = new Date(Number(ts) * 1000);
      return d.toLocaleString("ja-JP", {
        month: "numeric",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  }

  function renderHistory(history) {
    const items = Array.isArray(history) ? history : [];
    if (historyPanel) {
      historyPanel.hidden = items.length === 0;
    }
    if (items.length === 0) {
      historyExpanded = false;
    }
    historyList.innerHTML = "";
    if (historyEmpty) historyEmpty.hidden = true;

    const reversed = [...items].reverse();
    const shouldCollapse = items.length > HISTORY_COLLAPSE_AFTER && !historyExpanded;
    const visible = shouldCollapse
      ? reversed.slice(0, HISTORY_COLLAPSED_MAX)
      : reversed;

    if (btnHistoryToggle) {
      if (items.length > HISTORY_COLLAPSE_AFTER) {
        btnHistoryToggle.hidden = false;
        btnHistoryToggle.textContent = historyExpanded
          ? "たたむ"
          : "すべての履歴を見る";
      } else {
        btnHistoryToggle.hidden = true;
      }
    }

    visible.forEach((batch) => {
      const wrap = document.createElement("article");
      wrap.className = "history-batch";
      wrap.innerHTML = `
        <div class="history-batch-head">
          <div class="history-batch-head-main">
            <h3 class="history-batch-title"></h3>
            <span class="history-batch-time"></span>
          </div>
          <button type="button" class="btn btn-ghost btn-sm btn-export">コピー</button>
        </div>
        <p class="history-batch-slots"></p>
        <div class="plan-cards"></div>
      `;
      wrap.querySelector(".history-batch-title").textContent =
        `候補セット #${batch.id}`;
      wrap.querySelector(".history-batch-time").textContent =
        formatHistoryTime(batch.created_at);
      wrap.querySelector(".history-batch-slots").textContent =
        batch.slots_summary || formatSlotsLocal(batch.slots);
      renderPlans(batch.plans || [], wrap.querySelector(".plan-cards"));
      wrap.querySelectorAll(".btn-export").forEach((btn) => {
        btn.dataset.planHistoryId = String(batch.id);
      });
      historyList.appendChild(wrap);
    });
  }

  function formatSlotsLocal(slots) {
    if (!slots) return "";
    const avoid = slots.avoid_areas || [];
    const avoidS = Array.isArray(avoid)
      ? avoid.length
        ? avoid.join("、")
        : "なし"
      : avoid || "なし";
    const budgetS = "budget" in slots ? `${slots.budget}円` : "予算未定";
    const areaS =
      slots.area ||
      (slots.mood || slots.time_slot || Object.prototype.hasOwnProperty.call(slots, "budget")
        ? "仮（優先エリア）"
        : "エリア未定");
    return (
      `${budgetS} / ` +
      `${slots.time_slot || "時間未定"} / ` +
      `${areaS} / ` +
      `mood ${slots.mood || "なし"} / ` +
      `除外 ${avoidS}`
    );
  }

  function applyState(data) {
    state = { ...state, ...data };
    if (data.slot_options) buildChipRows(data.slot_options);
    const summaryText =
      data.slots_summary || "まだ条件なし — 条件タブかおしゃべりで決めよう";
    if (globalSlotsSummary) globalSlotsSummary.textContent = summaryText;
    resultsSlots.textContent = data.slots_summary || summaryText;
    renderMessages(data.messages || []);
    syncChipsFromSlots(data.slots || {});
    if (data.last_plans) renderPlans(data.last_plans);
    renderHistory(data.plan_history || state.plan_history || []);

    const history = data.plan_history || state.plan_history || [];
    resultsExportId =
      history.length > 0 ? history[history.length - 1].id : null;
    if (btnExportResults) {
      btnExportResults.disabled = !resultsExportId;
    }

    if (data.view_hint === "results" && data.last_plans?.length) {
      showView("results");
    } else if (data.view_hint === "login") {
      showView("login");
    } else {
      showView("main");
    }
  }

  function collectSlotsPatch() {
    const budget = selectedValues("budget");
    const time_slot = selectedValues("time_slot");
    const area = selectedValues("area");
    const moodList = selectedValues("mood");
    const avoid = selectedValues("avoid_areas");

    const patch = {
      budget: budget,
      time_slot: time_slot,
      area: area,
      mood: Array.isArray(moodList) ? (moodList.length ? moodList.join("、") : null) : moodList,
      avoid_areas: Array.isArray(avoid) ? avoid : avoid ? [avoid] : [],
    };
    return patch;
  }

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    loginError.hidden = true;
    const password = document.getElementById("login-password").value.trim();
    setLoading(true);
    try {
      const data = await api("/api/login", {
        method: "POST",
        body: JSON.stringify({ password }),
      });
      applyState(data);
    } catch (err) {
      loginError.textContent = err.message || "ログインに失敗したよ";
      loginError.hidden = false;
    } finally {
      setLoading(false);
    }
  });

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message) return;
    setLoading(true);
    try {
      const data = await api("/api/chat", {
        method: "POST",
        body: JSON.stringify({ message }),
      });
      chatInput.value = "";
      applyState(data);
      if (!(data.view_hint === "results" && data.last_plans?.length)) {
        revealBotFeedback(data);
      }
    } catch (err) {
      notifyUser(err.message || "送信に失敗したよ");
    } finally {
      setLoading(false);
    }
  });

  slotsForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fromSlotsTab = activeMainTab === "slots";
    setLoading(true);
    try {
      const data = await api("/api/slots", {
        method: "POST",
        body: JSON.stringify({ slots: collectSlotsPatch() }),
      });
      applyState(data);
      if (!(data.view_hint === "results" && data.last_plans?.length)) {
        revealBotFeedback(data);
        if (fromSlotsTab) notifyFromLastBotMessage(data);
      }
    } catch (err) {
      notifyUser(err.message || "条件の反映に失敗したよ");
    } finally {
      setLoading(false);
    }
  });

  async function doReset() {
    const fromSlotsTab = activeMainTab === "slots";
    setLoading(true);
    try {
      const data = await api("/api/reset", { method: "POST", body: "{}" });
      applyState(data);
      revealBotFeedback(data);
      if (fromSlotsTab) notifyFromLastBotMessage(data);
    } catch (err) {
      notifyUser(err.message || "reset失敗");
    } finally {
      setLoading(false);
    }
  }

  document.getElementById("btn-reset").addEventListener("click", doReset);
  document.getElementById("btn-results-reset").addEventListener("click", doReset);

  document.getElementById("btn-logout").addEventListener("click", async () => {
    await api("/api/logout", { method: "POST", body: "{}" });
    showView("login");
  });

  document.getElementById("btn-edit-slots").addEventListener("click", () => {
    showView("main");
    setMainTab("slots");
  });

  if (tabChat) tabChat.addEventListener("click", () => setMainTab("chat"));
  if (tabSlots) tabSlots.addEventListener("click", () => setMainTab("slots"));

  if (btnHistoryToggle) {
    btnHistoryToggle.addEventListener("click", () => {
      historyExpanded = !historyExpanded;
      renderHistory(state.plan_history || []);
    });
  }

  if (btnExportResults) {
    btnExportResults.addEventListener("click", () => {
      exportPlanSet(latestPlanHistoryId() ?? resultsExportId);
    });
  }

  historyList.addEventListener("click", (e) => {
    const btn = e.target.closest(".btn-export");
    if (!btn || !historyList.contains(btn)) return;
    const raw = btn.dataset.planHistoryId;
    exportPlanSet(raw ? Number(raw) : null);
  });

  setMainTab("chat");

  // boot: try restore session
  (async () => {
    try {
      const data = await api("/api/state");
      applyState(data);
    } catch {
      showView("login");
    }
  })();
})();
