import { BaseStrategy } from './base_strategy.js';

export class PharmacyStrategy extends BaseStrategy {
    renderResults(data, container, message) {
        // Validation: data should be an object with { drugs: [], summary: "" }
        if (!data || !data.drugs) {
            super.renderResults(data, container, message);
            return;
        }

        console.log("Rendering Pharmacy Cards...");

        const messageHtml = message ?
            `<h5 class="text-sm font-bold uppercase tracking-wide mb-4 text-brand-accent">${message}</h5>` : '';

        // 1. Render Summary if present
        let summaryHtml = '';
        if (data.summary) {
            summaryHtml = `
                <div class="glass-panel p-6 rounded-2xl border-l-4 border-blue-500 bg-blue-500/5 mb-6">
                     <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Patient Summary</h4>
                     <p class="text-slate-200 leading-relaxed">${data.summary}</p>
                </div>
            `;
        }

        // 2. Render Drug Cards
        const cardsHtml = this.renderDrugCards(data.drugs);

        // 3. Assemble
        container.innerHTML = messageHtml + summaryHtml + cardsHtml;

        // 4. Save Button
        const btnContainer = document.createElement('div');
        btnContainer.className = "mt-6 flex justify-end";

        const btn = document.createElement('button');
        btn.id = "save-pharmacy-btn";
        btn.className = "bg-green-600 hover:bg-green-500 text-white px-6 py-3 rounded-lg font-medium transition-all hover:scale-105 active:scale-95 shadow-lg shadow-green-900/20 flex items-center gap-2";
        btn.innerHTML = '<span>💾</span> Save to Vault';

        btn.onclick = () => {
            console.log("Save button clicked");
            this.saveToVault(data);
        };

        btnContainer.appendChild(btn);
        container.appendChild(btnContainer);

        // 5. Container styling
        container.className = "space-y-6";
    }

    renderDrugCards(drugs) {
        if (!Array.isArray(drugs)) return '';

        return `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                ${drugs.map((drug, index) => this.renderSingleDrugCard(drug, index)).join('')}
            </div>
        `;
    }

    renderSingleDrugCard(drug, index) {
        // drug = { name, smiles, checks: [{label, value, status}, ...] }

        const checksHtml = drug.checks.map(check => {
            let colorClass = 'text-slate-300';
            let icon = '•';

            if (check.status === 'green') {
                colorClass = 'text-green-400';
                icon = '✓';
            } else if (check.status === 'yellow') {
                colorClass = 'text-yellow-400';
                icon = '⚠️';
            } else if (check.status === 'red') {
                colorClass = 'text-red-400';
                icon = '🛑';
            }

            return `
                <div class="flex justify-between items-start py-2 border-b border-slate-700/30 last:border-0 hover:bg-white/5 px-2 rounded transition-colors">
                    <div class="flex-1">
                        <span class="text-xs font-bold uppercase text-slate-500 block mb-0.5">${check.label}</span>
                        <span class="text-sm ${colorClass}">${icon} ${check.value}</span>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="glass-panel p-5 rounded-xl border border-slate-700 bg-slate-800/40 flex flex-col h-full animate-fade-in" style="animation-delay: ${index * 150}ms">
                <div class="mb-4 border-b border-slate-700 pb-3">
                    <h4 class="text-lg font-bold text-white flex items-center gap-2">
                        💊 ${drug.name}
                    </h4>
                    <code class="text-[10px] text-slate-500 font-mono block mt-1 truncate" title="${drug.smiles}">${drug.smiles}</code>
                </div>
                <div class="flex-1 space-y-1 overflow-y-auto max-h-[400px] custom-scrollbar">
                    ${checksHtml}
                </div>
            </div>
        `;
    }

    async saveToVault(data) {
        if (!data) {
            alert("No analysis data to save!");
            return;
        }

        try {
            const response = await fetch(`/api/run/pharmacy`, {
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
