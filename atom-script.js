document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded and parsed");

    // Get elements by ID
    const sendTextButton = document.getElementById('send-text-button');
    const startRecordingButton = document.getElementById('start-recording-button');
    const micIcon = document.getElementById('mic-icon');
    const keyboardIcon = document.getElementById('keyboard-icon');

    // Log the existence of elements
    console.log('sendTextButton:', sendTextButton);
    console.log('startRecordingButton:', startRecordingButton);
    console.log('micIcon:', micIcon);
    console.log('keyboardIcon:', keyboardIcon);

    // Check for null references
    if (!sendTextButton || !startRecordingButton || !micIcon || !keyboardIcon) {
        console.error("One or more elements not found in the DOM.");
        return; // Exit if any element is not found
    }

    // ElectronManager class to manage electron states and animation
    class ElectronManager {
        constructor(electrons, centerX, centerY) {
            console.log("Initializing ElectronManager");
            this.electrons = electrons;
            this.centerX = centerX;
            this.centerY = centerY;
            this.currentState = 'standby';
            this.startElectronAnimation();
        }

        startElectronAnimation() {
            console.log("Starting electron animation");
            setInterval(this.updateElectrons.bind(this), 16);
        }

        updateElectrons() {
            this.electrons.forEach(electron => {
                const x = electron.a * Math.cos(electron.angle);
                const y = electron.b * Math.sin(electron.angle);
                electron.el.style.transform = `translate(${this.centerX + x}px, ${this.centerY + y}px)`;
                electron.angle += electron.speed;
                if (electron.angle >= 2 * Math.PI) {
                    electron.angle -= 2 * Math.PI;
                }
            });
        }

        updateElectronColors(state) {
            console.log(`Updating electron colors to state: ${state}`);
            this.electrons.forEach(electron => {
                electron.el.className = `electron ${state}`;
            });
        }

        async setState(newState) {
            if (this.currentState !== newState) {
                console.log(`State change detected: ${this.currentState} -> ${newState}`);
                this.currentState = newState;
                this.updateElectronColors(newState);

                // Communicate state change to server
                try {
                    console.log(`Sending state change to server: ${newState}`);
                    const response = await fetch('https://yourserver.com/api/electron-state', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ state: newState }),
                        mode: 'no-cors'  // Use no-cors for local development
                    });
                    const data = await response.json();
                    console.log("Server acknowledged state change:", data);
                } catch (error) {
                    console.error('Error sending state to server:', error);
                }
            }
        }
    }

    // AudioManager class to handle audio setup and processing
    class AudioManager {
        constructor(nucleus, microphone, stateManager) {
            console.log("Initializing AudioManager");
            this.nucleus = nucleus;
            this.microphone = microphone;
            this.stateManager = stateManager;
            this.audioContext = null;
            this.micStream = null;
            this.micAnalyser = null;
            this.speakerAnalyser = null;
            this.micDataArray = null;
            this.speakerDataArray = null;
            this.audioStarted = false;
            this.sensitivityMultiplier = 2.0;

            console.log("Adding event listener to microphone icon");
            this.microphone.addEventListener('click', this.toggleAudioProcessing.bind(this));
        }

        async setupAudio() {
            try {
                console.log("Requesting microphone access...");
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();

                // Microphone stream
                this.micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                console.log("Microphone stream obtained:", this.micStream);

                const micSource = this.audioContext.createMediaStreamSource(this.micStream);
                this.micAnalyser = this.audioContext.createAnalyser();
                micSource.connect(this.micAnalyser);
                this.micAnalyser.fftSize = 256;
                this.micDataArray = new Uint8Array(this.micAnalyser.frequencyBinCount);

                // Speaker stream
                const speakerSource = this.audioContext.createMediaElementSource(new Audio());
                this.speakerAnalyser = this.audioContext.createAnalyser();
                speakerSource.connect(this.speakerAnalyser);
                this.speakerAnalyser.connect(this.audioContext.destination);
                this.speakerAnalyser.fftSize = 256;
                this.speakerDataArray = new Uint8Array(this.speakerAnalyser.frequencyBinCount);

                this.microphone.classList.add('active');
                this.audioStarted = true;
                console.log("Audio processing started, setting state to 'listening'");
                this.stateManager.setState('listening');
                this.updateNucleus();

                // Inform server that audio setup is complete
                console.log("Notifying server that audio setup is complete");
                fetch('https://yourserver.com/api/audio-setup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: 'audioStarted' }),
                    mode: 'no-cors'  // Use no-cors for local development
                }).then(response => response.json())
                  .then(data => console.log("Server acknowledged audio setup:", data))
                  .catch(error => console.error('Error notifying server:', error));

            } catch (error) {
                console.error('Error accessing audio:', error);
                this.stateManager.setState('error');
                alert('Could not access microphone. Please check permissions.');
            }
        }

        toggleAudioProcessing() {
            if (this.audioStarted) {
                console.log("Stopping audio processing.");
                this.stopAudioProcessing();
            } else {
                console.log("Starting audio processing.");
                this.setupAudio();
            }
        }

        stopAudioProcessing() {
            console.log("Stopping audio, cleaning up resources.");
            if (this.micStream) {
                this.micStream.getTracks().forEach(track => track.stop());
                console.log("Microphone stream stopped.");
            }
            if (this.audioContext) {
                this.audioContext.close();
                console.log("Audio context closed.");
            }
            this.audioStarted = false;
            this.microphone.classList.remove('active');

            console.log("Setting state to 'standby'");
            this.stateManager.setState('standby');
        }

        updateNucleus() {
            if (!this.audioStarted) return;

            this.micAnalyser.getByteFrequencyData(this.micDataArray);
            this.speakerAnalyser.getByteFrequencyData(this.speakerDataArray);

            const micVolume = this.getAverageVolume(this.micDataArray);
            const speakerVolume = this.getAverageVolume(this.speakerDataArray);
            const scale = 1 + Math.max(micVolume, speakerVolume) * this.sensitivityMultiplier;
            this.nucleus.style.transform = `translate(-50%, -50%) scale(${scale})`;

            console.log("Updating nucleus scale:", scale);
            requestAnimationFrame(this.updateNucleus.bind(this));
        }

        getAverageVolume(array) {
            const values = array.reduce((acc, val) => acc + val, 0);
            const averageVolume = values / array.length / 128.0;
            console.log("Average volume calculated:", averageVolume);
            return averageVolume;
        }
    }

    // ChatManager class to handle text and audio messaging
    class ChatManager {
        constructor(chatWindow, inputText, sendButton, recordButton, stateManager) {
            console.log("Initializing ChatManager");
            this.chatWindow = chatWindow;
            this.inputText = inputText;
            this.sendButton = sendButton;
            this.recordButton = recordButton;
            this.stateManager = stateManager;
            this.audioChunks = [];
            this.mediaRecorder = null;

            console.log("Adding event listeners to chat elements");
            this.sendButton.addEventListener('click', this.sendText.bind(this));
            this.inputText.addEventListener('keypress', (event) => {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    this.sendText();
                }
            });

            this.recordButton.addEventListener('click', this.toggleRecording.bind(this));
        }

        addMessageToChat(message, isWaiting = false) {
            const messageElement = document.createElement('div');
            messageElement.className = 'atom-chat-message';
            messageElement.textContent = message;

            if (isWaiting) {
                messageElement.id = 'atom-waiting-message';
                messageElement.style.fontStyle = 'italic';
            }

            console.log(`Adding message to chat: ${message}`);
            this.chatWindow.prepend(messageElement);

            while (this.chatWindow.children.length > 5) {
                this.chatWindow.removeChild(this.chatWindow.lastChild);
            }
        }

        async sendText() {
            const text = this.inputText.value.trim();
            if (text === '') return;

            this.addMessageToChat(`You: ${text}`);
            this.addMessageToChat('Waiting for response...', true);

            try {
                console.log(`Sending text to server: ${text}`);
                const response = await fetch('http://127.0.0.1:5000/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ input_text: text }),
                    mode: 'no-cors'  // Use no-cors for local development
                });
                const data = await response.json();
                console.log("Received response from server:", data);
                this.displayResponse(data);
                this.stateManager.setState('standby');  // Set state to standby after processing
            } catch (error) {
                this.handleChatError(error);
            }

            this.inputText.value = '';
        }

        async toggleRecording() {
            if (this.recordButton.textContent === "Start Recording") {
                console.log("Starting audio recording");
                this.startRecording();
                this.stateManager.setState('processing');  // Set state to processing during recording
            } else {
                console.log("Stopping audio recording");
                this.stopRecording();
                this.stateManager.setState('standby');  // Set state back to standby after recording
            }
        }

        startRecording() {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    this.mediaRecorder = new MediaRecorder(stream);
                    this.mediaRecorder.start();
                    this.recordButton.textContent = "Stop Recording";

                    this.mediaRecorder.addEventListener("dataavailable", event => {
                        this.audioChunks.push(event.data);
                        console.log("Audio chunk captured");
                    });
                })
                .catch(error => console.error('Error accessing microphone:', error));
        }

        stopRecording() {
            this.mediaRecorder.stop();
            this.recordButton.textContent = "Start Recording";

            this.mediaRecorder.addEventListener("stop", async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                const formData = new FormData();
                formData.append('audio', audioBlob, 'recording.wav');

                this.addMessageToChat('You: Sent an audio message');
                this.addMessageToChat('Waiting for response...', true);

                try {
                    console.log("Sending audio to server");
                    const response = await fetch('http://127.0.0.1:5000/upload_audio', {
                        method: 'POST',
                        body: formData,
                        mode: 'no-cors'  // Use no-cors for local development
                    });
                    const data = await response.json();
                    console.log("Received response from server:", data);
                    this.displayResponse(data);
                } catch (error) {
                    this.handleChatError(error);
                }

                this.audioChunks = [];
            });
        }

        displayResponse(data) {
            const waitingMessage = document.getElementById('atom-waiting-message');
            if (waitingMessage) {
                this.chatWindow.removeChild(waitingMessage);
            }

            if (data.recognized_text) {
                console.log("Displaying recognized text:", data.recognized_text);
                this.addMessageToChat(`You: ${data.recognized_text}`);
            }

            if (data.response_text) {
                console.log("Displaying response text:", data.response_text);
                this.addMessageToChat(`Atom: ${data.response_text}`);
            }
        }

        handleChatError(error) {
            console.error('Error in chat communication:', error);
            const waitingMessage = document.getElementById('atom-waiting-message');
            if (waitingMessage) {
                this.chatWindow.removeChild(waitingMessage);
            }
            this.addMessageToChat('Error: Could not retrieve response from server.');
            this.stateManager.setState('error');
        }
    }

    class StateManager {
        constructor(electronManager) {
            console.log("Initializing StateManager");
            this.electronManager = electronManager;
        }

        setState(newState) {
            console.log(`StateManager setting state: ${newState}`);
            this.electronManager.setState(newState);
        }
    }

    // Initialization of managers
    console.log("Initializing electrons and managers");
    const electrons = [
        { el: document.getElementById('electron1'), a: 150, b: 75, speed: 0.02, angle: 0 },
        { el: document.getElementById('electron2'), a: 75, b: 150, speed: 0.015, angle: Math.PI / 4 },
        { el: document.getElementById('electron3'), a: 106, b: 106, speed: 0.01, angle: Math.PI / 2 },
        { el: document.getElementById('electron4'), a: 150, b: 75, speed: 0.025, angle: Math.PI }
    ];

    const electronManager = new ElectronManager(electrons, 200, 200);
    const stateManager = new StateManager(electronManager);
    const audioManager = new AudioManager(
        document.getElementById('nucleus'),
        document.getElementById('mic-icon'),  // Microphone SVG
        stateManager
    );
    const chatManager = new ChatManager(
        document.getElementById('atom-chat-window'),
        document.getElementById('atom-input-text'),
        document.getElementById('send-text-button'), // Send Text Button
        document.getElementById('start-recording-button'), // Start Recording Button
        stateManager
    );

    // Add event listener for the SVG keyboard icon
    keyboardIcon.addEventListener('click', () => {
        console.log('Keyboard icon clicked');
        chatManager.sendText();  // Trigger sendText on keyboard icon click
    });

    // Clock update function (unchanged)
    function updateClock() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        document.getElementById('clock').textContent = `${hours}:${minutes}:${seconds}`;
    }

    setInterval(updateClock, 1000);
    updateClock();
});
