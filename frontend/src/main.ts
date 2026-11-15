import '../style.css';
import { FileListResponse, LLMProvider, UploadResponse, WorkflowResponse } from './types.ts';

const API_URL = window.location.port === '5173' ? 'http://localhost:8000' : window.location.origin;

function requiredElement<T extends HTMLElement>(id: string): T {
    const element = document.getElementById(id);
    if (!element) throw new Error(`Missing required page element: ${id}`);
    return element as T;
}

const workflowForm = requiredElement<HTMLFormElement>('workflow-form');
const goalInput = requiredElement<HTMLTextAreaElement>('goal-input');
const includeWeb = requiredElement<HTMLInputElement>('include-web');
const apiEndpoint = requiredElement<HTMLInputElement>('api-endpoint');
const modelProvider = requiredElement<HTMLSelectElement>('model-provider');
const ollamaModel = requiredElement<HTMLInputElement>('ollama-model');
const ollamaModelGroup = requiredElement<HTMLDivElement>('ollama-model-group');
const groqKey = requiredElement<HTMLInputElement>('groq-key');
const groqKeyGroup = requiredElement<HTMLDivElement>('groq-key-group');
const runButton = requiredElement<HTMLButtonElement>('run-button');
const workflowStatus = requiredElement<HTMLParagraphElement>('workflow-status');
const resultPanel = requiredElement<HTMLElement>('result-panel');
const fileUpload = requiredElement<HTMLInputElement>('file-upload');
const uploadStatus = requiredElement<HTMLParagraphElement>('upload-status');
const fileList = requiredElement<HTMLDivElement>('file-list');
const fileCount = requiredElement<HTMLSpanElement>('file-count');
const clearAllButton = requiredElement<HTMLButtonElement>('clear-all-btn');
const statusDot = requiredElement<HTMLSpanElement>('status-dot');
const statusText = requiredElement<HTMLSpanElement>('status-text');

function getSessionId(): string {
    let sessionId = sessionStorage.getItem('fieldwork-session');
    if (!sessionId) {
        sessionId = crypto.randomUUID();
        sessionStorage.setItem('fieldwork-session', sessionId);
    }
    return sessionId;
}

async function readError(response: Response): Promise<string> {
    try {
        const body = await response.json() as { detail?: string };
        return body.detail || `Request failed (${response.status})`;
    } catch {
        return `Request failed (${response.status})`;
    }
}

modelProvider.addEventListener('change', () => {
    const isGroq = modelProvider.value === 'groq';
    groqKeyGroup.classList.toggle('is-hidden', !isGroq);
    ollamaModelGroup.classList.toggle('is-hidden', isGroq);
});

