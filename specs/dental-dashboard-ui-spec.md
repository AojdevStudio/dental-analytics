---
title: "Dental Analytics Dashboard UI Specification"
description: "Minimal UI design specification for KamDental's 5-KPI dashboard using Streamlit framework."
category: "Technical Documentation"
subcategory: "UI Specifications"
product_line: "Dental Analytics Dashboard"
audience: "Development Team"
status: "Final"
author: "AOJDevStudio"
created_date: "2025-09-04"
last_updated: "2025-09-04"
tags:
  - ui-specification
  - streamlit
  - dashboard
  - dental-analytics
  - mvp
---

# Dental Analytics Dashboard UI Specification

## Executive Summary

A radically simple, single-screen dashboard displaying 5 critical dental KPIs using Streamlit's native components. Zero navigation, zero complexity - open the browser, see your numbers instantly.

## Visual Layout Architecture

### Screen Structure (1920x1080 Desktop)

```
┌─────────────────────────────────────────────────────────────┐
│                    KAM DENTAL ANALYTICS                     │
│                     [Navy #142D54]                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ DAILY PRODUCTION │  │ COLLECTION RATE  │                 │
│  │    $28,450       │  │      92.3%       │                 │
│  │    ▲ Good        │  │    ▲ Excellent   │                 │
│  └──────────────────┘  └──────────────────┘                 │
│                                                             │
│  ┌─────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ NEW PATIENTS│  │TREATMENT ACCEPT. │  │HYGIENE REAPPT. │  │
│  │     12      │  │     78.5%        │  │    94.2%       │  │
│  │   ▲ Target  │  │   ▼ Below Goal   │  │   ▲ Good       │  │
│  └─────────────┘  └──────────────────┘  └────────────────┘  │
│                                                             │
│                   Last Updated: 2:45 PM                     │
└─────────────────────────────────────────────────────────────┘
```

## Component Specifications

### 1. Header Section
```python
st.title("KAM DENTAL ANALYTICS")
# Styling: Navy (#142D54), Roboto Condensed Bold, 36px equivalent
# Centered alignment
# 20px padding top/bottom
```

### 2. Primary Metrics Row (Most Critical)
**Layout:** 2 equal columns with 40px gap

