import Link from "next/link";
import {
  Scale,
  ShieldCheck,
  Clock,
  Search,
  ArrowRight,
  CheckCircle2,
  FileText,
  AlertTriangle,
  Sparkles,
  Lock,
  ChevronRight,
  ExternalLink,
  Shield,
  Layers,
  Check,
  Cpu,
  FileCheck,
  Zap,
} from "lucide-react";
import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.container}>
      {/* Dynamic Architectural Canvas & Multi-Spectrum Ambient Glow */}
      <div className={styles.heroBackground}>
        <div className={styles.glowTop} />
        <div className={styles.glowRight} />
        <div className={styles.glowLeft} />
        <div className={styles.gridPattern} />
      </div>

      <header className={styles.header}>
        <div className={styles.logo}>
          <div className={styles.logoIcon}>
            <Scale size={18} strokeWidth={2.2} />
          </div>
          <span className={styles.brandName}>LegalLens</span>
          <span className={styles.brandBadge}>PRO</span>
        </div>
        <nav className={styles.nav}>
          <Link href="#preview" className={styles.navLink}>Live Engine</Link>
          <Link href="#features" className={styles.navLink}>Capabilities</Link>
          <Link href="#architecture" className={styles.navLink}>Architecture</Link>
          <Link href="/upload" className={styles.navCta}>
            <span>Open Workspace</span>
            <ChevronRight size={14} />
          </Link>
        </nav>
      </header>

      <main className={styles.main}>
        {/* Shimmering Verification Pill */}
        <div className={styles.badge}>
          <span className={styles.badgePulse}>
            <span className={styles.badgeDot} />
          </span>
          <span className={styles.badgeCategory}>Deterministic AI Engine</span>
          <span className={styles.badgeDivider}>/</span>
          <span className={styles.badgeText}>Zero Hallucination Guarantee</span>
        </div>
        
        {/* Hero Title & Subtitle */}
        <h1 className={styles.title}>
          Precision AI for <br />
          <span className={styles.titleGradient}>Contract Intelligence</span> &amp; Review.
        </h1>
        
        <p className={styles.subtitle}>
          Engineered for corporate legal, procurement, and risk operations. Every finding is
          mathematically grounded and linked to verbatim agreement clauses with cryptographic certainty.
        </p>

        {/* Action CTAs */}
        <div className={styles.ctaContainer}>
          <Link href="/upload" className={styles.primaryButton}>
            <span>Analyze a Contract</span>
            <ArrowRight size={16} strokeWidth={2.2} />
          </Link>
          <Link href="/dashboard/doc_b137e5743500" className={styles.secondaryButton}>
            <Sparkles size={15} className={styles.sparkleIcon} />
            <span>View Interactive Demo</span>
          </Link>
        </div>

        {/* Trust Badges */}
        <div className={styles.trustBanner}>
          <div className={styles.trustItem}>
            <CheckCircle2 size={15} className={styles.trustCheck} />
            <span>Zero Data Retention</span>
          </div>
          <div className={styles.trustItem}>
            <CheckCircle2 size={15} className={styles.trustCheck} />
            <span>Verbatim Source Citations</span>
          </div>
          <div className={styles.trustItem}>
            <CheckCircle2 size={15} className={styles.trustCheck} />
            <span>Cryptographic Proof Matching</span>
          </div>
          <div className={styles.trustItem}>
            <CheckCircle2 size={15} className={styles.trustCheck} />
            <span>Deterministic Refusal Protocol</span>
          </div>
        </div>

        {/* Live Interactive Contract Verification Showcase */}
        <div className={styles.previewSection} id="preview">
          <div className={styles.previewHeader}>
            <div className={styles.previewDocInfo}>
              <div className={styles.previewFileIcon}>
                <FileText size={16} />
              </div>
              <span className={styles.previewFileName}>Standard_Mutual_NDA_v2.4.pdf</span>
              <span className={styles.previewStatusBadge}>
                <Check size={12} strokeWidth={2.5} /> Audited &bull; 100% Grounded
              </span>
            </div>
            <div className={styles.previewMeta}>
              <span className={styles.previewLatency}>Ingestion: 3.2s</span>
              <span className={styles.previewClausesCount}>12 Clauses Mapped</span>
            </div>
          </div>

          <div className={styles.previewContent}>
            {/* Left: Grounded Verbatim Extraction */}
            <div className={styles.previewSourceColumn}>
              <div className={styles.columnHeader}>
                <span className={styles.columnLabel}>VERBATIM CLAUSE EXTRACTION</span>
                <span className={styles.clauseRefTag}>Page 3 &bull; Section 4.2</span>
              </div>
              <div className={styles.clauseSnippetBox}>
                <p className={styles.clauseSnippetText}>
                  &ldquo;Recipient shall hold the Confidential Information in strict confidence and shall not disclose such information to any third party... <mark className={styles.highlightWarning}>provided, however, that Recipient&apos;s obligations under this Section shall expire exactly twelve (12) months</mark> following the Effective Date of this Agreement.&rdquo;
                </p>
                <div className={styles.clauseSnippetFooter}>
                  <span className={styles.snippetHash}>SHA-256: 4f9e2b...8a1c</span>
                  <span className={styles.snippetSourceType}>Original Vector Scan</span>
                </div>
              </div>
            </div>

            {/* Right: Deterministic Risk Synthesis */}
            <div className={styles.previewAnalysisColumn}>
              <div className={styles.columnHeader}>
                <span className={styles.columnLabel}>DETERMINISTIC RISK AUDIT</span>
                <span className={styles.riskLevelTag}>
                  <AlertTriangle size={12} /> HIGH RISK EXPOSURE
                </span>
              </div>

              <div className={styles.riskCard}>
                <h4 className={styles.riskTitle}>Abnormally Truncated Survival Window</h4>
                <p className={styles.riskDescription}>
                  Commercial NDA benchmark standards mandate a <strong>36 to 60 month</strong> survival covenant. A 12-month expiration forfeits intellectual property and proprietary trade secret protections prematurely.
                </p>
                <div className={styles.riskActionBox}>
                  <span className={styles.riskActionLabel}>PROPOSED REDLINE:</span>
                  <p className={styles.riskActionText}>
                    Extend survival duration to 36 months, with indefinite protection for proprietary codebases and trade secrets.
                  </p>
                </div>
                <div className={styles.verificationScoreBar}>
                  <div className={styles.scoreInfo}>
                    <span>Verification Confidence</span>
                    <span className={styles.scorePercent}>99.4%</span>
                  </div>
                  <div className={styles.scoreTrack}>
                    <div className={styles.scoreFill} style={{ width: "99.4%" }} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div className={styles.features} id="features">
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.iconShield}`}>
              <ShieldCheck size={22} strokeWidth={2} />
            </div>
            <div className={styles.featureBadge}>Deterministic Citation</div>
            <h3 className={styles.featureTitle}>Dual-Stage Evidence Layer</h3>
            <p className={styles.featureDesc}>
              Every assertion is verified against exact clause text. If ungrounded or speculative, the engine halts and marks the statement as unsupported.
            </p>
            <div className={styles.featureMetric}>
              <Zap size={13} /> <span>100% Verifiable Citations</span>
            </div>
          </div>
          
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.iconClock}`}>
              <Clock size={22} strokeWidth={2} />
            </div>
            <div className={styles.featureBadge}>Automated Synthesis</div>
            <h3 className={styles.featureTitle}>Contractual Timelines</h3>
            <p className={styles.featureDesc}>
              Synthesizes effective dates, notice periods, unilateral termination windows, and renewal triggers into a clean, actionable agenda.
            </p>
            <div className={styles.featureMetric}>
              <Clock size={13} /> <span>Dynamic Obligation Map</span>
            </div>
          </div>
          
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.iconSearch}`}>
              <Search size={22} strokeWidth={2} />
            </div>
            <div className={styles.featureBadge}>Risk Classification</div>
            <h3 className={styles.featureTitle}>Risk &amp; Gap Detection</h3>
            <p className={styles.featureDesc}>
              Heuristic scanners flag uncapped indemnities, silent dispute resolutions, and asymmetric liabilities with instant clause jump references.
            </p>
            <div className={styles.featureMetric}>
              <AlertTriangle size={13} /> <span>High/Med/Low Severity Triage</span>
            </div>
          </div>
        </div>

        {/* Architecture Section */}
        <div className={styles.architectureSection} id="architecture">
          <div className={styles.archContent}>
            <div className={styles.archTag}>SECURITY &amp; COMPLIANCE</div>
            <h2 className={styles.archTitle}>Engineered for Zero Data Retention &amp; Pure Grounding</h2>
            <p className={styles.archSubtitle}>
              Built from first principles for legal and compliance requirements. Documents are processed in isolated memory spaces, analyzed deterministically, and never used for foundation model training.
            </p>
            <div className={styles.archPills}>
              <span className={styles.archPill}><Cpu size={14} /> Ephemeral Processing</span>
              <span className={styles.archPill}><Lock size={14} /> TLS 1.3 Transport</span>
              <span className={styles.archPill}><Shield size={14} /> AES-256 Storage</span>
              <span className={styles.archPill}><FileCheck size={14} /> Verifiable Audit Log</span>
            </div>
          </div>
        </div>
      </main>

      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <div className={styles.footerBrand}>
            <div className={styles.logoIconSm}>
              <Scale size={14} />
            </div>
            <span>LegalLens &bull; Deterministic Contract Intelligence Platform</span>
          </div>
          <div className={styles.footerLinks}>
            <Link href="/upload" className={styles.footerLink}>Analyze Agreement</Link>
            <Link href="/dashboard/doc_b137e5743500" className={styles.footerLink}>Sample Report</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
