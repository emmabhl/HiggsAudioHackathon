let mediaRecorder = null;
let audioChunks = [];

async function startRecording() {
    // Don't start a new recording if one is already in progress
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        console.log('Recording already in progress, ignoring start request');
        return;
    }

    console.log('Starting new recording session');
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

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

  // Pick a supported MIME (WAV is rarely supported by MediaRecorder)
  const preferred = 'audio/webm;codecs=opus';
  const mimeType = MediaRecorder.isTypeSupported(preferred) ? preferred : '';

  mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);

  audioChunks = [];
  mediaRecorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) audioChunks.push(e.data); };

  mediaRecorder.onstop = async () => {
    const recordedType = mediaRecorder.mimeType || (audioChunks[0] && audioChunks[0].type) || 'application/octet-stream';
    const audioBlob = new Blob(audioChunks, { type: recordedType });
    audioChunks = [];

    // Loading UI
    document.getElementById('recording-ui').innerHTML = `
      <div class="loading-spinner"></div>
      <p class="recording-text">Processing your question...</p>
    `;

    try {
      // SEND RAW BLOB (not FormData)
      const response = await fetch('/live_chat/response', {
        method: 'POST',
        headers: { 'Content-Type': audioBlob.type || 'application/octet-stream' },
        body: audioBlob,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      // BACKEND RETURNS WAV BYTES → get as Blob and play
      const wavBlob = await response.blob();
      const wavUrl = URL.createObjectURL(wavBlob);

      // Simple playback UI
      document.getElementById('recording-ui').innerHTML = `
        <audio controls autoplay src="${wavUrl}"></audio>
        <button onclick="resetQuestionCard()" class="ask-another-btn">Ask Another Question</button>
      `;
    } catch (err) {
      console.error('Error processing question:', err);
      document.getElementById('recording-ui').innerHTML = `
        <div class="error-message">
          <p>Sorry, there was an error processing your question.</p>
          <button onclick="resetQuestionCard()" class="try-again-btn">Try Again</button>
        </div>
      `;
    } finally {
      // Stop tracks
      mediaRecorder.stream.getTracks().forEach(t => t.stop());
    }
  };

  mediaRecorder.start();
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
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
