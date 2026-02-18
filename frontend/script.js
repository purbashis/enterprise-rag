const API_URL = 'http://localhost:8000';

const fileUpload = document.getElementById('file-upload');
const uploadStatus = document.getElementById('upload-status');
const queryForm = document.getElementById('query-form');
const queryInput = document.getElementById('query-input');
const chatMessages = document.getElementById('chat-messages');

// Sidebar Toggle logic
const sidebar = document.getElementById('sidebar');
const toggleBtn = document.getElementById('sidebar-toggle');
const overlay = document.getElementById('sidebar-overlay');

function toggleSidebar() {
    sidebar.classList.toggle('active');
    toggleBtn.classList.toggle('active');
    overlay.classList.toggle('active');
}

toggleBtn.addEventListener('click', toggleSidebar);
overlay.addEventListener('click', toggleSidebar);

// Handle File Upload
fileUpload.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    uploadStatus.textContent = 'Uploading and indexing...';
    uploadStatus.className = 'status-msg loading';

    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            uploadStatus.textContent = 'File indexed successfully!';
            uploadStatus.className = 'status-msg success';
            addMessage('assistant', `I've successfully indexed "${file.name}". You can now ask questions about it.`);
        } else {
            const error = await response.json();
            uploadStatus.textContent = `Upload failed: ${error.detail}`;
            uploadStatus.className = 'status-msg error';
        }
    } catch (err) {
        uploadStatus.textContent = 'Check if backend is running.';
        uploadStatus.className = 'status-msg error';
    }
});

// Handle Query Submission
queryForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = queryInput.value.trim();
    if (!question) return;

    addMessage('user', question);
    queryInput.value = '';

    const loadingBubble = addMessage('assistant', 'Thinking...');

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        if (response.ok) {
            const data = await response.json();
            updateMessage(loadingBubble, data.answer, data.sources);
        } else {
            const error = await response.json();
            updateMessage(loadingBubble, `Error: ${error.detail}`);
        }
    } catch (err) {
        updateMessage(loadingBubble, 'Failed to connect to backend.');
    }
});

function addMessage(type, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;

    msgDiv.innerHTML = `
        <div class="bubble">${text}</div>
    `;

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgDiv;
}

function updateMessage(msgDiv, text, sources = []) {
    const bubble = msgDiv.querySelector('.bubble');
    bubble.textContent = text;

    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';
        const uniqueSources = [...new Set(sources)];
        sourcesDiv.textContent = `Sources: ${uniqueSources.join(', ')}`;
        msgDiv.appendChild(sourcesDiv);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}
