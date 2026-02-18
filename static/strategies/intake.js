import { BaseStrategy } from './base_strategy.js?v=9';

export class IntakeStrategy extends BaseStrategy {
    constructor(metadata) {
        super(metadata);
        this.chatHistory = [];
        this.turnCount = 0;
        this.maxTurns = 5;
    }

    renderResults(data, container, message) {
        // Initial render logic or update logic?
        // Since executeAction re-renders the whole strategy via loadStrategy often... 
        // actually app.js's executeAction calls renderResults into the result-area.
        // But for a chat interface, we want to take over the main content area or 
        // inject a chat UI into the result area.

        // If this is the FIRST render (data contains initial message or empty), set up the UI.

        if (!container.querySelector('#chat-container')) {
            container.innerHTML = `
                <div class="flex flex-col h-[600px] glass-panel rounded-2xl overflow-hidden">
                    <!-- Chat Header -->
                    <div class="bg-slate-800/50 p-4 border-b border-slate-700 flex justify-between items-center">
                        <div class="flex items-center gap-3">
                            <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                            <h3 class="font-bold text-white">Medical Assistant</h3>
                        </div>
                        <span id="turn-counter" class="text-xs text-slate-400">Turn 0/${this.maxTurns}</span>
                    </div>

                    <!-- Chat Messages Area -->
                    <div id="chat-messages" class="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-900/30">
                        <!-- Messages go here -->
                    </div>

                    <!-- Input Area -->
                    <div class="p-4 bg-slate-800/50 border-t border-slate-700">
                        <div class="flex gap-2">
                            <input type="text" id="chat-input" 
                                class="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-accent transition-colors"
                                placeholder="Type your response..."
                                onkeypress="if(event.key === 'Enter') document.getElementById('send-chat-btn').click()">
                            <button id="send-chat-btn" 
                                class="bg-brand-accent hover:bg-brand-accent/80 text-white px-6 rounded-lg font-medium transition-colors">
                                Send
                            </button>
                        </div>
                    </div>
                </div>
            `;

            // Bind events
            container.querySelector('#send-chat-btn').onclick = () => this.sendMessage(container);

            // Start the conversation if no history yet
            if (this.chatHistory.length === 0) {
                this.startConversation(container);
            }
        }

        // If data is a response from sendMessage action
        if (data && data.message) {
            this.appendMessage('assistant', data.message, container);
            if (data.history) this.chatHistory = data.history; // Sync full history
            if (data.turn_count !== undefined) this.turnCount = data.turn_count;
            this.updateCounter(container);

            // Check if we should finish
            if (this.turnCount >= this.maxTurns) {
                this.showFinishOption(container);
            }
        }
        else if (data && data.report) {
            // Show the report interaction
            container.innerHTML = `
                <div class="glass-panel p-6 rounded-2xl space-y-6 animate-fade-in">
                    <div class="flex items-center gap-3 text-brand-accent mb-4">
                         <span class="text-2xl">📋</span>
                         <h3 class="text-xl font-bold text-white">Pre-Briefing Note Generated</h3>
                    </div>
                    
                    <div class="bg-slate-900/50 p-6 rounded-xl border border-slate-700 font-mono text-sm text-slate-300 whitespace-pre-wrap">
                        ${data.report}
                    </div>

                    <div class="flex justify-end gap-3">
                         <button onclick="location.reload()" class="px-4 py-2 text-slate-400 hover:text-white transition-colors">Restart</button>
                         <button id="save-note-btn" class="bg-green-600 hover:bg-green-500 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2">
                            <span>💾</span> Save to Vault
                         </button>
                    </div>
                </div>
            `;

            container.querySelector('#save-note-btn').onclick = () => this.saveNoteToVault(data.report);
        }
        else if (data && data.id) {
            // Saved successfully
            alert(`✅ Pre-Mission Briefing saved to Vault! (ID: ${data.id})`);
        }
    }

