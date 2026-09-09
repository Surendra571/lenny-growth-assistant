import { Artifact, ChatResponse, Message, Session, Ship30Response, SystemHealth } from '../types';

const API_BASE = '/api/v1';

async function handleResponse<T>(res: Response, defaultError: string): Promise<T> {
  if (!res.ok) {
    let errorDetail = defaultError;
    try {
      const errorJson = await res.json();
      if (errorJson.error && errorJson.error.message) {
        errorDetail = errorJson.error.message;
      } else if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      errorDetail = `${defaultError} (${res.status} ${res.statusText})`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export async function checkHealth(): Promise<SystemHealth> {
  const res = await fetch('/health');
  return handleResponse<SystemHealth>(res, 'Failed to fetch service health status');
}

export async function listSessions(): Promise<Session[]> {
  const res = await fetch(`${API_BASE}/sessions`);
  return handleResponse<Session[]>(res, 'Failed to fetch conversations');
}

export async function createSession(title?: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: title || 'New Growth Conversation' }),
  });
  return handleResponse<Session>(res, 'Failed to create conversation');
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!res.ok && res.status !== 204) {
    throw new Error(`Failed to delete session (${res.status})`);
  }
}

export async function listMessages(sessionId: string): Promise<Message[]> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`);
  return handleResponse<Message[]>(res, 'Failed to load conversation history');
}

export async function sendMessage(
  sessionId: string,
  message: string,
  skillOverride?: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      skill_override: skillOverride || null,
    }),
  });
  return handleResponse<ChatResponse>(res, 'Inference request failed');
}

export async function generateShip30(
  sessionId: string,
  topic?: string,
  audience?: string,
  angle?: string,
  tone?: string
): Promise<Ship30Response> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/ship30`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic,
      audience,
      angle,
      tone,
    }),
  });
  return handleResponse<Ship30Response>(res, 'Failed to generate Ship 30 essay');
}

export async function listSessionArtifacts(sessionId: string): Promise<Artifact[]> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/artifacts`);
  return handleResponse<Artifact[]>(res, 'Failed to fetch session artifacts');
}

export async function getArtifact(id: string): Promise<Artifact> {
  const res = await fetch(`${API_BASE}/artifacts/${id}`);
  return handleResponse<Artifact>(res, 'Failed to fetch artifact');
}

export async function createArtifact(
  sessionId: string,
  title: string,
  artifactType: 'markdown' | 'html' | 'svg',
  content: string,
  metadata?: Record<string, any>
): Promise<Artifact> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/artifacts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      title,
      artifact_type: artifactType,
      content,
      metadata: metadata || {},
    }),
  });
  return handleResponse<Artifact>(res, 'Failed to create artifact');
}

export async function deleteArtifact(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/artifacts/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok && res.status !== 204) {
    throw new Error('Failed to delete artifact');
  }
}
