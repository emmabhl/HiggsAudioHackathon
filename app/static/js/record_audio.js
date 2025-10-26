document.addEventListener('DOMContentLoaded', function() {
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let isPaused = false;
    let startTime;
    let timerInterval;

    // DOM Elements
    const recordBtn = document.getElementById('record-btn');
    const pauseBtn = document.getElementById('pause-btn');
    const stopBtn = document.getElementById('stop-btn');
    const playbackBtn = document.getElementById('playback-btn');
    const reRecordBtn = document.getElementById('re-record-btn');
    const saveBtn = document.getElementById('save-btn');
    const audioPlayback = document.getElementById('audio-playback');
    const timerDisplay = document.getElementById('timer');

    // Timer function
    function updateTimer() {
        const currentTime = new Date();
        const elapsedTime = new Date(currentTime - startTime);
        const minutes = elapsedTime.getMinutes().toString().padStart(2, '0');
        const seconds = elapsedTime.getSeconds().toString().padStart(2, '0');
        timerDisplay.textContent = `${minutes}:${seconds}`;
    }

    // Start recording
    recordBtn.addEventListener('click', async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                audioPlayback.src = URL.createObjectURL(audioBlob);
                playbackBtn.style.display = 'inline-block';
                reRecordBtn.style.display = 'inline-block';
                saveBtn.style.display = 'inline-block';
            };

            mediaRecorder.start();
            isRecording = true;
            startTime = new Date();
            timerInterval = setInterval(updateTimer, 1000);

            recordBtn.style.display = 'none';
            pauseBtn.style.display = 'inline-block';
            stopBtn.style.display = 'inline-block';
        } catch (err) {
            console.error('Error accessing microphone:', err);
            alert('Error accessing microphone. Please ensure you have granted permission.');
        }
    });

    // Pause/Resume recording
    pauseBtn.addEventListener('click', () => {
        if (isRecording) {
            if (!isPaused) {
                mediaRecorder.pause();
                pauseBtn.innerHTML = '<i class="fas fa-play"></i> Resume';
                clearInterval(timerInterval);
            } else {
                mediaRecorder.resume();
                pauseBtn.innerHTML = '<i class="fas fa-pause"></i> Pause';
                timerInterval = setInterval(updateTimer, 1000);
            }
            isPaused = !isPaused;
        }
    });

    // Stop recording
    stopBtn.addEventListener('click', () => {
        if (isRecording) {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            isRecording = false;
            clearInterval(timerInterval);
            stopBtn.style.display = 'none';
            pauseBtn.style.display = 'none';
        }
    });

    // Playback recording
    playbackBtn.addEventListener('click', () => {
        if (audioPlayback.paused) {
            audioPlayback.style.display = 'block';
            audioPlayback.play();
            playbackBtn.textContent = '⏸ Pause';
        } else {
            audioPlayback.pause();
            playbackBtn.textContent = '▶️ Play Recording';
        }
    });

    // Re-record
    reRecordBtn.addEventListener('click', () => {
        audioChunks = [];
        audioPlayback.src = '';
        audioPlayback.style.display = 'none';
        playbackBtn.style.display = 'none';
        reRecordBtn.style.display = 'none';
        saveBtn.style.display = 'none';
        recordBtn.style.display = 'inline-block';
        timerDisplay.textContent = '00:00';
    });

    // Save recording
    saveBtn.addEventListener('click', async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        
        try {
            // D'abord, on obtient la transcription
            const transcribeFormData = new FormData();
            transcribeFormData.append('audio', audioBlob);
            
            const transcribeResponse = await fetch('/api/transcribe', {
                method: 'POST',
                body: transcribeFormData
            });
            
            if (!transcribeResponse.ok) {
                throw new Error('Failed to transcribe audio');
            }
            
            const transcribeResult = await transcribeResponse.json();
            
            // Ensuite, on sauvegarde l'enregistrement avec la transcription
            const saveFormData = new FormData();
            saveFormData.append('audio', audioBlob);
            saveFormData.append('transcription', transcribeResult.transcription);
            
            const saveResponse = await fetch('/new_entry/save_entry', {
                method: 'POST',
                body: saveFormData
            });

            if (saveResponse.ok) {
                const result = await saveResponse.json();
                alert('Entry saved successfully!');
                window.location.href = '/';
            } else {
                throw new Error('Failed to save entry');
            }
        } catch (error) {
            console.error('Error saving entry:', error);
            alert('Error saving entry: ' + error.message);
        }
    });
});