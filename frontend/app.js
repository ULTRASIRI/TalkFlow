/**
 * TalkFlow Frontend Application
 * Handles WebSocket communication, audio capture, and UI updates
 */

class TalkFlowApp {
    constructor() {
        // WebSocket
        this.ws = null;
        this.wsReconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        // Audio
        this.mediaStream = null;
        this.audioContext = null;
        this.processor = null;
        this.isRecording = false;
        
        // UI Elements
        this.elements = {
            statusBadge: document.getElementById('statusBadge'),
            statusText: document.querySelector('.status-text'),
            startButton: document.getElementById('startButton'),
            stopButton: document.getElementById('stopButton'),
            clearButton: document.getElementById('clearButton'),
            sourceLanguage: document.getElementById('sourceLanguage'),
            targetLanguage: document.getElementById('targetLanguage'),
            vadToggle: document.getElementById('vadToggle'),
            transcriptionBox: document.getElementById('transcriptionBox'),
            translationBox: document.getElementById('translationBox'),
            playAudioButton: document.getElementById('playAudioButton'),
            audioPlayer: document.getElementById('audioPlayer'),
            sourceLanguageTag: document.getElementById('sourceLanguageTag'),
            targetLanguageTag: document.getElementById('targetLanguageTag'),
            totalLatency: document.getElementById('totalLatency'),
            asrLatency: document.getElementById('asrLatency'),
            translationLatency: document.getElementById('translationLatency'),
            ttsLatency: document.getElementById('ttsLatency')
        };
        
        // State
        this.currentTranscription = '';
        this.currentTranslation = '';
        this.latestAudioBlob = null;
        
        // Initialize
        this.init();
    }
    
    init() {
        console.log('Initializing TalkFlow...');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Connect WebSocket
        this.connectWebSocket();
    }
    
    setupEventListeners() {
        // Control buttons
        this.elements.startButton.addEventListener('click', () => this.startRecording());
        this.elements.stopButton.addEventListener('click', () => this.stopRecording());
        this.elements.clearButton.addEventListener('click', () => this.clearTranscriptions());
        
        // Language selectors
        this.elements.sourceLanguage.addEventListener('change', () => this.updateLanguages());
        this.elements.targetLanguage.addEventListener('change', () => this.updateLanguages());
        
        // VAD toggle
        this.elements.vadToggle.addEventListener('change', () => this.updateVAD());
        
        // Audio playback
        this.elements.playAudioButton.addEventListener('click', () => this.playAudio());
        
        // Update language tags on change
        this.elements.sourceLanguage.addEventListener('change', (e) => {
            this.elements.sourceLanguageTag.textContent = e.target.value.toUpperCase();
        });
        
        this.elements.targetLanguage.addEventListener('change', (e) => {
            this.elements.targetLanguageTag.textContent = e.target.value.toUpperCase();
        });
    }
    
