const API_URL = window.location.origin; // Dynamically use the same origin as the frontend

const fileUpload = document.getElementById('file-upload');
const uploadStatus = document.getElementById('upload-status');
const queryForm = document.getElementById('query-form');
const queryInput = document.getElementById('query-input');
const chatMessages = document.getElementById('chat-messages');
const fileList = document.getElementById('file-list');
const modelProvider = document.getElementById('model-provider');
const customKeyGroup = document.getElementById('custom-key-group');
const customApiKey = document.getElementById('custom-api-key');
const localModelGroup = document.getElementById('local-model-group');
const localModelName = document.getElementById('local-model-name');
const clearAllBtn = document.getElementById('clear-all-btn');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');

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

// Provider Selection logic
modelProvider.addEventListener('change', () => {
    customKeyGroup.classList.add('hidden');
    localModelGroup.classList.add('hidden');

    if (modelProvider.value === 'custom') {
        customKeyGroup.classList.remove('hidden');
    } else if (modelProvider.value === 'local') {
        localModelGroup.classList.remove('hidden');
    }
});

// Load existing files on start
async function loadFiles() {
    try {
        const response = await fetch(`${API_URL}/list-files`);
        const data = await response.json();
        renderFileList(data.files);
    } catch (error) {
        console.error('Failed to load files:', error);
    }
}

function renderFileList(files) {
    fileList.innerHTML = '';
    files.forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <span class="file-name" title="${file}">${file}</span>
            <button class="delete-file-btn" onclick="deleteFile('${file}')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"></path>
                </svg>
            </button>
        `;
        fileList.appendChild(item);
    });
}

window.deleteFile = async (filename) => {
    if (!confirm(`Delete ${filename}?`)) return;
    try {
        const response = await fetch(`${API_URL}/delete/${filename}`, { method: 'DELETE' });
        if (response.ok) {
            loadFiles();
            addMessage('assistant', `Deleted document: ${filename}`);
        }
    } catch (error) {
        console.error('Delete failed:', error);
    }
};

clearAllBtn.addEventListener('click', async () => {
    if (!confirm('This will delete ALL documents and clear the Knowledge Base. Continue?')) return;
    try {
        const response = await fetch(`${API_URL}/reset`, { method: 'POST' });
        if (response.ok) {
            loadFiles();
            chatMessages.innerHTML = `
                <div class="message assistant">
                    <div class="bubble">Knowledge base and chat cleared. How can I help you today?</div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Reset failed:', error);
    }
});

// Handle File Upload
fileUpload.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    uploadStatus.textContent = 'Uploading and indexing...';
    uploadStatus.className = 'status-msg loading';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            uploadStatus.textContent = 'File indexed successfully!';
            uploadStatus.className = 'status-msg success';
            loadFiles();
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
            body: JSON.stringify({
                question,
                provider: modelProvider.value,
                api_key: customApiKey.value || null,
                ollama_model: localModelName.value || 'mistral'
            })
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
        sourcesDiv.className = 'sources'; // Match existing CSS
        const uniqueSources = [...new Set(sources)];
        sourcesDiv.textContent = `Sources: ${uniqueSources.join(', ')}`;
        msgDiv.appendChild(sourcesDiv);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Health Check logic
async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/`);
        if (response.ok) {
            statusDot.classList.add('online');
            statusText.textContent = 'Backend: Online';
        } else {
            throw new Error('Offline');
        }
    } catch (error) {
        statusDot.classList.remove('online');
        statusText.textContent = 'Backend: Offline';
    }
}

// Initial load
loadFiles();
checkHealth();

// Check health every 30 seconds
setInterval(checkHealth, 30000);
