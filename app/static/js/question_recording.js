let mediaRecorder = null;
let audioChunks = [];

function startRecording() {
    // Hide the card content and show the recording UI
    document.getElementById('ask-card-content').style.display = 'none';
    document.getElementById('recording-ui').style.display = 'flex';
    
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
    document.getElementById('ask-card-content').style.display = 'block';
    document.getElementById('recording-ui').style.display = 'none';
}