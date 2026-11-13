# Design System

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Design baseline  
**Purpose:** Specify the intended Design System requirements and implementation constraints.  
**Scope:** Covers the proposed Design System behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Tokens and components

| Token | Initial value/purpose |
|---|---|
| Background | Deep navy #07111F; primary surface #101D2D; elevated card #15263A. |
| Text | Primary #F2F6FA; muted #A9B8C8; maintain WCAG contrast against surface. |
| Accent | Cyan/blue for navigation and links; not a sole status indicator. |
| Status | Green/blue for healthy/current, amber for stale/warning, red for failed; include icon and text label. |
| Typography | System sans for body; tabular numerals for measurements; no all-caps paragraph labels. |
| Spacing | 4 px base spacing scale; 8 px typical control gap; 16/24 px content spacing. |
| Radius | 6–10 px for cards and controls; use subtle border rather than glow. |

Reusable components: AppShell, PrimaryNav, PageHeader, FilterBar, SearchInput, DataTable, MetricCard, ChartCard, Timeline, MapPanel, SourceBadge, FreshnessBadge, ProvenancePanel, DetailDrawer, SaveButton, EvidenceCard, EmptyState, ErrorState, LoadingState, ConfirmDialog.

Scientific charts always include units, time basis, missing-value behavior, and a table or text summary. Do not infer causality or create severity bands that are not present in source data.

## Related documents

[UX Specification](UX_SPECIFICATION.md), [Accessibility](ACCESSIBILITY.md), [NASA Integrations](../03-integrations/NASA_INTEGRATIONS.md).
