class CivilServiceWidget extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  async connectedCallback() {
    const url = this.getAttribute("data-url");
    if (!url) {
      this.shadowRoot.innerHTML = `<p>Error: falta el atributo <code>data-url</code>.</p>`;
      return;
    }

    try {
      const response = await fetch(url);
      if (!response.ok) {
        this.shadowRoot.innerHTML = `<p>Error ${response.status}: ${response.statusText}</p>`;
        return;
      }
      const html = await response.text();
      this.shadowRoot.innerHTML = html;
    } catch (err) {
      this.shadowRoot.innerHTML = `<p>Error al cargar contenido: ${err.message}</p>`;
    }
  }
}

customElements.define("civil-service-widget", CivilServiceWidget);
