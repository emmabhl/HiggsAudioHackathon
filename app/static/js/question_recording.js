let mediaRecorder = null;
let audioChunks = [];

async function startRecording() {
  document.getElementById('ask-card-content').style.display = 'none';
  document.getElementById('recording-ui').style.display = 'flex';

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
  document.getElementById('ask-card-content').style.display = 'block';
  document.getElementById('recording-ui').style.display = 'none';
}
