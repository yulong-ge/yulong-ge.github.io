# Blog Writing Workflow

## Publish a post

Create a Markdown file in `_posts/` named `YYYY-MM-DD-slug.md`.

Chinese-first post front matter:

```yaml
---
layout: post
title: "文章标题"
date: 2026-07-10 12:00:00 +0800
description: "用于列表、搜索和分享预览的简短摘要。"
tags: [machine-learning]
categories: [research-notes]
lang: zh-CN
giscus_comments: true
---
```

For an English post, use `lang: en`. When publishing both languages, use two
posts with distinct slugs such as `topic-zh` and `topic-en`, then add a visible
link to the counterpart near the beginning of each post.

The theme does not provide automatic translation. AI-assisted translation is
best done before publishing so equations, terminology, and citations can be
reviewed. Chinese is the site default; English posts remain first-class posts
in the same Blog, search index, archives, and feed.

## Keep drafts private

Drafts belong in `_drafts/`, which is ignored by Git and never enters the public
repository. Preview them locally with:

```bash
bundle exec jekyll serve --drafts
```

Move a finished draft to `_posts/YYYY-MM-DD-slug.md` before committing it.

## RSS

Published posts are included automatically in `/feed.xml`. Drafts and ordinary
page edits are not included.
