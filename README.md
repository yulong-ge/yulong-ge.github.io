# Yulong Ge

Personal academic website built with the [al-folio](https://github.com/alshedivat/al-folio) Jekyll theme and deployed at <https://yulong-ge.github.io/>.

## Content

- `/_pages/about.md`: homepage biography and education.
- `/_pages/blog.md`: blog index.
- `/_pages/publications.md` and `/_bibliography/papers.bib`: publications.
- `/_data/cv.yml`: English CV content used by the web CV page and English PDF.
- `/_data/cv_zh.yml`: Chinese CV content used by the Chinese PDF.
- `/assets/rendercv/rendercv_output/`: generated English and Chinese CV PDFs.
- `/_data/socials.yml`: contact and social links.
- `/_data/repositories.yml`: GitHub profile and repository cards.

## Local Preview

Use the project Ruby/Bundler setup or Docker support from al-folio, then serve the site locally with:

```bash
bundle exec jekyll serve --host 127.0.0.1 --port 4000
```
