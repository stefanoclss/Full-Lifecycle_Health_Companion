import { getStrategy } from './strategies/index.js?v=8';

// State
let currentStrategyId = null;
let currentMetadata = null;

// DOM Elements
const navContainer = document.getElementById('sidebar-nav');
const contentArea = document.getElementById('content-area');
const pageTitle = document.getElementById('page-title');

// Initialize
async function init() {
    try {
        const response = await fetch('/api/strategies');
        const strategies = await response.json();
        renderSidebar(strategies);

        // Auto-load first strategy
        if (strategies.length > 0) {
            loadStrategy(strategies[0]);
        }
    } catch (error) {
        console.error("Failed to load strategies:", error);
        contentArea.innerHTML = `<div class="text-red-500">Failed to connect to server. Ensure backend is running.</div>`;
    }
}

// Render Sidebar
function renderSidebar(strategies) {
    navContainer.innerHTML = strategies.map(s => `
        <button 
            onclick="window.loadStrategyById('${s.id}')"
            class="w-full text-left px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors flex items-center gap-3 group"
            data-id="${s.id}"
        >
            <div class="w-2 h-8 bg-slate-700 rounded-full group-hover:bg-brand-accent transition-colors"></div>
            <div>
                <div class="text-sm font-medium text-slate-200 group-hover:text-white">${s.title.replace(/^[^\s]+\s/, '')}</div>
                <div class="text-xs text-slate-500 group-hover:text-slate-400 truncate w-40">${s.description}</div>
            </div>
        </button>
    `).join('');
}

// Load Strategy Wrapper (Exposed to window for onclick)
window.loadStrategyById = async function (id) {
    const buttons = navContainer.querySelectorAll('button');
    buttons.forEach(btn => {
        if (btn.dataset.id === id) {
            btn.classList.add('bg-slate-800');
            const indicator = btn.querySelector('.bg-slate-700');
            if (indicator) indicator.classList.add('bg-brand-accent');
        } else {
            btn.classList.remove('bg-slate-800');
            const indicator = btn.querySelector('.bg-slate-700');
            if (indicator) indicator.classList.remove('bg-brand-accent');
        }
    });

    const response = await fetch('/api/strategies');
    const strategies = await response.json();
    const strategy = strategies.find(s => s.id === id);
    if (strategy) loadStrategy(strategy);
}


// Render Strategy Content
function loadStrategy(strategy) {
    currentStrategyId = strategy.id;
    currentMetadata = strategy;
    pageTitle.textContent = strategy.title;

    let html = `
        <div class="max-w-4xl mx-auto animate-fade-in space-y-8">
            <!-- Header Card -->
            <div class="glass-panel p-6 rounded-2xl">
                <h3 class="text-2xl font-bold text-white mb-2">${strategy.title}</h3>
                <p class="text-slate-400">${strategy.description}</p>
            </div>
    `;

    // Render Content (Tables, Charts, Text)
    if (strategy.content && strategy.content.length > 0) {
        html += `<div class="grid gap-6">`;
        strategy.content.forEach(item => {
            if (item.type === 'text') {
                const style = item.style === 'highlight' ? 'text-xl font-mono text-brand-accent' :
                    item.style === 'info' ? 'text-blue-400 animate-pulse' : 'text-slate-300';
                html += `<div class="glass-panel p-4 rounded-xl ${style}">${item.text}</div>`;
            } else if (item.type === 'table') {
                html += renderTable(item);
            } else if (item.type === 'chart') {
                html += `<div class="glass-panel p-6 rounded-xl"><canvas id="chart-${strategy.id}"></canvas></div>`;
            }
        });
        html += `</div>`;
    }

    // Render Inputs
    if (strategy.inputs && strategy.inputs.length > 0) {
        html += `<div class="glass-panel p-6 rounded-2xl space-y-4">
            ${strategy.inputs.map(input => `
                <div>
                    <label class="block text-sm font-medium text-slate-400 mb-2">${input.label}</label>
                    <input type="${input.type}" id="input-${input.name}" placeholder="${input.placeholder || ''}" 
                           class="w-full bg-brand-dark border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-accent transition-colors">
                </div>
            `).join('')}
        </div>`;
    }

    // Render Actions (only visible ones)
    if (strategy.actions) {
        const visibleActions = strategy.actions.filter(a => !a.hidden);

        if (visibleActions.length > 0) {
            html += `<div class="flex flex-wrap gap-4">
                ${visibleActions.map(action => `
                    <button onclick="window.executeAction('${action.name}')" 
                            class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-lg font-medium transition-all hover:scale-105 active:scale-95 shadow-lg shadow-blue-900/20">
                        ${action.label}
                    </button>
                `).join('')}
            </div>`;
        }
    }

    // Result Area (Always render it, and let strategy module populate it if it wants)
    html += `<div id="result-area" class="hidden glass-panel p-6 rounded-2xl border-l-4 border-brand-accent bg-brand-accent/5"></div>`;

    // Custom Container for strategies that take over the UI (like detailed Intake)
    html += `<div id="strategy-custom-container"></div>`;

    html += `</div>`; // End container

    contentArea.innerHTML = html;

    // Post-render initialization (Charts)
    if (strategy.content) {
        strategy.content.forEach(item => {
            if (item.type === 'chart') {
                renderChart(`chart-${strategy.id}`, item);
            }
        });
    }

    // INITIALIZE STRATEGY MODULE
    // This allows the strategy to render custom UI immediately (e.g. Chat interface)
    const strategyModule = getStrategy(currentStrategyId, currentMetadata);
    const customContainer = document.getElementById('strategy-custom-container');

    // We pass null data to indicate "initial load"
    if (strategyModule && typeof strategyModule.renderResults === 'function') {
        strategyModule.renderResults(null, customContainer, null);
    }
}

