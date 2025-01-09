let sendMessage; // this makes both function access it

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Starting initialization');
    initChatbot();
    initSpeechToText();

});

function initChatbot() {
    console.log('Initializing chatbot...');

    // 1. Get DOM elements
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const audioEl   = document.getElementById('myAudio');
    const loadingIndicator = document.getElementById('loading-indicator');
    const speakingIndicator = document.getElementById('speaking-indicator');
    // 2. Check if all required elements are found
    if (!chatBox || !userInput || !sendButton) {
        console.error('Some elements were not found. Chatbot initialization failed.');
        return;
    }

    // 3. Generate or retrieve a session ID
    function generateUniqueId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    function getOrCreateSessionId() {
        let sessionId = localStorage.getItem('sessionId');
        if (!sessionId) {
            sessionId = generateUniqueId();
            localStorage.setItem('sessionId', sessionId);
            console.log('Created new session ID');
        } else {
            console.log('Retrieved existing session ID');
        }
        return sessionId;
    }
    const sessionId = getOrCreateSessionId();
    console.log('All elements found successfully');

    // 4. Helper function: append a message to the chat box
    function appendMessage(message, sender) {
        console.log(`Appending ${sender} message:`, message);

        if (sender === 'user') {
            // If it's a user message, create a single element
            const messageElement = document.createElement('div');
            messageElement.classList.add('user-message');
            messageElement.textContent = message;
            chatBox.appendChild(messageElement);
        } else {
            // If it's a bot message, create a wrapper with an image + text
            const wrapper = document.createElement('div');
            wrapper.classList.add('bot-message-wrap');
            const profilePic = document.createElement('div');
            profilePic.classList.add('bot-profile-pic');
            const img = document.createElement('img');
            img.src = '../static/images/Argos-red.png';
            img.alt = '';
            profilePic.appendChild(img);
            const botText = document.createElement('div');
            botText.classList.add('bot-message');
            botText.innerHTML = message;
            wrapper.appendChild(botText);
            wrapper.appendChild(profilePic);
            chatBox.appendChild(wrapper);
        }

        // Always scroll to the latest message
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // 5. Helper function: find the last bot message's text
    function getLastBotMessageText() {
        const botMessages = document.querySelectorAll('.bot-message');
        if (botMessages.length === 0) {
            return ''; // Fallback if no bot messages
        }                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       J
        return botMessages[botMessages.length - 1].textContent;
    }

    function playTTS(botReply) {
      const encoded = encodeURIComponent(botReply);
      // 1) Set up an event listener to show text & start playback at once
      audioEl.addEventListener('loadeddata', onAudioDataLoaded, { once: true });

      // 2) Assign the audio source
      //    The browser starts fetching the audio but won't necessarily play it yet
      audioEl.src = `/chat/tts?textToSpeak=${encoded}`;
      // We'll actually call .play() after it has some data
      // in the 'loadeddata' event or possibly 'canplay' event.
        // ADDED: Functions to show/hide "speakingIndicator"
      audioEl.addEventListener('playing', onAudioStartSpeaking);
      audioEl.addEventListener('pause', onAudioStopSpeaking);
      audioEl.addEventListener('ended', onAudioStopSpeaking);
      function onAudioDataLoaded() {
        // This fires once there's enough data to at least start playing
        console.log('Audio has enough data, now showing text and playing audio.');

        // Show the bot reply text at the same time
        appendMessage(botReply, 'bot');

        // Attempt autoplay now
        audioEl.play()
          .catch(err => {
             console.error('Audio playback error:', err);
          });
      }
    }
    function onAudioStartSpeaking() {
        console.log('Audio playing => show speaking animation');
        speakingIndicator.style.display = 'block';
    }
    function onAudioStopSpeaking() {
        console.log('Audio paused/ended => hide speaking animation');
        speakingIndicator.style.display = 'none';
    }
    // 7. Send a chat message to the server
    sendMessage = function() {
        const message = userInput.value.trim();
        if (!message) {
            console.log('Message is empty.');
            return;
        }

        console.log('Sending message:', message);

        // Optional: Append user's message immediately to the chat
        appendMessage(message, 'user');
        // Clear the input
        userInput.value = '';
        loadingIndicator.style.display = 'block';

        fetch('http://localhost:8000/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        })
        .then(response => {
            console.log('Response received:', response);
            return response.json();
        })
        .then(data => {
            console.log('Data received from server:', data);
            // Check for data.response or data.error
            loadingIndicator.style.display = 'none';
            if (data.response) {
                playTTS(data.response);

            } else if (data.error) {
                appendMessage(`Error: ${data.error}`, 'bot');
            } else {
                appendMessage('Unexpected server response.', 'bot');
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            loadingIndicator.style.display = 'none';
            appendMessage('Error: Could not connect to the server.', 'bot');
        });
    }

    // 8. Attach event listeners
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            console.log('Enter key pressed');
            sendMessage();
        }
    });

    sendButton.addEventListener('click', function() {
        sendMessage();
    });


    console.log('Chatbot initialization completed');
}
// New function to initialize speech-to-text
function initSpeechToText() {
    let mediaRecorder;
    let audioChunks = [];

    const recordBtn = document.getElementById("record-btn");
    const stopBtn = document.getElementById("stop-btn");
    const audioPreview = document.getElementById("audio-preview");
    const transcriptionElement = document.getElementById("transcription");

    if (!recordBtn || !stopBtn || !audioPreview || !transcriptionElement) {
        console.error('Some speech-to-text elements were not found.');
        return;
    }

    recordBtn.addEventListener("click", async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                try {
                    const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
                    audioChunks = [];

                    const audioURL = URL.createObjectURL(audioBlob);
                    audioPreview.src = audioURL;

                    const formData = new FormData();
                    formData.append("audio", audioBlob);

                    const response = await fetch("http://localhost:8000/speech/transcribe", {
                        method: "POST",
                        body: formData,
                        headers: {
                            Accept: "application/json",
                        },
                    });

                    if (!response.ok) {
                        throw new Error(`Server responded with status: ${response.status}`);
                    }

                    const data = await response.json();
                    transcriptionElement.innerText = `Transcription: ${data.message}`;

                    // Optional: Automatically send transcribed text to chat
                    if (data.message) {
                        document.getElementById('user-input').value = data.message;
                        sendMessage();
                    }
                } catch (error) {
                    console.error("Error during transcription:", error);
                    transcriptionElement.innerText = "Error during transcription.";
                }
            };

            mediaRecorder.start();
            recordBtn.disabled = true;
            stopBtn.disabled = false;
        } catch (error) {
            console.error("Error initializing recording:", error);
            alert("Could not access microphone. Please ensure you have granted permissions.");
        }
    });

    stopBtn.addEventListener("click", () => {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            recordBtn.disabled = false;
            stopBtn.disabled = true;
        }
    });
}