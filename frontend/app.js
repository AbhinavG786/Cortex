const API_BASE_URL = 'http://localhost:5000/api/v1';

document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('videoFile');
    const submitBtn = document.getElementById('submitBtn');
    const statusMsg = document.getElementById('statusMessage');
    const resultsContainer = document.getElementById('results-container');
    
    const file = fileInput.files[0];
    if (!file) return;

    submitBtn.disabled = true;
    statusMsg.className = 'status';
    statusMsg.textContent = 'Uploading...';
    resultsContainer.style.display = 'none';

    const formData = new FormData();
    formData.append('video', file);

    try {
       
        const response = await fetch(`${API_BASE_URL}/videos`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok && response.status !== 202) {
            throw new Error(data.error || 'Failed to upload video');
        }

        statusMsg.textContent = 'Processing video... This may take a minute depending on file size.';
        
        pollProcessingStatus(data.video_id);

    } catch (error) {
        handleError(error.message);
    }
});

async function pollProcessingStatus(videoId) {
    const statusMsg = document.getElementById('statusMessage');

    try {

        const response = await fetch(`${API_BASE_URL}/videos/${videoId}/roi`);
        const data = await response.json();

        if (data.status === 'pending' || data.status === 'processing') {

            setTimeout(() => pollProcessingStatus(videoId), 2000);
        } else if (data.status === 'completed') {
            statusMsg.textContent = 'Processing complete!';
            displayResults(videoId, data.rois);
            document.getElementById('submitBtn').disabled = false;
        } else {
            throw new Error('Video processing failed on the server.');
        }
    } catch (error) {
        handleError('Error checking status: ' + error.message);
    }
}

function displayResults(videoId, rois) {
    const resultsContainer = document.getElementById('results-container');
    const videoElement = document.getElementById('processedVideo');
    const tbody = document.querySelector('#roiTable tbody');

    videoElement.src = `${API_BASE_URL}/videos/${videoId}/stream?t=${new Date().getTime()}`;

    tbody.innerHTML = '';
    rois.forEach(roi => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${roi.frame_number}</td>
            <td>${roi.x_min}</td>
            <td>${roi.y_min}</td>
            <td>${roi.width}</td>
            <td>${roi.height}</td>
        `;
        tbody.appendChild(tr);
    });

    resultsContainer.style.display = 'block';
}

function handleError(message) {
    const statusMsg = document.getElementById('statusMessage');
    const submitBtn = document.getElementById('submitBtn');
    
    statusMsg.className = 'error';
    statusMsg.textContent = message;
    submitBtn.disabled = false;
}