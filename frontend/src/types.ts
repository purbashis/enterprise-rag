export type LLMProvider = 'local' | 'groq';

export interface WorkflowStep {
    agent: string;
    status: string;
    result?: unknown;
}

export interface WorkflowResponse {
    workflow_id: string;
    session_id: string;
    goal: string;
    answer: string;
    steps: WorkflowStep[];
    sources: string[];
}

export interface FileListResponse {
    files: string[];
}

export interface UploadResponse {
    message: string;
    chunks: number;
}
