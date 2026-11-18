# Phase 1 research dashboard

Local, read-only Astro + TypeScript app. Requires Node.js 22.23.4+ (or a newer supported LTS) and npm. From this directory:

```sh
npm install
npm run dev
```

Open the printed local URL (normally http://127.0.0.1:4321). To verify and preview production output:

```sh
npm run check
npm run build
npm test
npm run preview
```

`npm test` checks built routes, source-text fidelity, internal links and heading anchors, audit coverage counts and the distinction between the completed audit and unrun protocol. Run it after the build. Tables scroll horizontally on narrow screens; navigation and reading layouts adapt to mobile. There are no browser scripts, API keys, backend, remote fonts, raw vendor files or runtime service requests. External source links open only when followed.

## Source of truth

The app reads `../README.md`, `../research/exp001/DATA_AUDIT.md` and `../research/exp001/PROTOCOL.md` directly with paths resolved relative to `astro.config.mjs` before bundling, independent of the shell's working directory. Nothing is copied into a second report. Markdown is rendered in full, including GFM tables and code blocks, with a heading navigation and links to the GitHub sources on the research base branch (`codex/exp001-data-audit`). Local report links point to the corresponding dashboard reader.

The overview hypothesis, full audit decision paragraph and coverage cards are extracted from those documents. Extraction intentionally fails a build if the NO-GO decision or expected coverage rows change: review the curated explanation before accepting a different scientific state. The experiment explanation is a short, source-linked guide; the full reports remain authoritative. The protocol is conditional, frozen and **not activated**. Coverage counts are not forecast scores or counts of eligible forecast cases.

**Refresh limitation:** Markdown lives outside Astro's source tree and is read with Node's filesystem API. Restart `npm run dev` after report edits; automatic hot reload is not guaranteed. Rebuild production output after every report change. Preview serves only the last build.

## Adding an experiment later

Keep the convention small and explicit:

1. Add the authoritative reports under `research/exp002/` (as a separately authorized research change).
2. Add document entries with unique slugs and repository-relative paths to `src/lib/research.ts`'s `documents` manifest. The source reader routes and Data & Methods index are generated from it.
3. Add `src/pages/experiments/exp002.astro`, following EXP-001's six source-linked sections, and add its index link to the experiment index and overview. State the actual completion status and distinguish plans from results.
4. If adding overview metrics, extract them from the new report and extend the source-fidelity checks. Update the explicit GitHub source branch if the research base changes.
5. Run the check, build and tests above and inspect desktop and mobile layouts.

There is no experiment database or CMS. Phase 1 includes Overview, Experiments and Data & Methods only. Learn, Roadmap, visualizations, model fitting, synchronization and deployment are outside this app's scope. The dependency-free Python audit is unchanged.

## Dependency audit limitation

The current Astro release is locked in `package-lock.json`. At implementation time, `npm audit` still reported upstream advisories (including picomatch in build/dev tooling and dependencies of the Astro language server). `npm audit --omit=dev` also reports the picomatch dependency chain. No patched picomatch release was available from npm; the suggested forced Astro downgrade reintroduces older framework advisories. Recheck upstream patches before expanding beyond localhost use. The generated static dashboard has no client JavaScript or runtime dependencies.
