import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import { test } from "node:test";
import { parse, parseFragment } from "parse5";
import { createMarkdownProcessor } from "@astrojs/markdown-remark";

const root = new URL("../", import.meta.url);
const read = (path) => readFile(new URL(path, root), "utf8");
const documents = [
  ["project", "../README.md"],
  ["audit", "../research/exp001/DATA_AUDIT.md"],
  ["protocol", "../research/exp001/PROTOCOL.md"],
];
function all(node) {
  return [node, ...(node.childNodes ?? []).flatMap(all)];
}
function attr(node, name) {
  return node.attrs?.find((a) => a.name === name)?.value;
}
function text(node) {
  return node.nodeName === "#text"
    ? node.value
    : (node.childNodes ?? []).map(text).join("");
}
function normalized(node) {
  return text(node).replace(/\s+/g, " ").trim();
}
async function pages(directory = "dist") {
  const entries = await readdir(new URL(directory + "/", root), {
    withFileTypes: true,
  });
  return (
    await Promise.all(
      entries.map((entry) =>
        entry.isDirectory()
          ? pages(`${directory}/${entry.name}`)
          : entry.name.endsWith(".html")
            ? [`${directory}/${entry.name}`]
            : [],
      ),
    )
  ).flat();
}

test("all seven Phase 1 routes build, with no client scripts or forms", async () => {
  const routes = await pages();
  assert.equal(routes.length, 7);
  for (const path of [
    "index.html",
    "experiments/index.html",
    "experiments/exp001/index.html",
    "methods/index.html",
    ...documents.map(([slug]) => `methods/${slug}/index.html`),
  ]) {
    const html = await read(`dist/${path}`);
    assert.match(html, /<html lang="en">/);
    assert.match(html, /Skip to content/);
    assert.doesNotMatch(html, /<(script|form|iframe)\b/);
  }
});

test("full source report text, tables, code and external citations survive rendering", async () => {
  const processor = await createMarkdownProcessor();
  for (const [slug, path] of documents) {
    const expected = parseFragment(
      (await processor.render(await read(path))).code,
    );
    const actualPage = parse(await read(`dist/methods/${slug}/index.html`));
    const article = all(actualPage).find((n) => n.tagName === "article");
    assert.ok(article, slug);
    assert.equal(
      normalized(article),
      normalized(expected),
      `${slug}: all report text must be preserved`,
    );
    for (const tag of ["table", "pre", "h2", "h3"]) {
      assert.equal(
        all(article).filter((n) => n.tagName === tag).length,
        all(expected).filter((n) => n.tagName === tag).length,
        `${slug}: ${tag}`,
      );
    }
    const externalLinks = (tree) =>
      all(tree)
        .filter((n) => n.tagName === "a")
        .map((n) => attr(n, "href"))
        .filter((href) => href?.startsWith("https://"));
    assert.deepEqual(
      externalLinks(article),
      externalLinks(expected),
      `${slug}: external source URLs`,
    );
  }
});

test("every local page, stylesheet and fragment resolves", async () => {
  for (const path of await pages()) {
    const route = "/" + path.replace(/^dist\//, "").replace(/index.html$/, "");
    const nodes = all(parse(await read(path)));
    for (const node of nodes.filter(
      (n) => n.tagName === "a" || n.tagName === "link",
    )) {
      const href = attr(node, "href");
      if (!href || /^[a-z]+:/i.test(href)) continue;
      const url = new URL(href, "http://local" + route);
      const file = `dist${url.pathname}${url.pathname.endsWith("/") ? "index.html" : ""}`;
      const target = await read(file);
      if (url.hash) {
        const ids = all(parse(target)).map((n) => attr(n, "id"));
        assert.ok(
          ids.includes(decodeURIComponent(url.hash.slice(1))),
          `${path}: broken ${href}`,
        );
      }
    }
  }
});

test("coverage cards match screened audit counts and NO-GO is explicit", async () => {
  const audit = await read("../research/exp001/DATA_AUDIT.md");
  const overview = parse(await read("dist/index.html"));
  const values = all(overview)
    .filter((n) => attr(n, "class") === "metric-value")
    .map(normalized);
  const labels = [
    "Unflagged observed pairs",
    "Matched metros",
    "Unflagged with inventory, price and at least one rate reading in month",
    "Metros with unflagged pairs in all 105 months",
  ];
  assert.deepEqual(
    values,
    labels.map((label) =>
      audit
        .split("\n")
        .find((line) => line.startsWith(`| ${label} |`))
        .split("|")[3]
        .trim(),
    ),
  );
  for (const path of [
    "dist/index.html",
    "dist/experiments/exp001/index.html",
  ]) {
    const html = normalized(parse(await read(path)));
    assert.match(html, /NO-GO/);
    assert.match(html, /Data feasibility/);
    assert.match(html, /forecasting comparison has not been run/);
  }
});