    async startConversation(container) {
        this.setLoading(true, container);
        try {
            const response = await fetch('/api/run/intake', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data: { action: "start_intake" } })
            });
            const result = await response.json();

            if (result.data) {
                this.chatHistory = result.data.history;
                this.appendMessage('assistant', result.data.message, container);
            }
        } catch (e) {
            console.error(e);
            this.appendMessage('system', "Error starting conversation.", container);
        } finally {
            this.setLoading(false, container);
        }
    }

    async sendMessage(container) {
        const input = container.querySelector('#chat-input');
        const message = input.value.trim();
        if (!message) return;

        // Display user message
        this.appendMessage('user', message, container);
        input.value = '';
        this.setLoading(true, container);

        try {
            const response = await fetch('/api/run/intake', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data: {
                        action: "send_message",
                        payload: {
                            message: message,
                            history: this.chatHistory,
                            turn_count: this.turnCount
                        }
                    }
                })
            });
            const result = await response.json();

            if (result.data) {
                this.chatHistory = result.data.history;
                this.turnCount = result.data.turn_count; // Sync turn count
                this.appendMessage('assistant', result.data.message, container);
                this.updateCounter(container);

                if (this.turnCount >= this.maxTurns) {
                    this.showFinishOption(container);
                }
            }
        } catch (e) {
            console.error(e);
            this.appendMessage('system', "Error sending message.", container);
        } finally {
            this.setLoading(false, container);
        }
    }

    appendMessage(role, text, container) {
        const historyDiv = container.querySelector('#chat-messages');
        const isUser = role === 'user';
        const isSystem = role === 'system';

        const div = document.createElement('div');
        div.className = `flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`;

        if (isSystem) {
            div.innerHTML = `<span class="text-xs text-red-400 bg-red-900/20 px-2 py-1 rounded">${text}</span>`;
        } else {
            div.innerHTML = `
                <div class="max-w-[80%] rounded-2xl px-5 py-3 ${isUser
                    ? 'bg-brand-accent text-white rounded-tr-none'
                    : 'bg-slate-700 text-slate-200 rounded-tl-none'
                }">
                    <p class="text-sm leading-relaxed">${text}</p>
                </div>
            `;
        }

        historyDiv.appendChild(div);
        historyDiv.scrollTop = historyDiv.scrollHeight;
    }

    setLoading(isLoading, container) {
        const input = container.querySelector('#chat-input');
        const btn = container.querySelector('#send-chat-btn');
        if (input) input.disabled = isLoading;
        if (btn) {
            btn.disabled = isLoading;
            btn.innerHTML = isLoading ? '<div class="w-5 h-5 border-2 border-white/50 border-t-white rounded-full animate-spin"></div>' : 'Send';
        }

        // Show typing indicator OR Progress Bar
        const historyDiv = container.querySelector('#chat-messages');

        if (isLoading) {
            const loadingId = "ai-loading-indicator";
            // Remove existing if any
            const existing = container.querySelector(`#${loadingId}`);
            if (existing) existing.remove();

            const loadingContainer = document.createElement('div');
            loadingContainer.id = loadingId;
            loadingContainer.className = "flex flex-col gap-2 p-4 max-w-[80%] animate-fade-in";

            // Smart Loading UI: If it takes long (model loading), show progress
            loadingContainer.innerHTML = `
                <div class="flex items-center gap-2 mb-1">
                    <span class="text-xs font-bold text-brand-accent uppercase tracking-wider">MedGemma AI Thinking</span>
                    <div class="w-1.5 h-1.5 bg-brand-accent rounded-full animate-pulse"></div>
                </div>
                <!-- Progress Bar -->
                <div class="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div id="ai-progress-bar" class="h-full bg-brand-accent/80 w-0 transition-all duration-300 ease-out"></div>
                </div>
                <span id="ai-loading-text" class="text-[10px] text-slate-500">Processing context...</span>
             `;

            historyDiv.appendChild(loadingContainer);
            historyDiv.scrollTop = historyDiv.scrollHeight;

            // Simulate progress for model loading
            // Starts fast, then slows down to 90% until done
            this.loadingInterval = setInterval(() => {
                const bar = loadingContainer.querySelector('#ai-progress-bar');
                const text = loadingContainer.querySelector('#ai-loading-text');
                if (!bar) return;

                let width = parseFloat(bar.style.width) || 0;
                if (width < 30) {
                    width += 2; // Fast start
                    if (text) text.textContent = "Analyzing input...";
                } else if (width < 60) {
                    width += 0.5; // Slow down
                    if (text) text.textContent = "Loading medical knowledge (4B parameters)...";
                } else if (width < 90) {
                    width += 0.1; // Crawl
                    if (text) text.textContent = "Generating clinical response...";
                }
                bar.style.width = `${width}%`;
            }, 100);

        } else {
            // Remove loading UI
            const loading = container.querySelector('#ai-loading-indicator');
            if (loading) loading.remove();

            // Clear interval
            if (this.loadingInterval) {
                clearInterval(this.loadingInterval);
                this.loadingInterval = null;
            }
        }
    }

    updateCounter(container) {
        const counter = container.querySelector('#turn-counter');
        if (counter) counter.textContent = `Turn ${this.turnCount}/${this.maxTurns}`;
    }

    showFinishOption(container) {
        const historyDiv = container.querySelector('#chat-messages');
        const div = document.createElement('div');
        div.className = "flex justify-center my-4 animate-fade-in";
        div.innerHTML = `
            <button id="finish-chat-btn" class="bg-brand-accent hover:bg-white hover:text-brand-accent text-white px-8 py-2 rounded-full font-bold shadow-lg transition-all transform hover:scale-105">
                Generate Pre-Briefing Note ✨
            </button>
        `;
        historyDiv.appendChild(div);
        historyDiv.scrollTop = historyDiv.scrollHeight;

        // Disable input
        const input = container.querySelector('#chat-input');
        if (input) {
            input.disabled = true;
            input.placeholder = "Interview complete.";
        }

        container.querySelector('#finish-chat-btn').onclick = () => this.generateReport(container);
    }

    async generateReport(container) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-20 animate-fade-in">
                <div class="w-16 h-16 border-4 border-brand-accent border-t-transparent rounded-full animate-spin mb-6"></div>
                <h3 class="text-xl font-bold text-white mb-2">Analyzing Interview...</h3>
                <p class="text-slate-400">Generating structured SOAP note with MedGemma</p>
            </div>
        `;

        try {
            const response = await fetch('/api/run/intake', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data: {
                        action: "generate_report",
                        payload: { history: this.chatHistory }
                    }
                })
            });
            const result = await response.json();

            // Re-render with result
            this.renderResults(result.data, container, result.message);

        } catch (e) {
            console.error(e);
            container.innerHTML = `<div class="text-red-500 text-center">Error generating report.</div>`;
        }
    }

    async saveNoteToVault(report) {
        try {
            const response = await fetch('/api/run/intake', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data: {
                        action: "save_pre_briefing",
                        payload: { report: report }
                    }
                })
            });
            const result = await response.json();
            if (result.status === 'success') {
                alert(`✅ Saved to Vault! ID: ${result.data.id}`);
            } else {
                alert(`❌ Error: ${result.message}`);
            }
        } catch (e) {
            console.error(e);
            alert("Error saving to vault.");
        }
    }
}
