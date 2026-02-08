# ANNA Platform UI Implementation Recommendations

## Overview

This document provides recommendations for incrementally refactoring the ANNA UI without breaking existing functionality. The approach prioritizes stability while gradually introducing role-aware, permission-driven interfaces.

---

## Phase 1: Foundation (Week 1)

### 1.1 Add Permission Template Tags

The [`core/templatetags/permissions.py`](core/templatetags/permissions.py) file provides template tags for conditional rendering based on user roles:

```django
{% load permissions %}

{% can_record_transaction user wakala as can_record %}
{% if can_record %}
  <button>Record Transaction</button>
{% endif %}
```

**Files to update:**
- [`core/templatetags/__init__.py`](core/templatetags/__init__.py)
- [`core/templatetags/permissions.py`](core/templatetags/permissions.py)

### 1.2 Deploy New CSS System

The [`static/css/`](static/css/) directory contains the new design system:

- [`variables.css`](static/css/variables.css) - Design tokens and CSS variables
- [`anna.css`](static/css/anna.css) - Core styling components

**Include in base.html:**
```html
<link href="{% static 'css/variables.css' %}" rel="stylesheet">
<link href="{% static 'css/anna.css' %}" rel="stylesheet">
```

---

## Phase 2: Template Updates (Week 2)

### 2.1 Update Base Template

The [`templates/base.html`](templates/base.html) now includes:
- Role indicator badge in navbar
- App switcher for Wakala/Mchezo
- Improved alert styling
- Theme toggle

### 2.2 Create Component Templates

Reusable components in [`templates/components/`](templates/components/):
- `role_badge.html` - Role display badges
- `kpi_card.html` - KPI metric cards
- `day_status.html` - Financial day status bar
- `permission_denied.html` - Permission messages

### 2.3 Create Domain Dashboards

- [`templates/dashboard/wakala.html`](templates/dashboard/wakala.html) - Wakala dashboard
- [`templates/dashboard/mchezo.html`](templates/dashboard/mchezo.html) - Mchezo dashboard

---

## Phase 3: JavaScript & Analytics (Week 3)

### 3.1 Core JavaScript

[`static/js/anna.js`](static/js/anna.js) provides:
- Form confirmation helpers
- Keyboard shortcuts
- Balance polling (for HTMX)
- Amount validation

### 3.2 Chart Configurations

[`static/js/charts.js`](static/js/charts.js) includes:
- Balance trend charts
- Transaction bar charts
- Contribution doughnut charts
- Activity heatmaps

**Usage:**
```html
<canvas id="balanceChart"></canvas>
<script>
  const ctx = document.getElementById('balanceChart');
  annaCharts.createBalanceChart(ctx, {
    labels: ['Mon', 'Tue', 'Wed'],
    values: [100000, 150000, 120000]
  });
</script>
```

---

## Phase 4: HTMX Integration (Week 4)

### 4.1 Recommended HTMX Patterns

For low-bandwidth optimization, use HTMX for:

1. **Live balance updates:**
```html
<div hx-get="/api/balance/" hx-trigger="every 5s">
  <!-- Balance updates here -->
</div>
```

2. **Transaction list updates:**
```html
<table hx-get="/api/transactions/" hx-trigger="load">
  <!-- Transactions load here -->
</table>
```

3. **Inline editing:**
```html
<td hx-get="/api/txn/1/edit/" hx-trigger="click" class="cursor-pointer">
  Click to edit
</td>
```

### 4.2 CSRF Protection

Ensure HTMX requests include CSRF tokens:
```html
<script>
  document.body.addEventListener('htmx:configRequest', function(evt) {
    evt.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
  });
</script>
```

---

## Security Checklist

### Permission Enforcement

1. **Template-level (UI only):**
   - Use `{% if can_record_transaction %}` to hide buttons
   - Never rely solely on this for security

2. **View-level (required):**
   - Use `@user_passes_test` decorators
   - Use permission mixins
   - Always validate in forms

3. **Model-level (defense in depth):**
   - Add `clean()` methods for validation
   - Use Django's permission system

### Irreversible Actions

Always require confirmation for:
- Day closing
- Transaction deletion
- Cycle completion
- Member removal

Use `anna.showConfirmModal()`:
```javascript
anna.showConfirmModal({
  title: 'Close Financial Day?',
  message: 'This will finalize all transactions for today.',
  confirmClass: 'anna-btn-danger',
  onConfirm: function() {
    window.location.href = '{% url "wakala:close_day" wakala_id=wakala.id %}';
  }
});
```

---

## Mobile Optimization

### Responsive Design

The CSS system uses mobile-first patterns:
- Grid layouts with `grid-template-columns: 1fr` on mobile
- Touch-friendly button sizes (44px minimum)
- Collapsible navigation

### Low-Bandwidth Optimizations

1. **Progressive loading:**
   - Critical KPIs load first
   - Charts load asynchronously
   - Historical data on demand

2. **Minimal JavaScript:**
   - Vanilla JS (no frameworks)
   - Chart.js only on analytics pages
   - Bootstrap for responsive layout

3. **Caching:**
   - Cache static assets
   - Use Django's template caching for expensive queries

---

## Testing Recommendations

### Visual Testing

1. **Cross-browser testing:**
   - Chrome, Firefox, Safari, Edge
   - Mobile browsers (iOS Safari, Chrome Mobile)

2. **Responsive testing:**
   - Desktop (1920px, 1440px, 1280px)
   - Tablet (768px)
   - Mobile (375px, 414px)

### Functional Testing

1. **Permission testing:**
   - Test each role's capabilities
   - Verify unauthorized actions are blocked
   - Check role badges display correctly

2. **Form testing:**
   - Keyboard navigation
   - Validation messages
   - Error states

---

## Rollout Plan

### 1. Staged Rollout

1. **Internal testing:** Deploy to staging environment
2. **Pilot group:** Small set of users
3. **Gradual rollout:** 25% → 50% → 100%
4. **Rollback plan:** If issues arise, revert to previous templates

### 2. Backward Compatibility

The changes are additive:
- New CSS classes don't override Bootstrap
- Template tags don't change existing behavior
- JavaScript is opt-in

### 3. Fallback

If JavaScript fails:
- Forms still submit via POST
- Charts show as static placeholders
- Navigation works without enhancements

---

## File Reference

| File | Purpose |
|------|---------|
| [`core/templatetags/permissions.py`](core/templatetags/permissions.py) | Permission template tags |
| [`static/css/variables.css`](static/css/variables.css) | Design tokens |
| [`static/css/anna.css`](static/css/anna.css) | Core styling |
| [`static/js/anna.js`](static/js/anna.js) | Interactive functionality |
| [`static/js/charts.js`](static/js/charts.js) | Chart configurations |
| [`templates/base.html`](templates/base.html) | Global layout |
| [`templates/components/`](templates/components/) | Reusable components |
| [`templates/dashboard/wakala.html`](templates/dashboard/wakala.html) | Wakala dashboard |
| [`templates/dashboard/mchezo.html`](templates/dashboard/mchezo.html) | Mchezo dashboard |
| [`docs/UI_ARCHITECTURE.md`](docs/UI_ARCHITECTURE.md) | Architecture documentation |
