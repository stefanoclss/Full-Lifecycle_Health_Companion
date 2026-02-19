import { BaseStrategy } from './base_strategy.js?v=9';

export class ConsultStrategy extends BaseStrategy {
    constructor(metadata) {
        super(metadata);
        this.audioUrl = null;
        this.transcriptSegments = [];
    }

    renderResults(data, container, message) {
        // If initial load or specialized view needed
        if (!container.querySelector('#consult-container')) {
            this.renderConsultUI(container);
        }
    }

    async renderConsultUI(container) {
        container.innerHTML = `
            <div id="consult-container" class="space-y-6 animate-fade-in">
                <!-- Audio Player Card -->
                <div class="glass-panel p-6 rounded-2xl flex flex-col items-center gap-4">
                    <div class="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center text-blue-400">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold text-white">Consultation Recording: CAR0001</h3>
                    
                    <audio id="audio-player" controls class="w-full max-w-md hidden"></audio>
                    
                    <button id="load-audio-btn" class="bg-brand-accent hover:bg-white hover:text-brand-accent text-white px-8 py-3 rounded-full font-bold shadow-lg transition-all transform hover:scale-105">
                        ▶ Load Consultation Audio
                    </button>
                    
                    <div id="transcription-status" class="text-sm text-slate-400 hidden">
                        <span class="animate-pulse">Transcribing audio with MedASR...</span>
                    </div>
                </div>

                <!-- Live Transcription Area -->
                <div class="glass-panel p-6 rounded-2xl h-[400px] flex flex-col">
                    <div class="flex justify-between items-center mb-4">
                        <h4 class="font-bold text-slate-300">Live Transcription</h4>
                        <span class="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">Real-time Sync</span>
                    </div>
                    <div id="transcript-view" class="flex-1 overflow-y-auto space-y-4 p-4 bg-slate-900/50 rounded-xl border border-slate-700 font-mono text-sm leading-relaxed text-slate-400 transition-all">
                        <div class="text-center text-slate-600 italic py-10">Waiting for audio to start...</div>
                    </div>
                </div>

                <!-- Actions Area -->
                <div id="consult-actions" class="flex justify-end gap-4 opacity-50 pointer-events-none transition-opacity">
                    <button id="generate-note-btn" class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-medium shadow-lg transition-colors">
                        Generate Clinical Note
                    </button>
                </div>
            </div>
         `;

        container.querySelector('#load-audio-btn').onclick = () => this.loadAndTranscribe(container);
        container.querySelector('#generate-note-btn').onclick = () => this.generateNote(container);
    }

    async loadAndTranscribe(container) {
        const loadBtn = container.querySelector('#load-audio-btn');
        const status = container.querySelector('#transcription-status');
        const audioPlayer = container.querySelector('#audio-player');

        loadBtn.disabled = true;
        loadBtn.classList.add('opacity-50', 'cursor-not-allowed');
        status.classList.remove('hidden');

        try {
            // 1. Get Audio URL
            const urlResp = await this.runAction('get_audio');
            if (urlResp.status === 'success') {
                this.audioUrl = urlResp.data.url;
                audioPlayer.src = this.audioUrl;
                audioPlayer.classList.remove('hidden');
                loadBtn.classList.add('hidden'); // Hide load button
            } else {
                alert("Error loading audio: " + urlResp.message);
                return;
            }

            // 2. Start Transcription (Background)
            // Ideally we'd stream, but for now we wait for valid segments
            const view = container.querySelector('#transcript-view');
            view.innerHTML = `<div class="flex items-center justify-center h-full text-brand-accent animate-pulse">Transcribing... (This may take a moment)</div>`;

            const transResp = await this.runAction('transcribe');

            if (transResp.status === 'success') {
                this.transcriptSegments = transResp.data.segments;
                status.innerHTML = `<span class="text-green-400">✓ Transcription Ready</span>`;

                // Reset view
                view.innerHTML = '';

                // Enable actions
                container.querySelector('#consult-actions').classList.remove('opacity-50', 'pointer-events-none');

                // Auto-play audio
                audioPlayer.play();

                // Start Sync Loop
                this.startSyncLoop(audioPlayer, view);
            } else {
                view.innerHTML = `<div class="text-red-500 text-center">Transcription Failed: ${transResp.message}</div>`;
            }

        } catch (e) {
            console.error(e);
            alert("Error in consultation flow");
        }
    }

