---
layout: page
permalink: /blog/
title: blog
description: 中文为主的研究笔记与技术写作 / Research notes and technical writing.
nav: true
nav_order: 1
pagination:
  enabled: true
  collection: posts
  permalink: /page/:num/
  per_page: 5
  sort_field: date
  sort_reverse: true
---

{% if site.posts.size > 0 %}

<ul class="post-list">
  {% assign blog_posts = paginator.posts | default: site.posts %}
  {% for post in blog_posts %}
    <li>
      <h3><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h3>
      <p class="post-meta">{{ post.date | date: "%B %-d, %Y" }}</p>
      {% if post.description %}
        <p>{{ post.description }}</p>
      {% else %}
        <p>{{ post.excerpt | strip_html | truncatewords: 35 }}</p>
      {% endif %}
    </li>
  {% endfor %}
</ul>

{% include pagination.liquid %}

{% else %}

Posts will be added here.

{% endif %}
