---
note_type: journal
timestamp: <% tp.file.creation_date("YYYY-MM-DD HH:mm:ss") %>
tags:
  - journal
  - science
  - research
aliases:
subject:
url:
name: <% tp.file.title %>
abstract:
title: <% tp.file.title %>
abbreviation:
acronym:
scope:
impact_factor:
issn:
open_access:
deadlines:
url_submission:
publisher:
---
# <% tp.file.title %>

JOURNAL

![[<% tp.file.title %>.jpeg|500]]

> [!Abstract] Summary
> {a paragraph description of the note}

---

> [!example]+ Related 
> - {related links}

# Introduction

*Insert main content here*

---

# Publishing

Web portal: `=this.url_submission`

Login info:

---

# Aim and scope

*Insert main content here*

---

# Guide for authors

*Insert main content here*

---

# Available papers

```dataview
table WITHOUT ID citation_in as Author, title as Title, year as Year, journal as Journal, link(file.link, "File") as File FROM "alexandria/papers"
WHERE journal = this.name
SORT year DESC
```


---
# Resources

> [!info] Other references
> - {related references}