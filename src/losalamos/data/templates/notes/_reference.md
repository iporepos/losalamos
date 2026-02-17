---
note_type: reference
timestamp: <% tp.file.creation_date("YYYY-MM-DD HH:mm:ss") %>
tags:
  - reference-note
aliases:
subject:
category:
name: <% tp.file.title %>
pdf:
download:
cite_inline:
cite_bibli:
entry_type:
author:
title:
subtitle:
year:
doi:
url:
abstract:
note:
issn:
journal:
issue:
volume:
month:
number:
pages:
isbn:
edition:
publisher:
booktitle:
chapter:
howpublished:
organization:
institution:
location:
type:
language:
version:
---
# <% tp.file.title %>

`= upper(this.entry_type)`

![[<% tp.file.title %>.jpeg|300]]

**`=this.title`**

By `=this.cite_inline`

- File: `=this.pdf`
- URL: `=this.url`
- DOI: `=this.doi`

> [!Info] Abstract
> {a paragraph description of the note}

---

# Overview

> [!Abstract]+ Highlights
> - List highlights

> [!Example]+ Related
> - List related notes

---
# Comments

*Start typing here*

---
# References

- List references

---
# Bibliographic information

## In-line citation
```
{cite_inline}
```

## Full citation
```
{cite_bibli}
```

## BibTeX entry
```
{bibtex}
```
