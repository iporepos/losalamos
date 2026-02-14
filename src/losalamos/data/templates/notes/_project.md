---
note_type: project
timestamp: <% tp.file.creation_date("YYYY-MM-DD HH:mm:ss") %>
tags:
  - project
  - losalamos
aliases:
  - Project Note
  - Note for Projects
subject:
url:
abstract:
name: <% tp.file.title %>
title:
alias:
category:
service_id:
crea_id:
contract:
client:
status: on going
revenue_expected:
revenue:
expenses:
date_start:
date_end:
---
# <% tp.file.title %>

PROJECT

**`=this.title`**

`=this.category`   |   `=this.status`   |   R$ `=this.revenue_expected`

> [!Abstract] Summary
> {a paragraph description of the note}

---

> [!example]+ Related 
> - {related links}

# Lists

## Core team


## Expanded team


## Contractors


## Clients


## Products


---
# Routines


## Invoices


## Payments


---
# Tasks


---
# Planning


---
# Meetings

```dataview
TABLE WITHOUT ID
    timestamp as "Date",
    kind as "Kind",
    abstract as "Abstract",
    link(file.link, "==== Meeting File ====") as File
FROM ""
WHERE contains(file.folder, this.file.folder)
  AND contains(file.tags, "#meeting")
SORT timestamp DESC
```

---
# Resources


---
# Other resources
