# ANNA Platform UI Architecture

## Overview

ANNA is a Django-based financial platform with two distinct domains: **Wakala** (agent-based money operations) and **Mchezo** (rotating savings groups). This document outlines the UI architecture designed to make backend permissions visible and actionable through the interface.

---

## 1. Role-Permission Matrix

### Wakala Domain

| Capability | Agent | Manager | Owner |
|------------|-------|---------|-------|
| View transactions | ✅ | ✅ | ✅ |
| Record new transaction | ✅ | ✅ | ✅ |
| Edit today's transactions | ❌ | ✅ | ✅ |
| Delete transactions | ❌ | ❌ | ✅ |
| Open financial day | ✅ | ✅ | ✅ |
| Close financial day | ❌ | ✅ | ✅ |
| View balancing reports | ✅ (own) | ✅ | ✅ (cross-wakala) |
| Resolve discrepancies | ❌ | ✅ | ✅ |
| Manage agents | ❌ | ❌ | ✅ |
| Wakala settings | ❌ | ❌ | ✅ |
| View analytics | Basic | Standard | Full |
| Export data | ❌ | Own | All |

### Mchezo Domain

| Capability | Viewer | Member | Treasurer | Admin |
|------------|--------|--------|-----------|-------|
| View group dashboard | ✅ | ✅ | ✅ | ✅ |
| View contribution history | ✅ | Own | ✅ | ✅ |
| Record contribution | ❌ | ❌ | ✅ | ✅ |
| Flag defaulter | ❌ | ❌ | ✅ | ✅ |
| Record payout | ❌ | ❌ | ✅ | ✅ |
| Manage members | ❌ | ❌ | ❌ | ✅ |
| Control payout order | ❌ | ❌ | ❌ | ✅ |
| Close/restart cycles | ❌ | ❌ | ❌ | ✅ |
| Group settings | ❌ | ❌ | ❌ | ✅ |
| Export reports | ❌ | ❌ | Own | ✅ |

---

## 2. UI Architecture Layers

### Layer 1: Base Template (`base.html`)
- Global navigation
- Theme toggle (light/dark)
- User profile indicator
- App switcher (Wakala ↔ Mchezo)

### Layer 2: Domain Templates
- `wakala/` - Wakala-specific layouts
- `mchezo/` - Mchezo-specific layouts

### Layer 3: Component Library
- Cards (stat, action, info)
- Forms (transaction, contribution)
- Tables (with inline actions)
- Alerts (success, error, warning)
- Modals (confirmations)

### Layer 4: Permission-Driven Components
Template tags that conditionally render based on user permissions:

```django
{% can_record_transaction for wakala as agent %}
  <button class="btn-primary">Record Transaction</button>
{% endcan %}

{% can_close_day for financial_day %}
  <button class="btn-danger">Close Day</button>
{% endcan %}
```

---

## 3. Navigation Strategy

### Global App Switcher
```
┌─────────────────────────────────────────────────────┐
│ ANNA                    [Wakala ▼] [Mchezo ▼] [Profile] │
├─────────────────────────────────────────────────────┤
│ Wakala: [Agent ▼]              Day: Open ▪          │
├─────────────────────────────────────────────────────┤
```

### Sidebar (Domain Context)
- Dashboard
- Transactions (if Agent+: add/edit)
- Balancing (if Manager+: close day)
- Reports (if Owner+: export)
- Settings (if Owner+: configure)

---

## 4. Dashboard Layouts

### Agent Dashboard
```
┌─────────────────────────────────────────────────────┐
│ Wakala: Tasha Shop    |    Day: Open (Today)       │
├─────────────────────────────────────────────────────┤
│  Today's Balance     |  Today's Transactions      │
│  TZS 150,000         │  12 transactions           │
├─────────────────────────────────────────────────────┤
│  [QUICK: + Deposit]  [QUICK: - Withdrawal]         │
├─────────────────────────────────────────────────────┤
│  Recent Transactions (last 5)                       │
│  TXN001 - Deposit - TZS 50,000 - John Doe          │
│  TXN002 - Withdrawal - TZS 20,000 - Jane Doe       │
└─────────────────────────────────────────────────────┘
```

### Manager Dashboard
```
┌─────────────────────────────────────────────────────┐
│ Wakala: Tasha Shop    |    Day: Open (Today)       │
├─────────────────────────────────────────────────────┤
│  Opening Balance     │  Computed Closing          │
│  TZS 100,000         │  TZS 230,000               │
├─────────────────────────────────────────────────────┤
│  Discrepancy: TZS 0   │  Status: BALANCED         │
├─────────────────────────────────────────────────────┤
│  [CLOSE DAY]  [DISCREPANCY]  [EDIT TXN]            │
├─────────────────────────────────────────────────────┤
│  All Today's Transactions                          │
│  [Edit] [View]                                     │
└─────────────────────────────────────────────────────┘
```

