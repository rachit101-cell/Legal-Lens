const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || `Upload failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getDocumentStatus(documentId: string) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: "GET",
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || `Failed to get status: ${response.statusText}`);
  }

  return response.json();
}

export async function getDocumentPages(documentId: string) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/pages`, {
    method: "GET",
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || `Failed to get pages: ${response.statusText}`);
  }

  return response.json();
}

export async function createChatSession(documentId: string) {
  const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ document_id: documentId }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || `Failed to create session: ${response.statusText}`);
  }

  return response.json();
}

export async function sendMessage(sessionId: string, message: string) {
  const response = await fetch(`${API_BASE_URL}/chat/${sessionId}/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || `Failed to send message: ${response.statusText}`);
  }

  return response.json();
}

export async function getDocumentAnalysis(documentId: string) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/analysis`, {
    method: "GET",
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || `Failed to get analysis: ${response.statusText}`);
  }

  return response.json();
}

export async function getDocumentClauses(documentId: string, page = 1, clauseType?: string, q?: string) {
  const params = new URLSearchParams({ page: String(page) });
  if (clauseType) params.append("clause_type", clauseType);
  if (q) params.append("q", q);

  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/clauses?${params.toString()}`, {
    method: "GET",
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || `Failed to get clauses: ${response.statusText}`);
  }

  return response.json();
}

export async function getDocumentFindings(documentId: string, severity?: string) {
  const params = new URLSearchParams();
  if (severity) params.append("severity", severity);

  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/findings?${params.toString()}`, {
    method: "GET",
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || `Failed to get findings: ${response.statusText}`);
  }

  return response.json();
}

export async function getDocumentTimeline(documentId: string) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/timeline`, {
    method: "GET",
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || `Failed to get timeline: ${response.statusText}`);
  }

  return response.json();
}

export async function getDocumentChecklist(documentId: string) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/checklist`, {
    method: "GET",
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || `Failed to get checklist: ${response.statusText}`);
  }

  return response.json();
}

export async function getDocumentQuestions(documentId: string) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/questions`, {
    method: "POST",
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error?.message || `Failed to get questions: ${response.statusText}`);
  }

  return response.json();
}

