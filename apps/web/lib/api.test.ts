import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  uploadDocument,
  getDocumentStatus,
  getDocumentPages,
  createChatSession,
  sendMessage,
  getDocumentAnalysis,
  getDocumentClauses,
  getDocumentFindings,
  getDocumentTimeline,
  getDocumentChecklist,
  getDocumentQuestions,
} from "./api";

describe("Web API Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("uploadDocument successfully posts form data and returns result", async () => {
    const fakeResponse = { document_id: "doc_123", status: "QUEUED" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => fakeResponse,
    });

    const file = new File(["dummy content"], "contract.pdf", { type: "application/pdf" });
    const result = await uploadDocument(file);

    expect(result).toEqual(fakeResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/documents/upload"),
      expect.objectContaining({ method: "POST" })
    );
  });

  it("uploadDocument throws descriptive error on failure", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      statusText: "Bad Request",
      json: async () => ({ error: { message: "File exceeds 20MB limit" } }),
    });

    const file = new File(["test"], "huge.pdf", { type: "application/pdf" });
    await expect(uploadDocument(file)).rejects.toThrow("File exceeds 20MB limit");
  });

  it("getDocumentStatus calls correct URL and parses JSON", async () => {
    const fakeStatus = { document_id: "doc_123", status: "COMPLETED" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => fakeStatus,
    });

    const result = await getDocumentStatus("doc_123");
    expect(result).toEqual(fakeStatus);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/documents/doc_123"),
      expect.objectContaining({ method: "GET" })
    );
  });

  it("createChatSession sends document_id in body", async () => {
    const fakeSession = { session_id: "sess_456" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => fakeSession,
    });

    const result = await createChatSession("doc_123");
    expect(result).toEqual(fakeSession);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/chat/sessions"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ document_id: "doc_123" }),
      })
    );
  });

  it("sendMessage posts user question to chat session", async () => {
    const fakeAnswer = {
      message_id: "msg_789",
      answer: "The lease terminates in 30 days.",
      answer_status: "SUPPORTED",
      citations: [{ claim: "Terminates in 30 days", source_ids: ["clause_1"] }],
    };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => fakeAnswer,
    });

    const result = await sendMessage("sess_456", "When does this terminate?");
    expect(result).toEqual(fakeAnswer);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/chat/sess_456/message"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ message: "When does this terminate?" }),
      })
    );
  });

  it("getDocumentClauses correctly formats query parameters", async () => {
    const fakeClauses = { clauses: [], total: 0 };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => fakeClauses,
    });

    await getDocumentClauses("doc_123", 2, "PAYMENT_FEES", "deposit");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/documents\/doc_123\/clauses\?page=2&clause_type=PAYMENT_FEES&q=deposit/),
      expect.objectContaining({ method: "GET" })
    );
  });
});
