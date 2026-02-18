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
            onclick="loadStrategyById('${s.id}')"
            class="w-full text-left px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors flex items-center gap-3 group"
            data-id="${s.id}"
        >
            <div class="w-2 h-8 bg-slate-700 rounded-full group-hover:bg-brand-accent transition-colors"></div>
            <div>
                <div class="text-sm font-medium text-slate-200 group-hover:text-white">${s.title.replace(/^[^\s]+\s/, '')}</div> <!-- Remove icon from title -->
                <div class="text-xs text-slate-500 group-hover:text-slate-400 truncate w-40">${s.description}</div>
            </div>
        </button>
    `).join('');
}

// Load Strategy Wrapper
async function loadStrategyById(id) {
    // Re-fetch to ensure fresh state if needed, or find from cache
    // For now we just find it from the sidebar data if possible, or re-fetch list logic could be added
    // Simpler: Fetch specific strategy info or just pass full object from init.
    // Let's refetch all for simplicity or pass object.
    // We already have the list, let's just find it.
    const buttons = navContainer.querySelectorAll('button');
    buttons.forEach(btn => {
        if (btn.dataset.id === id) {
            btn.classList.add('bg-slate-800');
            btn.querySelector('div.bg-slate-700').classList.add('bg-brand-accent');
        } else {
            btn.classList.remove('bg-slate-800');
            btn.querySelector('div.bg-slate-700').classList.remove('bg-brand-accent');
        }
    });

    const response = await fetch('/api/strategies'); // In production optimize this
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
    if (strategy.content) {
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

    // Render Actions
    if (strategy.actions) {
        html += `<div class="flex flex-wrap gap-4">
            ${strategy.actions.map(action => `
                <button onclick="executeAction('${action.name}')" 
                        class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-lg font-medium transition-all hover:scale-105 active:scale-95 shadow-lg shadow-blue-900/20">
                    ${action.label}
                </button>
            `).join('')}
        </div>`;
    }

    // Result Area
    html += `<div id="result-area" class="hidden glass-panel p-6 rounded-2xl border-l-4 border-brand-accent bg-brand-accent/5"></div>`;
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
                backgroundColor: config.color + '20', // transparent fill
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

// Execute Action with Backend
async function executeAction(actionName) {
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

        // Show Result
        console.log("Result received:", result);
        console.log("Data type:", typeof result.data);
        console.log("Is Array:", Array.isArray(result.data));

        let resultContent = '';
        // Robust check for array-like objects
        if (Array.isArray(result.data) || (result.data && result.data.length !== undefined && typeof result.data !== 'string')) {
            console.log("Rendering cards...");
            resultContent = renderDimensionCards(result.data);
            resultArea.className = "glass-panel p-6 rounded-2xl border-l-4 border-brand-accent bg-brand-accent/5 grid gap-4";
        } else if (typeof result.data === 'object') {
            resultContent = `<pre class="text-white text-sm overflow-x-auto">${JSON.stringify(result.data, null, 2)}</pre>`;
            resultArea.className = "glass-panel p-6 rounded-2xl border-l-4 border-brand-accent bg-brand-accent/5";
        } else {
            resultContent = `<p class="text-white text-lg">${result.data}</p>`;
            resultArea.className = "glass-panel p-6 rounded-2xl border-l-4 border-brand-accent bg-brand-accent/5";
        }

        resultArea.innerHTML = `
            <h5 class="text-sm font-bold uppercase tracking-wide mb-4 ${result.status === 'warning' ? 'text-brand-warning' : 'text-brand-accent'}">
                ${result.message}
            </h5>
            ${resultContent}
        `;

        if (result.status === 'warning') {
            resultArea.classList.replace('border-brand-accent', 'border-brand-warning');
            resultArea.classList.replace('bg-brand-accent/5', 'bg-brand-warning/5');
        }

    } catch (error) {
        resultArea.innerHTML = `<div class="text-red-500">Error executing action.</div>`;
    }
}

// Start
init();

function renderDimensionCards(data) {
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
