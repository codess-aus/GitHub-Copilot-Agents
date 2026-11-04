# GitHub Copilot Agents

A Material for MkDocs learning site built around 28 supplied infographics. **Editorial draft: not published.** The learning order is beginner to advanced, followed by the architecture summary and Resources.

## Run locally

Requires Python 3.12. From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m mkdocs serve --dev-addr 127.0.0.1:8000
```

Open the address printed by MkDocs. Stop the server with Ctrl+C. On macOS/Linux, use `.venv/bin/python` instead of `.\.venv\Scripts\python`.

```powershell
.\.venv\Scripts\python -m mkdocs build --strict
.\.venv\Scripts\python -m unittest discover -s tests -v
```

## Edit chapters and images

`content/chapters.yml` is the single source of truth for chapter order, stable slugs, titles, tile previews and Markdown explanations. Reorder entries to change the reading sequence. `hooks/chapters.py` generates chapter pages, the sidebar, tiles and previous/home/next links during every build. Do not edit the generated `site/` output. Chapter slugs become public URLs; keep them stable after launch.

Each entry maps one supplied image to a chapter. Originals are preserved byte-for-byte in `docs/assets/images/originals/`. Uncropped WebP hero and thumbnail derivatives are committed so a normal build requires no access to the original upload directory.

After replacing an original, regenerate derivatives:

```powershell
.\.venv\Scripts\python scripts\prepare_images.py
```

To re-import the exact listed uploads from a local directory:

```powershell
.\.venv\Scripts\python scripts\prepare_images.py --source-dir "C:\path\to\uploads"
```

Only files explicitly named in the catalogue are read. New chapters need a unique kebab-case slug, a PNG original and the same metadata fields as existing entries. Regenerate derivatives before building. Missing images and duplicate slugs fail the build.

Infographics retain their full aspect ratio, link to the original, and are accompanied by substantive semantic HTML explanations. These are editorial adaptations, not exhaustive transcripts. Audit the original diagrams' tiny text/code independently; the site does not silently alter the source images. The text corrects or qualifies version-sensitive claims. Review all chapters before launch.

## Appearance and author links

The supplied art uses violet, indigo, magenta and cyan. Gradients are used as framing, not body-text backgrounds. Theme tokens are in `docs/assets/stylesheets/site.css`. Atkinson Hyperlegible is self-hosted under `docs/assets/fonts/` with its SIL Open Font License; no Google Fonts request is needed. The header theme toggle respects the system preference initially and remembers a reader's selection.

Add real URLs under `extra` in `mkdocs.yml`. Leave missing links empty; do not use dummy destinations.

```yaml
extra:
  blog_url: "" # Replace with the author's actual HTTPS blog URL.
  social: [] # Each entry: {name: "Platform name", link: "actual HTTPS URL"}
  resources: [] # Each entry: {title: "Link title", url: "actual HTTPS URL", description: "Optional context"}
```

Review final wording, site title, accessibility, image rights/credits and resource/social/blog links with the author. Once approved, change `extra.project_status` and the draft notices in `docs/index.md` and the chapter template as appropriate.

## Deploy to GitHub Pages (only after approval)

Nothing in this setup enables Pages or publishes on push. `validate.yml` only builds and checks the site. `pages.yml` is **manual**, defaults to no publication, and only permits deployment from `main`. No live repository settings were changed.

When the author has approved publication:

1. Commit and push the reviewed source to this repository, then merge the reviewed work to `main`. No pull request is required by this setup.
2. In **Settings > Pages > Build and deployment**, select **GitHub Actions** as the source.
3. Optionally require a reviewer for the `github-pages` deployment environment in **Settings > Environments**. Configure this explicitly; declaring the environment in YAML does not create approval rules.
4. Open **Actions > Publish reviewed site > Run workflow**, choose `main`, and tick the publication confirmation only when ready.
5. Follow the deployment URL from the successful workflow. The expected project URL is `https://codess-aus.github.io/GitHub-Copilot-Agents/`.

The workflow builds strictly and checks internal links before uploading a Pages artifact. Deployment receives only `pages: write` and `id-token: write`; validation receives `contents: read`. A push alone cannot deploy. A false confirmation builds but skips deployment. First-time manual workflows must exist on the default branch before GitHub shows their Run workflow control.

If publication fails, inspect the Actions run, confirm Pages uses GitHub Actions, confirm the selected branch is `main`, and check environment protection requirements. Do not use `mkdocs gh-deploy` alongside this artifact-based workflow.

## Accessibility checks

The foundation includes a skip link (from Material), landmarks, visible keyboard focus, large navigation targets, one H1 per page, decorative tile alt text, descriptive hero links, reduced-motion handling, full-width uncropped images, and left-aligned readable text. HTML explanations remain available without JavaScript; theme switching and search use JavaScript.

Before publishing, check keyboard-only navigation, a screen reader, both themes, 200% zoom, narrow screens and the quality/completeness of the image explanations. Automated checks cannot certify WCAG compliance or guarantee a particular font will suit every dyslexic reader.
