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

  // [data-fill="#target" data-fill-from="#template"]: copy a <template>'s text into a field.
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-fill]");
    if (!btn) return;
    const target = document.querySelector(btn.dataset.fill);
    const source = document.querySelector(btn.dataset.fillFrom);
    if (target && source) {
      target.value = source.content ? source.content.textContent.trim() : source.textContent.trim();
      target.dispatchEvent(new Event("input", { bubbles: true }));
      target.focus();
    }
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
  document.addEventListener("htmx:responseError", (e) =>
    toast(`Request failed (${e.detail.xhr.status}). Nothing was changed.`));
  document.addEventListener("htmx:sendError", () =>
    toast("RELAY server unreachable. Check that it is running."));
})();
