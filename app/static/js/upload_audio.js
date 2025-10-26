document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const audioFileInput = document.getElementById('audio-file');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadStatus = document.getElementById('upload-status');
    
    // Update file input label with selected filename
    audioFileInput.addEventListener('change', function(e) {
        const fileName = e.target.files[0]?.name || 'Choose file';
        e.target.nextElementSibling.textContent = fileName;
        uploadBtn.disabled = !e.target.files.length;
    });

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData();
        formData.append('audio', audioFileInput.files[0]);

        try {
            uploadStatus.textContent = 'Uploading...';
            uploadBtn.disabled = true;

            const response = await fetch('/new_entry/upload_file', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                uploadStatus.textContent = 'File uploaded successfully!';
                alert('File uploaded successfully!');
                window.location.href = '/';
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Error:', error);
            uploadStatus.textContent = 'Error: ' + error.message;
            uploadBtn.disabled = false;
        }
    });
});