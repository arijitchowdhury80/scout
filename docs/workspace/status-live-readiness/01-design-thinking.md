# Status Live Readiness UI Notes

## Mental Model
The status page is a readiness dashboard for operators and beta testers. Users expect a plain current verdict, visible readiness states, and concrete next actions.

## IA
Hero: launch status headline. Primary: live readiness cards, missing configuration, operator actions. Secondary: static launch context and command references. Supporting: timestamps and endpoint labels.

## Interaction Flow
1. Open /status.
2. Page fetches /v1/billing/stripe/status.
3. Cards update to ready/blocked and lists show missing keys/actions.
Loading shows a neutral state. Fetch failure shows a readable error and keeps static fallback copy.

## Cognitive Load
Keep live readiness to one section with 3 cards plus two compact lists. Static launch context remains below.

## Emotional Journey
Concern -> clarity. The page should make blockers feel concrete and solvable, not mysterious.

## Pre-Mortem
Risk: exposing secrets. Mitigation: only render non-secret variable names and text returned by status endpoint. Risk: stale static copy. Mitigation: live fetch updates visible status.

## Aesthetic
Use existing Flux Scout website aesthetic and current status-grid cards. No new design system.

## UIUX Constraints
Responsive grid must collapse naturally on mobile; live cards use existing status tags; lists must wrap long environment variable names; status text is not conveyed by color alone.