workflowForm.addEventListener('submit', async (event: SubmitEvent) => {
    event.preventDefault();
    const goal = goalInput.value.trim();
    if (goal.length < 3) {
        workflowStatus.textContent = 'Enter a goal with at least 3 characters.';
        return;
    }

    const provider = modelProvider.value as LLMProvider;
    if (provider === 'groq' && !groqKey.value.trim()) {
        workflowStatus.textContent = 'Add your Groq API key or switch to Ollama.';
        return;
    }

    runButton.disabled = true;
    workflowStatus.textContent = 'Running memory, retrieval and research steps…';
    renderLoading();

    const payload = {
        goal,
        provider,
        api_key: provider === 'groq' ? groqKey.value.trim() : null,
        ollama_model: ollamaModel.value.trim() || 'qwen2.5:3b',
        include_web: includeWeb.checked,
        api_endpoint: apiEndpoint.value.trim() || null,
        session_id: getSessionId(),
    };

    try {
        const response = await fetch(`${API_URL}/agent/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!response.ok) throw new Error(await readError(response));
        const result = await response.json() as WorkflowResponse;
        renderWorkflow(result);
        workflowStatus.textContent = `Completed · ${result.steps.length} agent steps`;
    } catch (error) {
        const message = error instanceof Error ? error.message : 'Research request failed.';
        workflowStatus.textContent = message;
        renderError(message);
    } finally {
        runButton.disabled = false;
    }
});

function renderLoading(): void {
    resultPanel.replaceChildren();
    const loading = document.createElement('div');
    loading.className = 'loading-state';
    loading.textContent = 'Coordinating your research…';
    resultPanel.appendChild(loading);
}

function renderError(message: string): void {
    resultPanel.replaceChildren();
    const notice = document.createElement('p');
    notice.className = 'error-state';
    notice.textContent = message;
    resultPanel.appendChild(notice);
}

function renderWorkflow(result: WorkflowResponse): void {
    resultPanel.replaceChildren();

    const heading = document.createElement('div');
    heading.className = 'result-heading';
    const label = document.createElement('p');
    label.className = 'eyebrow';
    label.textContent = 'RESEARCH RESULT';
    const goal = document.createElement('h2');
    goal.textContent = result.goal;
    heading.append(label, goal);

    const answer = document.createElement('p');
    answer.className = 'answer-text';
    answer.textContent = result.answer;
    resultPanel.append(heading, answer);

    if (result.sources.length) {
        const sources = document.createElement('div');
        sources.className = 'source-list';
        const sourceHeading = document.createElement('span');
        sourceHeading.className = 'source-label';
        sourceHeading.textContent = 'Sources';
        sources.appendChild(sourceHeading);
        result.sources.forEach((source) => {
            let link: HTMLAnchorElement | undefined;
            try {
                const url = new URL(source);
                if (url.protocol === 'https:' || url.protocol === 'http:') {
                    link = document.createElement('a');
                    link.href = url.href;
                    link.target = '_blank';
                    link.rel = 'noreferrer';
                    link.textContent = url.hostname;
                }
            } catch {
                // Document source names are labels, not links.
            }
            const item = link || document.createElement('span');
            if (!link) item.textContent = source;
            item.className = 'source-item';
            sources.appendChild(item);
        });
        resultPanel.appendChild(sources);
    }

    const steps = document.createElement('details');
    steps.className = 'steps-details';
    const summary = document.createElement('summary');
    summary.textContent = `Agent trace · ${result.steps.length} steps`;
    steps.appendChild(summary);
    const list = document.createElement('ol');
    result.steps.forEach((step) => {
        const item = document.createElement('li');
        const agent = document.createElement('strong');
        agent.textContent = step.agent.replaceAll('_', ' ');
        item.appendChild(agent);
        item.append(` · ${step.status}`);
        if (step.result !== undefined) {
            const output = document.createElement('pre');
            output.textContent = JSON.stringify(step.result, null, 2);
            item.appendChild(output);
        }
        list.appendChild(item);
    });
    steps.appendChild(list);
    resultPanel.appendChild(steps);
}

async function loadFiles(): Promise<void> {
    try {
        const response = await fetch(`${API_URL}/list-files`);
        if (!response.ok) throw new Error(await readError(response));
        const data = await response.json() as FileListResponse;
        fileCount.textContent = String(data.files.length);
        fileList.replaceChildren();
        if (!data.files.length) {
            const empty = document.createElement('p');
            empty.className = 'muted';
            empty.textContent = 'No documents yet.';
            fileList.appendChild(empty);
            return;
        }
        data.files.forEach((filename) => {
            const item = document.createElement('div');
            item.className = 'file-item';
            const name = document.createElement('span');
            name.className = 'file-name';
            name.textContent = filename;
            const remove = document.createElement('button');
            remove.className = 'remove-file';
            remove.type = 'button';
            remove.setAttribute('aria-label', `Delete ${filename}`);
            remove.textContent = '×';
            remove.addEventListener('click', () => deleteFile(filename));
            item.append(name, remove);
            fileList.appendChild(item);
        });
    } catch (error) {
        fileList.textContent = error instanceof Error ? error.message : 'Could not load documents.';
    }
}

async function deleteFile(filename: string): Promise<void> {
    const response = await fetch(`${API_URL}/delete/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
    });
    if (!response.ok) {
        uploadStatus.textContent = await readError(response);
        return;
    }
    await loadFiles();
}

fileUpload.addEventListener('change', async () => {
    const file = fileUpload.files?.[0];
    if (!file) return;
    uploadStatus.textContent = `Indexing ${file.name}…`;
    const formData = new FormData();
    formData.append('file', file);
    try {
        const response = await fetch(`${API_URL}/upload`, { method: 'POST', body: formData });
        if (!response.ok) throw new Error(await readError(response));
        const result = await response.json() as UploadResponse;
        uploadStatus.textContent = `${result.message} · ${result.chunks} chunks`;
        await loadFiles();
    } catch (error) {
        uploadStatus.textContent = error instanceof Error ? error.message : 'Upload failed.';
    } finally {
        fileUpload.value = '';
    }
});

clearAllButton.addEventListener('click', async () => {
    if (!window.confirm('Clear uploaded documents, the vector index and agent memory?')) return;
    clearAllButton.disabled = true;
    try {
        const response = await fetch(`${API_URL}/reset`, { method: 'POST' });
        if (!response.ok) throw new Error(await readError(response));
        uploadStatus.textContent = 'Workspace cleared.';
        await loadFiles();
        resultPanel.innerHTML = '';
        const empty = document.createElement('div');
        empty.className = 'empty-state';
        const title = document.createElement('h2');
        title.textContent = 'Your work will appear here';
        const text = document.createElement('p');
        text.textContent = 'Each run records its tool steps and saves a memory for later.';
        empty.append(title, text);
        resultPanel.appendChild(empty);
    } catch (error) {
        uploadStatus.textContent = error instanceof Error ? error.message : 'Workspace reset failed.';
    } finally {
        clearAllButton.disabled = false;
    }
});

async function checkHealth(): Promise<void> {
    try {
        const response = await fetch(`${API_URL}/health`);
        if (!response.ok) throw new Error('Backend is unavailable.');
        statusDot.classList.add('is-online');
        statusText.textContent = 'Connected';
    } catch {
        statusDot.classList.remove('is-online');
        statusText.textContent = 'Backend offline';
    }
}

void loadFiles();
void checkHealth();
window.setInterval(() => void checkHealth(), 30_000);
