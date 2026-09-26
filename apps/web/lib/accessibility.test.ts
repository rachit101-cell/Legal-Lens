import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

describe("Web Accessibility & Standards (WCAG 2.1 AA/AAA)", () => {
  it("globals.css contains focus-visible styling and reduced motion support", () => {
    const cssPath = path.resolve(__dirname, "../app/globals.css");
    const content = fs.readFileSync(cssPath, "utf-8");

    expect(content).toContain(":focus-visible");
    expect(content).toContain("prefers-reduced-motion");
    expect(content).toContain(".sr-only");
    expect(content).toContain(".skip-link");
  });

  it("layout.tsx includes a skip-to-content navigation link", () => {
    const layoutPath = path.resolve(__dirname, "../app/layout.tsx");
    const content = fs.readFileSync(layoutPath, "utf-8");

    expect(content).toContain('href="#main-content"');
    expect(content).toContain('className="skip-link"');
  });

  it("upload page has accessible landmarks, dropzone keyboard handler, and aria labels", () => {
    const uploadPath = path.resolve(__dirname, "../app/upload/page.tsx");
    const content = fs.readFileSync(uploadPath, "utf-8");

    expect(content).toContain('id="main-content"');
    expect(content).toContain('role="button"');
    expect(content).toContain("tabIndex={0}");
    expect(content).toContain('role="alert"');
    expect(content).toContain('role="status"');
    expect(content).toContain('aria-label=');
  });

  it("dashboard page has tablist semantics, aria-selected, and accessible chat inputs", () => {
    const dashPath = path.resolve(__dirname, "../app/dashboard/[id]/page.tsx");
    const content = fs.readFileSync(dashPath, "utf-8");

    expect(content).toContain('role="tablist"');
    expect(content).toContain('role="tab"');
    expect(content).toContain("aria-selected=");
    expect(content).toContain("aria-haspopup=");
    expect(content).toContain('aria-label="Ask a question grounded in this document"');
  });
});
