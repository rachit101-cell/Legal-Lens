"use client";

import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { UploadCloud, FileText, CheckCircle, Shield, AlertTriangle, Scale, Lock, ArrowLeft } from "lucide-react";
import styles from "./page.module.css";
import { uploadDocument, getDocumentStatus } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState(0);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Poll for document status
  const pollStatus = async (documentId: string) => {
    try {
      const res = await getDocumentStatus(documentId);
      if (res.status === "COMPLETED") {
        setProcessingStage(3);
        setTimeout(() => {
          router.push(`/dashboard/${documentId}`);
        }, 800);
      } else if (res.status === "ERROR") {
        setError("Document processing failed on the server.");
        setIsProcessing(false);
      } else {
        // Still processing
        setTimeout(() => pollStatus(documentId), 2000);
      }
    } catch (err: any) {
      setError(err.message || "Failed to check status.");
      setIsProcessing(false);
    }
  };

  const handleFileChange = useCallback(async (file: File | null) => {
    if (!file) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx'].includes(ext || '')) {
      setError("Please upload a PDF or DOCX file.");
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setError("File size exceeds 20MB limit.");
      return;
    }

    try {
      setError(null);
      setIsProcessing(true);
      setProcessingStage(0);

      // Stage 1: Uploading
      const response = await uploadDocument(file);
      
      setProcessingStage(1);
      
      // Stage 2: Processing (Server side)
      pollStatus(response.document_id);
      
      setTimeout(() => {
        if (processingStage < 2) setProcessingStage(2);
      }, 1500);

    } catch (err: any) {
      console.error("Upload error:", err);
      setError(err.message || "Failed to upload document. Is the backend running?");
      setIsProcessing(false);
    }
  }, [router, processingStage]);

  return (
    <div className={styles.container}>
      <div className={styles.pageBackground}>
        <div className={styles.glowTop} />
        <div className={styles.glowRight} />
        <div className={styles.gridPattern} />
      </div>

      <header className={styles.header}>
        <Link href="/" className={styles.logo}>
          <div className={styles.logoIcon}>
            <Scale size={18} strokeWidth={2.2} />
          </div>
          <span className={styles.brandName}>LegalLens</span>
        </Link>
        <Link href="/" className={styles.backHomeLink}>
          <ArrowLeft size={14} /> Back to Home
        </Link>
      </header>

      <main className={styles.main}>
        <div className={styles.uploadCard}>
          <div className={styles.cardHeaderIcon}>
            <Scale size={28} strokeWidth={2} />
          </div>
          <h1 className={styles.title}>Secure Document Ingestion</h1>
          <p className={styles.subtitle}>Upload your agreement, contract, or regulatory filing for deterministic verification.</p>

          <div 
            className={`${styles.dropzone} ${isDragging ? styles.dragActive : ''}`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              const files = e.dataTransfer.files;
              if (files?.length) handleFileChange(files[0]);
            }}
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              style={{ display: "none" }}
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={(e) => {
                const files = e.target.files;
                if (files?.length) handleFileChange(files[0]);
              }}
            />
            
            <div className={styles.dropzoneIcon}>
              <UploadCloud size={30} strokeWidth={1.8} />
            </div>
            <div className={styles.dropzoneText}>Drag &amp; drop your legal document here</div>
            <div className={styles.dropzoneSubtext}>Supports Adobe PDF and Microsoft Word (.docx) up to 20MB</div>
            <button className={styles.browseButton} type="button">Select File from Computer</button>
          </div>

          {error && (
            <div className={styles.errorBox}>
              <AlertTriangle size={18} />
              <span>{error}</span>
            </div>
          )}

          <div className={styles.securityNote}>
            <Lock size={14} className={styles.securityIcon} />
            <span>Encrypted with TLS 1.3. Documents are processed ephemerally with zero data retention.</span>
          </div>

          {isProcessing && (
            <div className={styles.processingOverlay}>
              <div className={styles.spinner} />
              <div className={styles.processingTitle}>Analyzing Document</div>
              <div className={styles.stageList}>
                <div className={`${styles.stageItem} ${processingStage >= 0 ? (processingStage > 0 ? styles.completed : styles.active) : ''}`}>
                  <div className={styles.stageIcon}>
                    {processingStage > 0 ? <CheckCircle size={14} /> : '1'}
                  </div>
                  <span>Uploading securely</span>
                </div>
                <div className={`${styles.stageItem} ${processingStage >= 1 ? (processingStage > 1 ? styles.completed : styles.active) : ''}`}>
                  <div className={styles.stageIcon}>
                    {processingStage > 1 ? <CheckCircle size={14} /> : '2'}
                  </div>
                  <span>Extracting clauses &amp; layout</span>
                </div>
                <div className={`${styles.stageItem} ${processingStage >= 2 ? (processingStage > 2 ? styles.completed : styles.active) : ''}`}>
                  <div className={styles.stageIcon}>
                    {processingStage > 2 ? <CheckCircle size={14} /> : '3'}
                  </div>
                  <span>Synthesizing Situation Map &amp; Risks</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
