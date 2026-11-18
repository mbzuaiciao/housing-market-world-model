import { readFile } from "node:fs/promises";
import { createMarkdownProcessor } from "@astrojs/markdown-remark";

// Explicit Phase 1 manifest. Root is resolved in Astro config before bundling.
export const documents = [
  {
    slug: "project",
    title: "Project brief",
    path: "README.md",
    description: "The research question and current decision.",
  },
  {
    slug: "audit",
    title: "Data feasibility audit",
    path: "research/exp001/DATA_AUDIT.md",
    description:
      "Completed · definitions, coverage, exclusions and provenance.",
  },
  {
    slug: "protocol",
    title: "Conditional forecasting protocol",
    path: "research/exp001/PROTOCOL.md",
    description: "Planned · frozen conditional on GO; not activated.",
  },
] as const;
export type Document = (typeof documents)[number];
declare const __RESEARCH_ROOT__: string;
const repositoryRoot = new URL(__RESEARCH_ROOT__);
export const githubRoot =
  "https://github.com/mbzuaiciao/housing-market-world-model/blob/codex/exp001-data-audit/";
export const sourceUrl = (document: Document) => githubRoot + document.path;
export const documentUrl = (document: Document) => `/methods/${document.slug}/`;

export async function rawDocument(document: Document) {
  return readFile(new URL(document.path, repositoryRoot), "utf8");
}

// Preserve all report text, tables and code. Only local Markdown destinations change.
interface MarkdownNode {
  type: string;
  url?: string;
  children?: MarkdownNode[];
}
function localLinks() {
  return (tree: MarkdownNode) => {
    function visit(node: MarkdownNode) {
      if (node.type === "link" && typeof node.url === "string") {
        const [path, fragment] = node.url.split("#");
        const target = documents.find(
          (doc) => doc.path === path || doc.path.endsWith("/" + path),
        );
        if (path && target)
          node.url = documentUrl(target) + (fragment ? `#${fragment}` : "");
      }
      node.children?.forEach(visit);
    }
    visit(tree);
  };
}
const processor = createMarkdownProcessor({ remarkPlugins: [localLinks] });
export async function renderDocument(document: Document) {
  return (await processor).render(await rawDocument(document));
}

export async function projectHypothesis() {
  const raw = await rawDocument(documents[0]);
  const paragraph = raw.split("\n\n")[1];
  if (!paragraph?.startsWith("**EXP-001**"))
    throw new Error("Project brief changed: review the overview hypothesis.");
  return paragraph.replaceAll("**", "");
}

export async function auditSummary() {
  const raw = await rawDocument(documents[1]);
  const decision = raw.split("\n\n")[1];
  if (!decision?.startsWith("**Decision: NO-GO"))
    throw new Error(
      "Audit decision changed: review the Phase 1 summary before building.",
    );
  const screenedCount = (label: string) => {
    const row = raw.split("\n").find((line) => line.startsWith(`| ${label} |`));
    const value = row?.split("|")[3]?.trim();
    if (!value || !/^[\d,]+$/.test(value))
      throw new Error(`Missing audit coverage row: ${label}`);
    return value;
  };
  return {
    decision: decision.replaceAll("**", ""),
    metrics: [
      {
        value: screenedCount("Unflagged observed pairs"),
        label: "Unflagged metro-month pairs",
        note: "Attention + newly pending listings",
      },
      {
        value: screenedCount("Matched metros"),
        label: "Candidate metros",
        note: "Exact legacy-to-2023 county screen",
      },
      {
        value: screenedCount(
          "Unflagged with inventory, price and at least one rate reading in month",
        ),
        label: "Pairs with same-month controls",
        note: "Coverage only; release timing unverified",
      },
      {
        value: screenedCount("Metros with unflagged pairs in all 105 months"),
        label: "Metros with all 105 months",
        note: "2018-01 through 2026-09",
      },
    ],
  };
}
