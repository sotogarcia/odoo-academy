// Civil Service widget (ESM, Odoo v18)

class CivilServiceWidget extends HTMLElement {
  static get observedAttributes() {
    return ["data-url"];
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._abortController = null;
  }

  connectedCallback() {
    this._load();
  }

  disconnectedCallback() {
    if (this._abortController) this._abortController.abort();
  }

  attributeChangedCallback(name, _old, _new) {
    if (name === "data-url" && this.isConnected) this._load();
  }

  async _load() {
    const url = this.getAttribute("data-url");
    if (!url) return this._renderError("Missing attribute: data-url.");

    this._renderLoading();

    if (this._abortController) this._abortController.abort();
    this._abortController = new AbortController();

    try {
      const res = await fetch(url, {
        method: "GET",
        credentials: "same-origin",
        signal: this._abortController.signal,
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });

      if (!res.ok) {
        return this._renderError(
          `HTTP ${res.status}: ${res.statusText || "Error"}`
        );
      }

      const html = await res.text();
      this._renderHTML(html);
    } catch (err) {
      if (err.name === "AbortError") return; // navigation/unmount
      this._renderError(`Failed to load content: ${err.message}`);
    }
  }

  _renderLoading() {
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        .loading { font: 14px/1.4 system-ui, -apple-system, Segoe UI, Roboto;
                   opacity:.7; }
      </style>
      <p class="loading">Loading…</p>
    `;
  }

  _renderError(msg) {
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        .err { color:#b71c1c; font: 14px/1.4 system-ui, -apple-system; }
        code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
      </style>
      <p class="err">Error: <code></code></p>
    `;
    this.shadowRoot.querySelector("code").textContent = String(msg);
  }

  _renderHTML(html) {
    // Trusts same-origin route; ensure the backend only serves safe HTML
    this.shadowRoot.innerHTML = html;
  }
}

// Avoid "Already defined" during dev/hot reload
if (!customElements.get("civil-service-widget")) {
  customElements.define("civil-service-widget", CivilServiceWidget);
}

// optional: export an empty object to mark this file as a module
// export {};
