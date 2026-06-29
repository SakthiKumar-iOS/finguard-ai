# FinGuard AI — Multi-Agent Banking Assistant with PII Governance

## Subtitle

A local, privacy-first AI agent system that helps customers understand
transactions, detect unusual spending, explore banking products,
get eligibility guidance, and raise service requests —
with enterprise-grade security built in from the ground up.

## Track

Concierge Agents

---

## The Problem

Banking customers increasingly expect intelligent, conversational
assistance — but traditional AI assistants create serious risks
in financial services:

- Customer PII exposure through AI responses
- Prompt injection attacks that manipulate AI behaviour
- Jailbreak attempts that bypass safety controls
- No audit trail for AI-assisted interactions
- Data leaving secure environments via cloud APIs

As someone with 10+ years building enterprise iOS applications
in the banking and fintech industry, I have seen firsthand how
difficult it is to introduce AI capabilities while maintaining
the strict compliance and governance standards that financial
services demand.

## Why Agents?

A single LLM cannot safely handle the full range of banking
interactions. Different tasks require different controls,
different data sources, and different compliance rules.

A multi-agent architecture solves this by:
- Isolating security concerns to a dedicated PII Guardian
- Giving each capability its own specialist agent
- Ensuring no agent ever receives raw, unscreened input
- Creating a clear, auditable chain of responsibility

## Solution — FinGuard AI

FinGuard AI is a local, privacy-first multi-agent banking
assistant built with Antigravity and FastMCP, running entirely
on macOS with no data ever leaving the device.

It handles five core customer needs:
1. Transaction history and unusual spending detection
2. Banking product information and comparison
3. Loan and card eligibility guidance
4. Service requests — disputes, freezes, complaints
5. Session audit log and compliance summary

## Architecture

Every input passes through a two-layer security pipeline
before reaching any specialist agent:

**Layer 1 — Prompt Guard:** 100+ keyword patterns detect and block
prompt injection, jailbreak attempts, financial fraud language,
social engineering, and system probing attempts across
6 named threat categories.

**Layer 2 — PII Guardian:** Microsoft Presidio detects and redacts
12 entity types including credit cards, account numbers,
BSB numbers, email addresses, phone numbers, and OTP codes.
Only sanitised text reaches the Orchestrator.

The Orchestrator uses deterministic keyword matching — not an
LLM call — to route intent to the correct specialist agent.
This keeps routing fast, predictable, and token-efficient.

The MCP Server acts as a local tool hub, giving agents clean,
validated access to mock transaction data, product knowledge,
eligibility rules, and the audit log — all from the local
macOS filesystem.

## Security and Governance

Security is not an afterthought in FinGuard AI — it is the
first thing every input encounters:

- PII is redacted before any agent sees the input
- 100+ injection and jailbreak keywords are blocked at the gate
- All audit log entries are sanitised — no raw input is ever written
- All processing is local — no cloud API receives customer data
- Input is hard-limited to 2000 characters at every layer
- Rotating log files prevent unbounded disk usage
- Every exception is caught and returns a safe message

## Capstone Concepts Applied

**Multi-Agent System:** Six agents with clear single responsibilities,
orchestrated via Antigravity. Each agent is independently testable
and replaceable.

**MCP Server:** FastMCP provides a local tool hub that decouples
agents from data sources. Agents call named tools — they never
access files directly.

**Security Features:** PII Guardian, Prompt Guard, 100+ keyword
blocklist, sanitised logging, and local-only enforcement form
a layered security architecture.

**Antigravity:** All agents, tools, and security components were
built and iterated using Antigravity as the primary development
environment.

**Deployability:** A single setup.sh command installs all
dependencies, downloads the spaCy model, and creates the
.env file — ready to run on any macOS Apple Silicon machine.

## The Build

Built on Python 3.13.7 for macOS Apple M1 using:
- Antigravity for agent development
- Google Gemini 2.0 Flash for LLM responses
- Microsoft Presidio for PII detection
- FastMCP for the local MCP server
- Typer and Rich for the terminal CLI
- pytest for a 63-test automated test suite

## What I Learned

Building FinGuard AI reinforced that security in AI systems
is not a single feature — it is a pipeline. Every layer must
assume the previous layer could fail. The PII Guardian does
not trust the user. The Orchestrator does not trust raw input.
The specialist agents do not trust unscreened text.

This defence-in-depth approach mirrors the security architecture
I have applied throughout my career building enterprise banking
applications — and it translates naturally to multi-agent AI systems.

## What Is Next

- Connect to a real iOS banking interface via REST API
- Add biometric authentication before session start
- Extend PII detection with Australian-specific entity types
- Add real-time transaction streaming
- Integrate with open banking APIs under PSD2/CDR frameworks
