export class BaseStrategy {
    constructor(metadata) {
        this.metadata = metadata;
    }

    renderResults(data, container, message) {
        // Default generic rendering
        const messageHtml = message ?
            `<h5 class="text-sm font-bold uppercase tracking-wide mb-4 text-brand-accent">${message}</h5>` : '';

        let contentHtml = '';
        if (typeof data === 'object') {
            contentHtml = `<pre class="text-white text-sm overflow-x-auto">${JSON.stringify(data, null, 2)}</pre>`;
        } else {
            contentHtml = `<p class="text-white text-lg">${data}</p>`;
        }

        container.innerHTML = messageHtml + contentHtml;
        // Keep container styles consistent with app.js default or update if needed
        // App.js sets default glass panel styles on the ResultArea div.
    }
}
