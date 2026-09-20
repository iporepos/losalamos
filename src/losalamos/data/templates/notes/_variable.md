---
note_type: variable
timestamp: <% tp.file.creation_date("YYYY-MM-DD HH:mm:ss") %>
tags:
  - variable-note
aliases:
subject:
code:
alias:
name: <% tp.file.title %>
synonyms:
title:
abstract:
symbol:
category:
dimension:
units:
dtype:
range:
source:
---
# <% tp.file.title %>

VARIABLE NOTE

> [!Abstract] Summary
> {a paragraph description of the note}

---

> [!example]+ Related 
> - {related links}

## Main

*Insert main content here*

---
## Definitions

 - `subject` - thematic subject. Like "Hydrology". I can be a link to vault wiki "[[The Subject]]"
 - `code` - unique code given by user.
 - `alias` - short word used for naming columns. Eg, "TAS" for Air Surface Temperature. Does not need to be unique across all subjects.
 - `name` - unique name of the varible. Can be a composite moderate size word. Like "Normalized Difference Vegetation Index". Same name as the file. Mandatory entry.
 - `synonyms` - list of other names related. Non-exaustive. List is separated by pipe. Eg, "Rain | Rainfall".
 - `title` - Long full name.
 - `abstract` - Long text explaining the variable.
 - `symbol` - LaTeX symbol. Does not need to be unique, but recommended in the subject.
 - `category` - open categorization field. 
 - `dimension` - physical dimension notation. Eg. "L/T" for velocity
 - `units` - SI recommended units. Use of (dt) for open time step. Eg. "mm/(dt)"
 - `dtype` - Primitive data type considering no storage compression, following SQLite convention. Real, Integer, Text, Boolean, Blob. Usually only Real and Integer.
 - `range` - mathematical range notation using parenthesis, brackets and "U" for the range. Eg. "(0U1)" mean from 0 to 1 inclusive. "(U)" means the full range.  
 - `source` - field available for citation of the main source. "Rouse (1974)" or "[[Rouse_1974_a]]" for a wiki link.

---
## Resources

> [!info] Other references
> - {related references}