    connectWebSocket() {
        console.log('Connecting to WebSocket...');
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => this.onWebSocketOpen();
            this.ws.onmessage = (event) => this.onWebSocketMessage(event);
            this.ws.onerror = (error) => this.onWebSocketError(error);
            this.ws.onclose = () => this.onWebSocketClose();
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.updateStatus('error', 'Connection failed');
        }
    }
    
    onWebSocketOpen() {
        console.log('WebSocket connected');
        this.wsReconnectAttempts = 0;
        this.updateStatus('connected', 'Connected');
        this.elements.startButton.disabled = false;
    }
    
    async onWebSocketMessage(event) {
        if (event.data instanceof Blob) {
            // Audio data received
            this.latestAudioBlob = event.data;
            this.elements.playAudioButton.style.display = 'inline-flex';
        } else {
            // JSON message
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Failed to parse message:', error);
            }
        }
    }
    
    handleMessage(data) {
        console.log('Message received:', data.type);
        
        switch (data.type) {
            case 'connection':
                console.log('Connection established:', data.message);
                break;
            
            case 'transcription':
                this.updateTranscription(data.text, data.is_final);
                break;
            
            case 'translation':
                this.updateTranslation(data.text);
                break;
            
            case 'metrics':
                this.updateMetrics(data.data);
                break;
            
            case 'vad_status':
                // VAD status update
                if (data.metrics) {
                    this.updateMetrics(data.metrics);
                }
                break;
            
            case 'error':
                console.error('Server error:', data.message);
                this.showError(data.message);
                break;
            
            case 'reset_complete':
                console.log('Pipeline reset');
                break;
            
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    onWebSocketError(error) {
        console.error('WebSocket error:', error);
        this.updateStatus('error', 'Connection error');
    }
    
    onWebSocketClose() {
        console.log('WebSocket closed');
        this.updateStatus('error', 'Disconnected');
        
        // Stop recording if active
        if (this.isRecording) {
            this.stopRecording();
        }
        
        // Attempt reconnection
        if (this.wsReconnectAttempts < this.maxReconnectAttempts) {
            this.wsReconnectAttempts++;
            console.log(`Reconnecting... (${this.wsReconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connectWebSocket(), 2000 * this.wsReconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.showError('Connection lost. Please refresh the page.');
        }
    }
    
    async startRecording() {
        console.log('Starting recording...');
        
        try {
            // Request microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000
            });
            
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            
            // Create audio worklet or script processor
            if (this.audioContext.audioWorklet) {
                // Use AudioWorklet (modern browsers)
                await this.setupAudioWorklet(source);
            } else {
                // Fall back to ScriptProcessor
                this.setupScriptProcessor(source);
            }
            
            this.isRecording = true;
            this.updateUIForRecording(true);
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            this.showError('Microphone access denied or unavailable');
        }
    }
    
    setupScriptProcessor(source) {
        // Create script processor with smaller buffer for better VAD alignment
        // 2048 samples = ~128ms at 16kHz (contains 4 VAD frames of 512 samples)
        const bufferSize = 2048;
        this.processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);
        
        this.processor.onaudioprocess = (event) => {
            if (!this.isRecording) return;
            
            const inputData = event.inputBuffer.getChannelData(0);
            
            // Convert Float32Array to Int16Array
            const int16Data = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                const s = Math.max(-1, Math.min(1, inputData[i]));
                int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }
            
            // Send to server
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(int16Data.buffer);
            }
        };
        
        source.connect(this.processor);
        this.processor.connect(this.audioContext.destination);
    }
    
    async setupAudioWorklet(source) {
        // AudioWorklet setup (future enhancement)
        // For now, fall back to ScriptProcessor
        this.setupScriptProcessor(source);
    }
    
    stopRecording() {
        console.log('Stopping recording...');
        
        this.isRecording = false;
        
        // Stop audio processing
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }
        
        // Close audio context
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        // Stop media stream
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        
        this.updateUIForRecording(false);
    }
    
    updateUIForRecording(isRecording) {
        if (isRecording) {
            this.elements.startButton.style.display = 'none';
            this.elements.stopButton.style.display = 'inline-flex';
            this.elements.stopButton.classList.add('recording');
        } else {
            this.elements.startButton.style.display = 'inline-flex';
            this.elements.stopButton.style.display = 'none';
            this.elements.stopButton.classList.remove('recording');
        }
    }
    
    updateTranscription(text, isFinal = false) {
        // Remove placeholder
        const placeholder = this.elements.transcriptionBox.querySelector('.placeholder');
        if (placeholder) {
            placeholder.remove();
        }
        
        // Update transcription
        if (isFinal) {
            // Add new final transcription
            const p = document.createElement('p');
            p.className = 'transcription-text fade-in';
            p.textContent = text;
            this.elements.transcriptionBox.appendChild(p);
            
            // Scroll to bottom
            this.elements.transcriptionBox.scrollTop = this.elements.transcriptionBox.scrollHeight;
        } else {
            // Update or create partial transcription
            let partialElement = this.elements.transcriptionBox.querySelector('.partial');
            if (!partialElement) {
                partialElement = document.createElement('p');
                partialElement.className = 'partial';
                this.elements.transcriptionBox.appendChild(partialElement);
            }
            partialElement.textContent = text;
        }
    }
    
    updateTranslation(text) {
        // Remove placeholder
        const placeholder = this.elements.translationBox.querySelector('.placeholder');
        if (placeholder) {
            placeholder.remove();
        }
        
        // Add new translation
        const p = document.createElement('p');
        p.className = 'translation-text fade-in';
        p.textContent = text;
        this.elements.translationBox.appendChild(p);
        
        // Scroll to bottom
        this.elements.translationBox.scrollTop = this.elements.translationBox.scrollHeight;
    }
    
    updateMetrics(metrics) {
        if (metrics.total_latency_ms !== undefined) {
            this.elements.totalLatency.textContent = `${Math.round(metrics.total_latency_ms)} ms`;
        }
        
        if (metrics.asr_latency_ms !== undefined) {
            this.elements.asrLatency.textContent = `${Math.round(metrics.asr_latency_ms)} ms`;
        }
        
        if (metrics.translation_latency_ms !== undefined) {
            this.elements.translationLatency.textContent = `${Math.round(metrics.translation_latency_ms)} ms`;
        }
        
        if (metrics.tts_latency_ms !== undefined) {
            this.elements.ttsLatency.textContent = `${Math.round(metrics.tts_latency_ms)} ms`;
        }
    }
    
    clearTranscriptions() {
        // Clear transcription box
        this.elements.transcriptionBox.innerHTML = '<p class="placeholder">Start speaking to see transcription...</p>';
        
        // Clear translation box
        this.elements.translationBox.innerHTML = '<p class="placeholder">Translation will appear here...</p>';
        
        // Hide audio button
        this.elements.playAudioButton.style.display = 'none';
        this.latestAudioBlob = null;
        
        // Reset metrics
        this.elements.totalLatency.textContent = '0 ms';
        this.elements.asrLatency.textContent = '0 ms';
        this.elements.translationLatency.textContent = '0 ms';
        this.elements.ttsLatency.textContent = '0 ms';
        
        // Send reset message to server
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'reset' }));
        }
    }
    
    async updateLanguages() {
        const sourceLanguage = this.elements.sourceLanguage.value;
        const targetLanguage = this.elements.targetLanguage.value;
        
        console.log(`Updating languages: ${sourceLanguage} → ${targetLanguage}`);
        
        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    source_language: sourceLanguage,
                    target_language: targetLanguage
                })
            });
            
            const result = await response.json();
            console.log('Language update result:', result);
            
            // Clear transcriptions for new language pair
            this.clearTranscriptions();
            
        } catch (error) {
            console.error('Failed to update languages:', error);
            this.showError('Failed to update languages');
        }
    }
    
    async updateVAD() {
        const vadEnabled = this.elements.vadToggle.checked;
        
        console.log(`VAD ${vadEnabled ? 'enabled' : 'disabled'}`);
        
        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    vad_enabled: vadEnabled
                })
            });
            
            const result = await response.json();
            console.log('VAD update result:', result);
            
        } catch (error) {
            console.error('Failed to update VAD:', error);
        }
    }
    
    playAudio() {
        if (!this.latestAudioBlob) return;
        
        const audioUrl = URL.createObjectURL(this.latestAudioBlob);
        this.elements.audioPlayer.src = audioUrl;
        this.elements.audioPlayer.play();
        
        // Cleanup URL after playback
        this.elements.audioPlayer.onended = () => {
            URL.revokeObjectURL(audioUrl);
        };
    }
    
    updateStatus(status, text) {
        this.elements.statusBadge.className = `status-badge ${status}`;
        this.elements.statusText.textContent = text;
    }
    
    showError(message) {
        // Simple error display (could be enhanced with a modal)
        console.error('Error:', message);
        alert(`Error: ${message}`);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.talkFlowApp = new TalkFlowApp();
});