function renderTable(item) {
    return `
        <div class="glass-panel rounded-xl overflow-hidden">
            <table class="w-full text-left">
                <thead class="bg-slate-800/50 text-slate-400 text-xs uppercase">
                    <tr>${item.headers.map(h => `<th class="px-6 py-3">${h}</th>`).join('')}</tr>
                </thead>
                <tbody class="divide-y divide-slate-800">
                    ${item.rows.map(row => `
                        <tr class="hover:bg-slate-800/30 transition-colors">
                            ${row.map(cell => `<td class="px-6 py-4 text-sm text-slate-300">${cell}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function renderChart(canvasId, config) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {
        type: config.chart_type,
        data: {
            labels: config.data.map(d => `Day ${d.x}`),
            datasets: [{
                label: config.label,
                data: config.data.map(d => d.y),
                borderColor: config.color,
                backgroundColor: config.color + '20',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#94a3b8' } } },
            scales: {
                y: { grid: { color: '#1e293b' }, ticks: { color: '#64748b' } },
                x: { grid: { color: '#1e293b' }, ticks: { color: '#64748b' } }
            }
        }
    });
}

// Execute Action with Backend (Exposed to window)
window.executeAction = async function (actionName) {
    const resultArea = document.getElementById('result-area');
    resultArea.classList.remove('hidden');
    resultArea.innerHTML = `<div class="flex items-center gap-3 text-slate-400"><div class="animate-spin h-5 w-5 border-2 border-brand-accent border-t-transparent rounded-full"></div> Processing with MedGemma...</div>`;

    // Gather Inputs
    const data = { action: actionName };
    if (currentMetadata.inputs) {
        currentMetadata.inputs.forEach(input => {
            const val = document.getElementById(`input-${input.name}`).value;
            data[input.name] = val;
        });
    }

    try {
        const response = await fetch(`/api/run/${currentStrategyId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data })
        });
        const result = await response.json();

        console.log("Result received:", result);

        // DELEGATE RENDERING TO STRATEGY MODULE
        const strategyModule = getStrategy(currentStrategyId, currentMetadata);
        strategyModule.renderResults(result.data, resultArea, result.message);

        // FALLBACK: If strategy module didn't add save button, add it here
        if (currentStrategyId === 'home_triage' && !resultArea.querySelector('#save-triage-btn')) {
            console.log("Fallback: Adding save button from app.js");
            const btnDiv = document.createElement('div');
            btnDiv.className = "mt-6 flex justify-end";
            btnDiv.innerHTML = `
                <button id="save-triage-btn" 
                        class="bg-green-600 hover:bg-green-500 text-white px-6 py-3 rounded-lg font-medium transition-all hover:scale-105 active:scale-95 shadow-lg shadow-green-900/20 flex items-center gap-2">
                    <span>💾</span> Save to Vault
                </button>
            `;
            resultArea.appendChild(btnDiv);

            btnDiv.querySelector('#save-triage-btn').onclick = async () => {
                try {
                    const saveResp = await fetch('/api/run/home_triage', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ data: { action: "save_analysis", payload: result.data } })
                    });
                    const saveResult = await saveResp.json();
                    if (saveResult.status === "success") {
                        alert("✅ Saved to Vault! ID: " + saveResult.data.id);
                    } else {
                        alert("❌ Save failed: " + saveResult.message);
                    }
                } catch (e) {
                    console.error("Save error:", e);
                    alert("Error saving to vault.");
                }
            };
        }

        if (result.status === 'warning') {
            resultArea.classList.replace('border-brand-accent', 'border-brand-warning');
            resultArea.classList.replace('bg-brand-accent/5', 'bg-brand-warning/5');
        }

    } catch (error) {
        console.error(error);
        resultArea.innerHTML = `<div class="text-red-500">Error executing action.</div>`;
    }
}

// Start
init();
