import { BaseStrategy } from './base_strategy.js';

export class HomeTriageStrategy extends BaseStrategy {
    renderResults(data, container, message) {
        // Robust check for array-like objects
        let analysisData = data;
        if (!Array.isArray(data) && typeof data === 'object' && data !== null) {
            if (Object.keys(data).every(key => !isNaN(parseInt(key)))) {
                analysisData = Object.values(data);
            }
        }

        if (Array.isArray(analysisData)) {
            console.log("Rendering Home Triage Cards...");

            const messageHtml = message ?
                `<h5 class="text-sm font-bold uppercase tracking-wide mb-4 text-brand-accent">${message}</h5>` : '';

            const cardsHtml = this.renderDimensionCards(analysisData);

            // 1. Render content
            container.innerHTML = messageHtml + cardsHtml;

            // 2. Explicitly create and append button to ensure it appears
            const btnContainer = document.createElement('div');
            btnContainer.className = "mt-6 flex justify-end";

            const btn = document.createElement('button');
            btn.id = "save-triage-btn";
            btn.className = "bg-green-600 hover:bg-green-500 text-white px-6 py-3 rounded-lg font-medium transition-all hover:scale-105 active:scale-95 shadow-lg shadow-green-900/20 flex items-center gap-2";
            btn.innerHTML = '<span>💾</span> Save to Vault';

            btn.onclick = () => {
                console.log("Save button clicked");
                this.saveToVault(analysisData);
            };

            btnContainer.appendChild(btn);
            container.appendChild(btnContainer);

            // 3. Update styling
            container.className = "glass-panel p-6 rounded-2xl border-l-4 border-brand-accent bg-brand-accent/5";

        } else {
            // Fallback to base
            super.renderResults(data, container, message);
        }
    }

    renderDimensionCards(data) {
        return `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                ${data.map((item, index) => {
            let colorClass = 'text-green-400';
            let bgClass = 'bg-green-500/10';
            let borderClass = 'border-green-500/20';

            // Map backend severity to frontend styles
            if (item.severity === 'red') {
                colorClass = 'text-red-400';
                bgClass = 'bg-red-500/10';
                borderClass = 'border-red-500/20';
            } else if (item.severity === 'yellow') {
                colorClass = 'text-yellow-400';
                bgClass = 'bg-yellow-500/10';
                borderClass = 'border-yellow-500/20';
            }

            return `
                        <div class="glass-panel p-4 rounded-xl border ${borderClass} ${bgClass} flex flex-col justify-between h-full animate-fade-in" style="animation-delay: ${index * 100}ms">
                            <div>
                                <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">${item.dimension}</h4>
                                <p class="text-lg font-semibold ${colorClass}">${item.status}</p>
                            </div>
                             <div class="mt-4 pt-3 border-t border-slate-700/50 flex justify-between items-center">
                                <span class="text-xs text-slate-400">${item.focus || 'Analysis'}</span>
                                <span class="text-xs font-mono bg-slate-800 px-2 py-1 rounded text-slate-300">
                                    ${(item.confidence * 100).toFixed(0)}% Conf
                                </span>
                            </div>
                        </div>
                    `;
        }).join('')}
            </div>
        `;
    }

    async saveToVault(data) {
        if (!data) {
            alert("No analysis data to save!");
            return;
        }

        try {
            const response = await fetch(`/api/run/home_triage`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data: {
                        action: "save_analysis",
                        payload: data
                    }
                })
            });

            const result = await response.json();
            if (result.status === "success") {
                alert("✅ Saved to Vault! ID: " + result.data.id);
            } else {
                alert("❌ Save failed: " + result.message);
            }

        } catch (e) {
            console.error("Save error:", e);
            alert("Error saving to vault.");
        }
    }
}
