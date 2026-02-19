import '../style.css';
import { FileListResponse, LLMProvider, QueryResponse, UploadResponse } from './types.ts';

const API_URL = window.location.origin;

// DOM Elements
const fileUpload = document.getElementById('file-upload') as HTMLInputElement;
const uploadStatus = document.getElementById('upload-status') as HTMLDivElement;
const queryForm = document.getElementById('query-form') as HTMLFormElement;
const queryInput = document.getElementById('query-input') as HTMLInputElement;
const chatMessages = document.getElementById('chat-messages') as HTMLDivElement;
const fileList = document.getElementById('file-list') as HTMLDivElement;
const modelProvider = document.getElementById('model-provider') as HTMLSelectElement;
const customKeyGroup = document.getElementById('custom-key-group') as HTMLDivElement;
const customApiKey = document.getElementById('custom-api-key') as HTMLInputElement;
const localModelGroup = document.getElementById('local-model-group') as HTMLDivElement;
const localModelName = document.getElementById('local-model-name') as HTMLInputElement;
const clearAllBtn = document.getElementById('clear-all-btn') as HTMLButtonElement;
const statusDot = document.getElementById('status-dot') as HTMLSpanElement;
const statusText = document.getElementById('status-text') as HTMLSpanElement;

// Sidebar Toggle logic
const sidebar = document.getElementById('sidebar') as HTMLElement;
const toggleBtn = document.getElementById('sidebar-toggle') as HTMLButtonElement;
const overlay = document.getElementById('sidebar-overlay') as HTMLDivElement;

function toggleSidebar(): void {
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

    const provider = modelProvider.value as LLMProvider;
    if (provider === 'custom') {
        customKeyGroup.classList.remove('hidden');
    } else if (provider === 'local') {
        localModelGroup.classList.remove('hidden');
    }
});

// Load existing files on start
async function loadFiles(): Promise<void> {
    try {
        const response = await fetch(`${API_URL}/list-files`);
        if (!response.ok) throw new Error('Failed to fetch files');
        const data: FileListResponse = await response.json();
        renderFileList(data.files);
    } catch (error) {
        console.error('Failed to load files:', error);
    }
}

function renderFileList(files: string[]): void {
    fileList.innerHTML = '';
    files.forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <span class="file-name" title="${file}">${file}</span>
            <button class="delete-file-btn" data-filename="${file}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"></path>
                </svg>
            </button>
        `;

        const deleteBtn = item.querySelector('.delete-file-btn') as HTMLButtonElement;
        deleteBtn.onclick = () => deleteFile(file);

        fileList.appendChild(item);
    });
}

async function deleteFile(filename: string): Promise<void> {
    if (!confirm(`Delete ${filename}?`)) return;
    try {
        const response = await fetch(`${API_URL}/delete/${filename}`, { method: 'DELETE' });
        if (response.ok) {
            await loadFiles();
            addMessage('assistant', `Deleted document: ${filename}`);
        }
    } catch (error) {
        console.error('Delete failed:', error);
    }
}

clearAllBtn.addEventListener('click', async () => {
    if (!confirm('This will delete ALL documents and clear the Knowledge Base. Continue?')) return;
    try {
        const response = await fetch(`${API_URL}/reset`, { method: 'POST' });
        if (response.ok) {
            await loadFiles();
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
fileUpload.addEventListener('change', async (e: Event) => {
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
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
            const data: UploadResponse = await response.json();
            uploadStatus.textContent = `Success! Indexed ${data.chunks} chunks.`;
            uploadStatus.className = 'status-msg success';
            await loadFiles();
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
    // Clear input so same file can be uploaded again if needed
    target.value = '';
});

// Handle Query Submission
queryForm.addEventListener('submit', async (e: Event) => {
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
            const data: QueryResponse = await response.json();
            updateMessage(loadingBubble, data.answer, data.sources);
        } else {
            const error = await response.json();
            updateMessage(loadingBubble, `Error: ${error.detail}`);
        }
    } catch (err) {
        updateMessage(loadingBubble, 'Failed to connect to backend.');
    }
});

function addMessage(type: 'assistant' | 'user', text: string): HTMLDivElement {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;

    msgDiv.innerHTML = `
        <div class="bubble">${text}</div>
    `;

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgDiv;
}

function updateMessage(msgDiv: HTMLDivElement, text: string, sources: string[] = []): void {
    const bubble = msgDiv.querySelector('.bubble') as HTMLDivElement;
    bubble.textContent = text;

    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';
        const uniqueSources = [...new Set(sources)];
        sourcesDiv.textContent = `Sources: ${uniqueSources.join(', ')}`;
        msgDiv.appendChild(sourcesDiv);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Health Check logic
async function checkHealth(): Promise<void> {
    try {
        const response = await fetch(`${API_URL}/list-files`); // Simple check to list-files or root
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