### Owner Dashboard
```
┌─────────────────────────────────────────────────────┐
│ Wakala: All Wakalas    |    Cross-Wakala View      │
├─────────────────────────────────────────────────────┤
│  Total Balance        │  Total Transactions        │
│  TZS 1,250,000        │  156 this month           │
├─────────────────────────────────────────────────────┤
│  [Profit Chart]       │  [Activity Heatmap]       │
├─────────────────────────────────────────────────────┤
│  All Wakalas Overview  |  Export Reports          │
│  [Tasha Shop: Open]   │  [Export All]            │
└─────────────────────────────────────────────────────┘
```

---

## 5. Form UX Patterns

### Transaction Entry (Agent+)
```yaml
Fields:
  - Transaction Type: [Deposit ▼]
  - Amount: [_________] TZS
  - Customer Name: [____________________]
  - Customer Phone: [____________]
  - Reference: [____________________]
  - Payment Method: [Cash ▼]
  - Notes: [____________________]

Validation:
  - Amount > 0
  - Required fields highlighted
  - Enter = Submit, Ctrl+Enter = Continue
```

### Day Closing (Manager+)
```yaml
Fields:
  - Closing Balance: [_________] TZS
  - Computed Balance: [_________] TZS (auto-calculated)
  - Note: [____________________]

Confirmation:
  "Close day with discrepancy of TZS 0?"
  [Cancel] [Confirm Close]
```

---

## 6. Security Patterns

### Frontend Permission Enforcement
1. **Template-level**: Never render disallowed buttons
2. **JavaScript-level**: Hide/disable actions for confirmation
3. **Backend-level**: Always validate permissions (already done)

### Irreversible Action Confirmation
```javascript
// Before closing day
if (closingBalance !== computedBalance) {
  showWarning(`Discrepancy detected: TZS ${diff}`);
}

// Final confirmation
confirmAction('Close Financial Day?', 
  'This action cannot be undone.',
  'Close Day'
);
```

---

## 7. Low-Bandwidth Optimizations

1. **Progressive Loading**:
   - Critical KPIs load immediately
   - Charts load after core content
   - Historical data on demand

2. **HTMX for Updates**:
   - Live balance updates
   - Transaction list without page reload
   - Status indicators

3. **Minimal JavaScript**:
   - Vanilla JS for interactions
   - Chart.js only on analytics pages
   - Bootstrap for responsive layout

---

## 8. File Structure

```
templates/
├── base.html                    # Global layout
├── accounts/
│   └── login.html
├── dashboard/
│   ├── home.html               # Main hub
│   ├── app_switcher.html       # App selection
│   ├── admin.html              # Superadmin
│   ├── wakala.html             # Wakala dashboard
│   ├── mchezo.html             # Mchezo dashboard
│   ├── no_access.html          # Permission denied
│   └── settings.html
├── wakala/
│   ├── _components.html       # Reusable widgets
│   ├── transactions.html       # Transaction list
│   ├── day_close.html          # Day closing form
│   └── reports.html
├── mchezo/
│   ├── _components.html
│   ├── contributions.html
│   ├── payouts.html
│   └── cycle_management.html
└── components/
    ├── cards.html              # KPI cards
    ├── alerts.html             # Notifications
    ├── modals.html             # Confirmations
    └── forms.html              # Form patterns

static/css/
├── variables.css               # Design tokens
├── components.css             # UI components
├── wakala.css                 # Wakala-specific
└── mchezo.css                 # Mchezo-specific

static/js/
├── permissions.js             # Permission helpers
├── charts.js                  # Chart.js configs
└── forms.js                   # Form interactions
```

---

## 9. Implementation Priority

### Phase 1: Core Foundation
- [ ] Permission template tags
- [ ] Updated base template with role indicator
- [ ] Wakala dashboard (Agent view)
- [ ] Mchezo dashboard (Member view)

### Phase 2: Role Expansion
- [ ] Manager capabilities (edit, close day)
- [ ] Owner capabilities (cross-wakala)
- [ ] Treasurer capabilities
- [ ] Admin capabilities

### Phase 3: Analytics & Export
- [ ] Chart.js integration
- [ ] Export functionality
- [ ] Advanced reports

### Phase 4: Polish
- [ ] Mobile optimization
- [ ] Accessibility review
- [ ] Performance tuning
