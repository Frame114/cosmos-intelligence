import type { ReactNode } from "react";

const allowedTags = new Set(["A", "BR", "EM", "P", "STRONG", "SUB", "SUP"]);

function renderNodes(node: Node, keyPrefix: string): ReactNode[] {
  return Array.from(node.childNodes).map((child, index) => {
    const key = `${keyPrefix}-${index}`;
    if (child.nodeType === Node.TEXT_NODE) return child.textContent;
    if (!(child instanceof HTMLElement)) return null;

    const tag = child.tagName;
    const children = renderNodes(child, key);
    if (!allowedTags.has(tag)) return children;
    if (tag === "BR") return <br key={key} />;
    if (tag === "A") {
      const href = child.getAttribute("href");
      try {
        const url = href ? new URL(href, "https://apod.nasa.gov/") : null;
        if (url?.protocol === "https:") {
          return <a key={key} href={url.href} target="_blank" rel="noreferrer">{children}</a>;
        }
      } catch {
        // Invalid links are rendered as their text.
      }
      return <span key={key}>{children}</span>;
    }
    const Tag = tag.toLowerCase() as "em" | "p" | "strong" | "sub" | "sup";
    return <Tag key={key}>{children}</Tag>;
  });
}

export function SafeMarkup({ value, fallback }: { value?: string | null; fallback?: string }) {
  if (!value) return <>{fallback ?? ""}</>;
  // Some APOD Basic records entity-escape markup inside an otherwise marked-up
  // explanation. Decode one HTML layer, then rebuild only the allowlisted nodes.
  const decoder = document.createElement("textarea");
  decoder.innerHTML = value;
  const parsed = new DOMParser().parseFromString(decoder.value, "text/html");
  return <>{renderNodes(parsed.body, "safe-markup")}</>;
}