#### Daily Production Total
- **Component:** `st.metric()`
- **Label:** "DAILY PRODUCTION" (Navy #142D54)
- **Value:** "$XX,XXX" format with thousands separator
- **Delta:** Show vs. yesterday (optional for Phase 2)
- **Color Logic:**
  - Teal (#007E9E) when ≥ $25,000
  - Default when $15,000-24,999
  - Red (#BB0A0A) when < $15,000

#### Collection Rate
- **Component:** `st.metric()`
- **Label:** "COLLECTION RATE" (Navy #142D54)
- **Value:** "XX.X%" format (one decimal)
- **Delta:** Show vs. last week avg (optional for Phase 2)
- **Color Logic:**
  - Teal (#007E9E) when ≥ 95%
  - Default when 85-94.9%
  - Red (#BB0A0A) when < 85%

### 3. Secondary Metrics Row
**Layout:** 3 equal columns with 30px gap

#### New Patient Count
- **Component:** `st.metric()`
- **Label:** "NEW PATIENTS" (Navy #142D54)
- **Value:** Integer, no decimals
- **Color Logic:**
  - Teal (#007E9E) when ≥ 10
  - Default when 5-9
  - Red (#BB0A0A) when < 5

#### Treatment Acceptance Rate
- **Component:** `st.metric()`
- **Label:** "TREATMENT ACCEPTANCE" (Navy #142D54)
- **Value:** "XX.X%" format
- **Color Logic:**
  - Teal (#007E9E) when ≥ 80%
  - Default when 65-79.9%
  - Red (#BB0A0A) when < 65%

#### Hygiene Reappointment Rate
- **Component:** `st.metric()`
- **Label:** "HYGIENE REAPPOINTMENT" (Navy #142D54)
- **Value:** "XX.X%" format
- **Color Logic:**
  - Teal (#007E9E) when ≥ 90%
  - Default when 80-89.9%
  - Red (#BB0A0A) when < 80%

### 4. Footer Section
- **Component:** `st.caption()`
- **Text:** "Last Updated: [TIME]"
- **Style:** Dark Gray (#565554), Roboto Regular, 12px equivalent
- **Position:** Centered

## Streamlit Implementation Pattern

### Code Structure (Under 100 Lines)
```python
import streamlit as st
import pandas as pd
from backend.metrics import get_all_kpis

# Page configuration
st.set_page_config(
    page_title="Kam Dental Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom theme configuration (in .streamlit/config.toml)
# [theme]
# primaryColor="#007E9E"
# backgroundColor="#FFFFFF"
# secondaryBackgroundColor="#F0F2F6"
# textColor="#142D54"
# font="sans serif"  # Will use Roboto if available

# Fetch KPI data
kpis = get_all_kpis()

# Header
st.markdown(
    "<h1 style='text-align: center; color: #142D54;'>KAM DENTAL ANALYTICS</h1>",
    unsafe_allow_html=True
)

# Primary metrics row
col1, col2 = st.columns(2)

with col1:
    production = kpis.get('production_total', 'N/A')
    if production != 'N/A':
        st.metric(
            label="DAILY PRODUCTION",
            value=f"${production:,.0f}",
            delta_color="normal"
        )
    else:
        st.metric(label="DAILY PRODUCTION", value="Data Unavailable")

with col2:
    collection_rate = kpis.get('collection_rate', 'N/A')
    if collection_rate != 'N/A':
        st.metric(
            label="COLLECTION RATE",
            value=f"{collection_rate:.1f}%",
            delta_color="normal"
        )
    else:
        st.metric(label="COLLECTION RATE", value="Data Unavailable")

# Secondary metrics row
col3, col4, col5 = st.columns(3)

with col3:
    new_patients = kpis.get('new_patients', 'N/A')
    if new_patients != 'N/A':
        st.metric(
            label="NEW PATIENTS",
            value=str(new_patients),
            delta_color="normal"
        )
    else:
        st.metric(label="NEW PATIENTS", value="Data Unavailable")

with col4:
    treatment_accept = kpis.get('case_acceptance', 'N/A')
    if treatment_accept != 'N/A':
        st.metric(
            label="TREATMENT ACCEPTANCE",
            value=f"{treatment_accept:.1f}%",
            delta_color="normal"
        )
    else:
        st.metric(label="TREATMENT ACCEPTANCE", value="Data Unavailable")

with col5:
    hygiene_reappt = kpis.get('hygiene_reappointment', 'N/A')
    if hygiene_reappt != 'N/A':
        st.metric(
            label="HYGIENE REAPPOINTMENT",
            value=f"{hygiene_reappt:.1f}%",
            delta_color="normal"
        )
    else:
        st.metric(label="HYGIENE REAPPOINTMENT", value="Data Unavailable")

# Footer
from datetime import datetime
st.caption(f"Last Updated: {datetime.now().strftime('%I:%M %p')}")
```

## Error States

### Data Unavailable State
When any KPI fails to load:
- Display text: "Data Unavailable"
- Color: Dark Gray (#565554)
- No delta indicator
- Maintains layout structure

### Complete Failure State
When Google Sheets connection fails entirely:
- Single centered message: "Unable to connect to data source"
- Subtitle: "Please check your connection and refresh"
- Maintain Kam Dental branding

## Visual Hierarchy Principles

1. **Size = Importance**
   - Primary metrics (Production, Collection): 2x larger
   - Secondary metrics: Standard size
   - Footer: Smallest

2. **Position = Priority**
   - Top row: Most critical financial metrics
   - Bottom row: Supporting operational metrics
   - Footer: Metadata

3. **Color = Status**
   - Teal Blue (#007E9E): Good/Excellent performance
   - Navy (#142D54): Labels and headers
   - Red (#BB0A0A): Below threshold (sparingly)
   - Gray (#565554): Unavailable data

## Responsive Behavior

### Desktop (1920x1080) - PRIMARY
- Full layout as specified
- All metrics on single screen
- No scrolling required

### Tablet (1024x768) - BASIC SUPPORT
- Stack to single column
- Maintain metric size
- Vertical scrolling acceptable

### Mobile - NOT SUPPORTED
- Redirect to message: "Please view on desktop"

## Performance Requirements

### Load Time Targets
- Initial render: < 500ms
- Data fetch: < 2s
- Complete display: < 3s total

### Optimization Strategies
- Cache KPI calculations for 5 minutes
- Preload Streamlit components
- Minimize custom styling
- Single API call for all metrics

## Accessibility Considerations (Phase 2)

### MVP Deferrals
- Screen reader support: Not required
- Keyboard navigation: Not required
- High contrast mode: Not required

### Built-in Streamlit Accessibility
- Semantic HTML structure
- Standard focus indicators
- Native browser zoom support

## Implementation Notes

### File Structure
```
frontend/
├── app.py              # Main Streamlit application (< 100 lines)
├── .streamlit/
│   └── config.toml     # Theme configuration
```

### Streamlit Configuration (.streamlit/config.toml)
```toml
[theme]
primaryColor = "#007E9E"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#142D54"
font = "sans serif"

[server]
headless = true
port = 8501

[browser]
gatherUsageStats = false
```

### Key Streamlit APIs Used
- `st.set_page_config()` - Page setup
- `st.columns()` - Horizontal layout
- `st.metric()` - KPI display
- `st.markdown()` - Custom styled header
- `st.caption()` - Footer text

## Success Metrics

### User Experience
- Zero clicks to see all metrics
- 2-second comprehension time
- No training required

### Technical
- Under 200 total lines of code
- 3-second max load time
- Zero external dependencies beyond Streamlit

## Future Enhancements (Post-MVP)

1. **Visual Polish**
   - Custom CSS for exact brand colors
   - Animated metric transitions
   - Trend sparklines

2. **Interactivity**
   - Date range selector
   - Drill-down to provider level
   - Export functionality

3. **Mobile Support**
   - Responsive grid system
   - Touch-optimized layout
   - Progressive web app

## Conclusion

This specification delivers a dashboard that achieves its core purpose: instant visibility into 5 critical KPIs. By embracing radical simplicity and leveraging Streamlit's native components, we create a solution that practice managers can use immediately without training, while staying well under the 200-line code constraint.

The design philosophy: **The best UI is invisible - let the numbers tell the story.**
