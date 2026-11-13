# Wireframes

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Descriptive wireframe baseline  
**Purpose:** Specify the intended Wireframes requirements and implementation constraints.  
**Scope:** Covers the proposed Wireframes behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Overview

~~~text
┌─────────────────┬─────────────────────────────────────────────────┐
│ Cosmos          │ Page title                 UTC / freshness      │
│ Overview        ├─────────────────────────────────────────────────┤
│ Astronomy       │ Source status: APOD | NeoWs | DONKI | EONET      │
│ Asteroids       ├─────────────────────────┬───────────────────────┤
│ Space Weather   │ APOD feature + details  │ Near approach list    │
│ Earth Events    ├─────────────────────────┼───────────────────────┤
│ NASA Media      │ Space-weather timeline  │ Earth event list/map  │
│ AI / Reports    └─────────────────────────┴───────────────────────┘
└─────────────────┘
~~~

## Record detail

Header: title, source-origin badge, date, stale badge. Main: media or visualization on left; normalized fields and explanation on right. Footer: source record ID, primary-source link, retrieved time, credit/copyright, save control, ask-assistant action.

## Assistant

Header: generated-content notice. Main: conversation thread. Each answer has sections for answer, source-backed facts, model interpretation, limitations, and retrieved evidence cards. Composer stays at bottom; show retrieval and generation states separately. Error states preserve typed question and show retry only if safe.

## Related documents

[UX Specification](UX_SPECIFICATION.md), [Design System](DESIGN_SYSTEM.md), [Accessibility](ACCESSIBILITY.md).
