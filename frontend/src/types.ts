export type LLMProvider = 'groq' | 'local' | 'custom';

export interface QueryRequest {
    question: string;
    provider: LLMProvider;
    api_key?: string | null;
    ollama_model?: string;
}

export interface QueryResponse {
    answer: string;
    sources: string[];
}

export interface FileListResponse {
    files: string[];
}

export interface UploadResponse {
    message: string;
    chunks: number;
}

export interface StatusMsg {
    text: string;
    type: 'loading' | 'success' | 'error' | '';
}
