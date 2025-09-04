# User Interface Design Goals

## Overall UX Vision
A single-screen dashboard that displays five critical dental KPIs with absolute clarity. Zero navigation, zero complexity - open the browser, see your numbers, make decisions. The interface maintains Kam Dental's professional yet approachable tone while letting metrics speak directly to practice managers.

## Key Interaction Paradigms
- **Read-only display** - No interactive elements, buttons, or inputs in MVP
- **Automatic refresh** - Data updates 3-4 times daily without user action
- **Glance-able metrics** - All five KPIs visible simultaneously without scrolling
- **Clear visual hierarchy** - Most important metrics (Production, Collections) prominently positioned

## Core Screens and Views
- **Main Dashboard** - Single screen displaying all 5 KPIs in metric cards
- **Error State** - Simple "Data Unavailable" message if connection fails

## Accessibility: None
MVP focuses on functional delivery; accessibility enhancements deferred to Phase 2

## Branding
Apply Kam Dental brand colors to Streamlit components:
- **Primary Navy (#142D54)** for headers and metric labels
- **Teal Blue (#007E9E)** for positive metric indicators
- **Emergency Red (#BB0A0A)** for metrics below threshold
- **Roboto font family** for all text elements
- Clean, professional medical aesthetic maintaining brand's patient-centric, trustworthy tone

## Target Device and Platforms: Web Responsive
Desktop-first design optimized for practice office computers, with basic responsive layout for tablets. Mobile optimization not required for MVP.
