---
note_type: basic
timestamp: <% tp.file.creation_date("YYYY-MM-DD HH:mm:ss") %>
tags:
  - basic-note
aliases:
subject:
url:
name: <% tp.file.title %>
abstract:
doi:
entry_type:
author:
title:
subtitle:
year:
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
pdf:
cite_inline:
cite_bibli:
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
