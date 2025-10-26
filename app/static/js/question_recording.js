let mediaRecorder = null;
let audioChunks = [];

function startRecording() {
    // Don't start a new recording if one is already in progress
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        console.log('Recording already in progress, ignoring start request');
        return;
    }

    console.log('Starting recording...');
    const askCardContent = document.getElementById('ask-card-content');
    const recordingUI = document.getElementById('recording-ui');

    if (askCardContent) {
        askCardContent.style.display = 'none';
        console.log('Hidden ask-card-content');
    } else {
        console.error('ask-card-content element not found');
    }

    if (recordingUI) {
        recordingUI.style.display = 'flex';
        console.log('Showed recording-ui');
    } else {
        console.error('recording-ui element not found');
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                audioChunks = [];
                
                try {
                    // Create FormData to send the audio file
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'question.wav');
                    
                    // Show loading state
                    document.getElementById('recording-ui').innerHTML = `
                        <div class="loading-spinner"></div>
                        <p class="recording-text">Processing your question...</p>
                    `;
                    console.log(formData)
                    // Send to API endpoint
                    const response = await fetch('/live_chat/response', {
                        method: 'POST',
                        headers: {
                            "Content-Type": "audio/wav"
                        },
                        data: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error('Failed to process question');
                    }
                    
                    const result = await response.json();
                    
                    // Show the answer
                    document.getElementById('recording-ui').innerHTML = `
                        <div class="answer-container">
                            <h6>Your Question</h6>
                            <p class="question-text">${result.question}</p>
                            <h6>Answer</h6>
                            <p class="answer-text">${result.answer}</p>
                            <button onclick="resetQuestionCard()" class="ask-another-btn">Ask Another Question</button>
                        </div>
                    `;
                } catch (error) {
                    console.error('Error processing question:', error);
                    document.getElementById('recording-ui').innerHTML = `
                        <div class="error-message">
                            <p>Sorry, there was an error processing your question.</p>
                            <button onclick="resetQuestionCard()" class="try-again-btn">Try Again</button>
                        </div>
                    `;
                }
            };
            
            mediaRecorder.start();
        })
        .catch(error => {
            console.error('Error accessing microphone:', error);
            // Reset the UI
            document.getElementById('ask-card-content').style.display = 'block';
            document.getElementById('recording-ui').style.display = 'none';
        });
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
}

function resetQuestionCard() {
    console.log(`Resetting question card UI`);
    const askCardContent = document.getElementById('ask-card-content');
    const recordingUI = document.getElementById('recording-ui');
    
    console.log('Ask card content element:', askCardContent);
    console.log('Recording UI element:', recordingUI);
    
    if (recordingUI) {
        // Clear the recording UI content to ensure we remove the answer display and match initial state
        recordingUI.innerHTML = `
            <div class="recording-animation">
                <div class="recording-pulse"></div>
                <div class="card-body-icon">🎙️</div>
            </div>
            <p class="recording-text">Recording your question...</p>
            <button onclick="event.stopPropagation(); stopRecording()" class="stop-recording-btn">
                <span class="stop-icon"></span>
                Stop Recording
            </button>
        `;
        console.log('Reset recording-ui content with animation');
    } else {
        console.error('recording-ui element not found');
    }

    // Start the new recording immediately - this will handle the UI display states
    console.log('Starting new recording session');
    startRecording();
}