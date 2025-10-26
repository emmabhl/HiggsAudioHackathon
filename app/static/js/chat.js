document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-message');
    const voiceButton = document.getElementById('voice-input');
    const chatMessages = document.getElementById('chat-messages');
    
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    // Fonction pour ajouter un message au chat
    function addMessage(message, isUser = false, audioUrl = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user-message' : 'assistant-message');
        
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        contentDiv.textContent = message;
        
        messageDiv.appendChild(contentDiv);
        
        // Ajouter le contrôle audio si disponible
        if (audioUrl && !isUser) {
            const audio = new Audio(audioUrl);
            
            // S'assurer que l'audio est chargé avant de le jouer
            audio.addEventListener('canplaythrough', () => {
                audio.play().catch(e => console.error('Erreur de lecture auto:', e));
            }, { once: true });
            
            const audioControls = document.createElement('div');
            audioControls.classList.add('audio-controls');
            
            const playButton = document.createElement('button');
            playButton.classList.add('btn', 'btn-sm', 'btn-link', 'play-audio');
            playButton.innerHTML = '<i class="fas fa-play"></i>';
            
            playButton.addEventListener('click', () => {
                audio.play().catch(e => console.error('Erreur de lecture manuelle:', e));
            });
            
            audioControls.appendChild(playButton);
            messageDiv.appendChild(audioControls);
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Fonction pour envoyer un message
    async function sendMessage(message) {
        addMessage(message, true);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            addMessage(data.response, false, data.audioUrl);
        } catch (error) {
            console.error('Error:', error);
            addMessage('Une erreur est survenue. Veuillez réessayer.', false);
        }
    }

    // Gestionnaire d'événements pour l'envoi de messages
    sendButton.addEventListener('click', () => {
        const message = chatInput.value.trim();
        if (message) {
            sendMessage(message);
            chatInput.value = '';
        }
    });

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendButton.click();
        }
    });

    // Gestion de l'enregistrement vocal
    voiceButton.addEventListener('click', async () => {
        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const formData = new FormData();
                    formData.append('audio', audioBlob);

                    try {
                        const transcriptionResponse = await fetch('/api/transcribe', {
                            method: 'POST',
                            body: formData
                        });

                        if (transcriptionResponse.ok) {
                            const data = await transcriptionResponse.json();
                            chatInput.value = data.transcription;
                            sendMessage(data.transcription);
                        } else {
                            throw new Error('Transcription failed');
                        }

                    } catch (error) {
                        console.error('Error:', error);
                        addMessage('Une erreur est survenue lors de la transcription. Veuillez réessayer.', false);
                    }

                    voiceButton.classList.remove('recording');
                    voiceButton.querySelector('i').classList.remove('fa-stop');
                    voiceButton.querySelector('i').classList.add('fa-microphone');
                    isRecording = false;
                };

                mediaRecorder.start();
                isRecording = true;
                voiceButton.classList.add('recording');
                voiceButton.querySelector('i').classList.remove('fa-microphone');
                voiceButton.querySelector('i').classList.add('fa-stop');

            } catch (err) {
                console.error('Error accessing microphone:', err);
                addMessage('Erreur d\'accès au microphone. Veuillez vérifier les permissions.', false);
            }
        } else if (isRecording && mediaRecorder) {
            // Arrêter l'enregistrement si le bouton est cliqué pendant l'enregistrement
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            // Réinitialiser l'apparence du bouton immédiatement
            voiceButton.classList.remove('recording');
            voiceButton.querySelector('i').classList.remove('fa-stop');
            voiceButton.querySelector('i').classList.add('fa-microphone');
            isRecording = false;
        }
    });

    // Message de bienvenue
    setTimeout(() => {
        addMessage('Hello! Welcome to QuarkNotes. What would you like to learn today?', false);
    }, 500);
});