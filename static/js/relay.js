// RELAY client glue (F1). HTMX does the work; this only handles the drawer and transport errors.
(() => {
  const drawer = () => document.getElementById("drawer");

  // Close the drawer on Escape or scrim click.
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && drawer()?.firstElementChild) drawer().replaceChildren();
  });
  document.addEventListener("click", (e) => {
    if (e.target === drawer() || e.target.closest("[data-drawer-close]")) drawer().replaceChildren();
  });

  // Engagement switcher: POST to the selected engagement's own URL.
  document.addEventListener("change", (e) => {
    const form = e.target.closest("[data-engagement-switch]");
    if (!form) return;
    form.action = e.target.selectedOptions[0].dataset.href;
    form.submit();
  });

  // "finding-json": validate_finding takes JSON {edited_body, note}. Form fields named
  // body.<key> become edited_body[key]; data-type="int" / "list" (one per line) are typed.
  const defineExtensions = () => {
    htmx.defineExtension("finding-json", {
      onEvent(name, evt) {
        if (name === "htmx:configRequest") evt.detail.headers["Content-Type"] = "application/json";
      },
      encodeParameters(xhr, parameters, elt) {
        xhr.overrideMimeType("text/json");
        const form = elt.closest("form");
        const out = {};
        const edited = {};
        for (const [key, value] of parameters.entries ? parameters.entries() : Object.entries(parameters)) {
          if (!key.startsWith("body.")) { if (value !== "") out[key] = value; continue; }
          const field = form?.querySelector(`[name="${CSS.escape(key)}"]`);
          const type = field?.dataset.type;
          edited[key.slice(5)] = type === "int" ? Number(value)
            : type === "list" ? String(value).split("\n").map((s) => s.trim()).filter(Boolean)
            : value;
        }
        if (Object.keys(edited).length) out.edited_body = edited;
        return JSON.stringify(out);
      },
    });
  };
  if (window.htmx) defineExtensions(); else document.addEventListener("DOMContentLoaded", defineExtensions);

  // AI failures come back as a designed error partial with HTTP 502: render it in the
  // nearest #stage-error slot (or in place) instead of dropping it.
  document.addEventListener("htmx:beforeSwap", (e) => {
    if (e.detail.xhr.status !== 502) return;
    e.detail.shouldSwap = true;
    e.detail.isError = false;
    const slot = document.getElementById("stage-error");
    if (slot) { e.detail.target = slot; e.detail.swapOverride = "innerHTML"; }
  });

  // Findings re-rendered successfully (synthesize or its retry): clear any stale error.
  document.addEventListener("htmx:afterSwap", (e) => {
    if (e.detail.xhr.status >= 400 || e.detail.target.id !== "findings") return;
    const slot = document.getElementById("stage-error");
    if (slot) slot.innerHTML = "";
  });

  // A finding was validated: let passport rows on the page refresh themselves.
  // afterSettle, not afterSwap: the replacement card must be in the page first.
  document.addEventListener("htmx:afterSettle", (e) => {
    if (e.detail.target?.classList?.contains("finding") || e.detail.elt?.closest?.(".finding")) {
      document.body.dispatchEvent(new Event("relay:validated"));
    }
  });

  // Each finding swaps in place, so the page-level tally and the Complete
  // validation button are recounted here from the cards themselves.
  document.body.addEventListener("relay:validated", () => {
    const cards = document.querySelectorAll("#findings .finding");
    const done = document.querySelectorAll("#findings .finding--approved, #findings .finding--rejected").length;
    const pending = cards.length - done;
    const count = document.querySelector("[data-validated-count]");
    if (count) count.textContent = done;
    const text = document.querySelector("[data-pending-text]");
    if (text) text.textContent = pending ? `${pending} finding${pending === 1 ? "" : "s"} still pending.` : "All findings reviewed.";
    const btn = document.querySelector("[data-complete-validation]");
    if (btn) btn.disabled = pending > 0 || btn.dataset.canAct !== "true";
  });

  // Cancel inside a <details> editor closes it.
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-close-details]");
    if (btn) btn.closest("details")?.removeAttribute("open");
  });

  // Transport failures (server down, 5xx) get a toast. AI failures are rendered by the
  // server as designed error states and never reach this path.
  const toast = (msg) => {
    const host = document.getElementById("toasts");
    if (!host) return;
    const el = document.createElement("div");
    el.className = "toast";
    el.setAttribute("role", "alert");
    el.textContent = msg;
    host.append(el);
    setTimeout(() => el.remove(), 6000);
  };
  document.addEventListener("htmx:responseError", (e) => {
    if (e.detail.xhr.status !== 502) toast(`Request failed (${e.detail.xhr.status}). Nothing was changed.`);
  });
  document.addEventListener("htmx:sendError", () =>
    toast("RELAY server unreachable. Check that it is running."));
})();
