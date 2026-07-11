---
layout: page
permalink: /repositories/
title: repositories
description: GitHub profile and repositories.
nav: true
nav_order: 3
---

{% if site.data.repositories.github_repos %}

## Selected repositories

<ul>
  {% for repo in site.data.repositories.github_repos %}
    <li><a href="https://github.com/{{ repo }}" rel="external nofollow noopener" target="_blank">{{ repo }}</a> - View on GitHub.</li>
  {% endfor %}
</ul>
{% endif %}