    startSyncLoop(audio, view) {
        // Clear view first
        view.innerHTML = '';

        // Create elements for all segments initially (or transparently)
        this.transcriptSegments.forEach((seg, index) => {
            const p = document.createElement('p');
            p.id = `seg-${index}`;
            p.className = "transition-colors duration-300 p-2 rounded hover:bg-slate-800/50";
            p.textContent = seg.text;
            p.dataset.start = seg.timestamp[0];
            p.dataset.end = seg.timestamp[1] || 99999;
            view.appendChild(p);
        });

        const updateHighlight = () => {
            const time = audio.currentTime;

            // Find active segment
            const activeIndex = this.transcriptSegments.findIndex(s => {
                const end = s.timestamp[1] || (s.timestamp[0] + 5); // Fallback duration
                return time >= s.timestamp[0] && time < end;
            });

            // Highlight
            Array.from(view.children).forEach((child, idx) => {
                if (idx === activeIndex) {
                    child.classList.add('text-white', 'bg-brand-accent/20', 'scale-[1.02]', 'font-bold');
                    child.classList.remove('text-slate-400');
                    // Auto scroll
                    child.scrollIntoView({ behavior: 'smooth', block: 'center' });
                } else if (idx < activeIndex) {
                    child.classList.add('text-slate-500'); // Completed
                    child.classList.remove('text-slate-400', 'text-white', 'bg-brand-accent/20', 'scale-[1.02]', 'font-bold');
                } else {
                    child.classList.remove('text-white', 'bg-brand-accent/20', 'scale-[1.02]', 'font-bold', 'text-slate-500');
                    child.classList.add('text-slate-400');
                }
            });

            if (!audio.paused) {
                requestAnimationFrame(updateHighlight);
            }
        };

        audio.onplay = () => updateHighlight();
    }

    async generateNote(container) {
        const btn = container.querySelector('#generate-note-btn');
        btn.disabled = true;
        btn.textContent = "Generating...";

        // Full text for summarization
        const fullText = this.transcriptSegments.map(s => s.text).join(" ");

        try {
            const resp = await this.runAction('generate_note', { transcript: fullText });
            if (resp.status === 'success') {
                const note = resp.data.note;
                this.showNoteModal(note, container);
            }
        } catch (e) {
            console.error(e);
            alert("Error generating note.");
        } finally {
            btn.disabled = false;
            btn.textContent = "Generate Clinical Note";
        }
    }

    showNoteModal(note, container) {
        // Overlay modal
        const modal = document.createElement('div');
        modal.className = "fixed inset-0 bg-black/80 flex items-center justify-center z-50 animate-fade-in";
        modal.innerHTML = `
            <div class="bg-slate-900 border border-slate-700 rounded-2xl p-8 max-w-2xl w-full shadow-2xl space-y-6">
                <div class="flex justify-between items-center border-b border-slate-700 pb-4">
                    <h3 class="text-xl font-bold text-white">📝 Clinical Consultation Note</h3>
                    <button id="close-modal" class="text-slate-400 hover:text-white">✕</button>
                </div>
                
                <div class="bg-slate-800/50 p-6 rounded-xl font-mono text-sm text-slate-300 whitespace-pre-wrap max-h-[60vh] overflow-y-auto">
                    ${note}
                </div>
                
                <div class="flex justify-end gap-4 pt-2">
                     <button id="save-note-btn" class="bg-green-600 hover:bg-green-500 text-white px-6 py-2 rounded-lg font-medium shadow-lg transition-colors flex items-center gap-2">
                        <span>💾</span> Save to Vault
                     </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('#close-modal').onclick = () => modal.remove();

        modal.querySelector('#save-note-btn').onclick = async () => {
            const resp = await this.runAction('save_note', { note: note });
            if (resp.status === 'success') {
                alert(`✅ Clinical Note Saved! ID: ${resp.data.id}`);
                modal.remove();
            } else {
                alert("Error saving note.");
            }
        };
    }

    async runAction(name, payload = {}) {
        const response = await fetch('/api/run/consult', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data: { action: name, payload: payload } })
        });
        return await response.json();
    }
}
