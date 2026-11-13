# Accessibility

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** WCAG 2.2 AA target  
**Purpose:** Specify the intended Accessibility requirements and implementation constraints.  
**Scope:** Covers the proposed Accessibility behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Requirements

- Semantic landmarks, one page H1, labelled inputs, explicit table headers, descriptive link text, and valid focus order.
- All functionality works with keyboard only; visible focus is never removed.
- Text and essential graphics meet WCAG 2.2 AA contrast; status is never color-only.
- Respect prefers-reduced-motion; disable nonessential parallax, pulsing, and animated star fields.
- Charts include an accessible name, summary, and tabular values; do not rely on SVG hover tooltip alone.
- Maps provide a synchronized keyboard-operable list/details and textual geometry summary.
- Dialogs trap focus, restore it on close, and announce error/confirmation states.
- Image alt uses source alt text where provided; decorative imagery gets empty alt.
- Model-generation updates use polite live regions without announcing every token.
- Responsive zoom to 200% without loss of content or controls.

## Verification

Run automated axe checks and keyboard/manual reviews on every major journey. Automated checks supplement a manual screen-reader and zoom pass at release. Record known limitations and remediation owner.

## Related documents

[UX Specification](UX_SPECIFICATION.md), [Testing Strategy](../09-quality-assurance/TESTING_STRATEGY.md), [Release Checklist](../09-quality-assurance/RELEASE_CHECKLIST.md).
