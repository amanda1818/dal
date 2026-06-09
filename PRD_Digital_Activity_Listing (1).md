# Product Requirements Document — Digital Activity Listing

**Version:** 1.1
**Status:** For build
**Changelog v1.1:** Added (a) meeting capture via calendar + call/presence logs and **idle-gap attribution** for ad-hoc briefings (Modules A & B); (b) **study-window = full-cycle** rule for cyclical functions like accounting month-end (Module F); (c) **load-profile** output and peak-vs-baseline manload for cyclical roles (Module D).
**Owner:** [you]
**Purpose of this document:** A complete, self-contained specification. Anyone — a developer, an AI coding agent (Cursor, Claude Code, etc.), or you — should be able to build the tool *exactly* as described here without needing the original conversation. Every module states its **purpose**, **behaviour**, **data**, and **acceptance criteria**.

---

## 1. Product overview

### 1.1 What it is
A study tool that replaces the manual "Activity Listing" consulting method (process mapping + interviews + observation) with a hybrid of **measured activity data** and **in-the-moment self-reporting**, then computes **Value-Added / Non-Value-Added (VA/NVA)** breakdowns and a **manload** result (required vs. actual headcount per role).

### 1.2 The core principle (do not violate)
The tool **does not** try to replace consultant judgment with surveillance. It does three things:
1. **Measures** the easy-to-measure ("what app, how long") passively.
2. **Samples** the hard-to-measure ("is this value-added / rework / waiting") via short, in-the-moment prompts.
3. **Computes** the analytics, leaving the consultant to confirm edge cases and set standards.

It captures **metadata only** — never keystrokes, never screenshots, never message/file content.

### 1.3 Primary goals (success = all four)
- G1: Cut consultant interview + observation effort by **≥ 70%** per engagement.
- G2: Produce a defensible required-vs-actual headcount number per role, backed by data.
- G3: Surface rework, waiting, and over-processing that interviews miss.
- G4: Remain legally and culturally deployable (consented, time-boxed, aggregate, deletable).

### 1.4 Non-goals
- Not a permanent/continuous employee-surveillance product.
- Not an individual performance-scoring or disciplinary tool.
- Not a keystroke logger or screen recorder.

---

## 2. Glossary

| Term | Definition |
|---|---|
| **Activity** | A unit of work from the catalog (e.g. "Prepare invoice", "Reconcile ledger"). |
| **Activity catalog** | The master list of activities per role family, each pre-tagged VA / NVA-necessary / NVA-waste. |
| **VA** | Value-Added: work the customer would pay for; transforms the product/service. |
| **NVA-necessary** | Non-value-added but currently required (e.g. compliance checks). |
| **NVA-waste** | Non-value-added and removable (rework, waiting, over-processing, redundant approvals). |
| **ESM** | Experience Sampling Method: short in-the-moment prompts asking what the person is doing now. |
| **Time spent** | Measured/reported actual time on an activity. |
| **Standard time** | The time an activity *should* take (the benchmark). |
| **Manload** | Required headcount = total standard work time ÷ available productive time per person. |
| **Study** | A single, time-boxed engagement at a client (e.g. 2–4 weeks, defined roles). |
| **Participant** | An employee enrolled in a study. |
| **Available productive time** | Net working minutes per person per period after breaks/allowances. |

---

## 3. Users / personas

1. **Consultant / Analyst (primary)** — configures studies, reviews classification flags, sets standard times, reads the manload result, exports the report. Power user. Uses the dashboard.
2. **Client Admin (secondary)** — at the client; approves data scope, grants telemetry access or pushes the agent via their IT, sees deployment status only (not raw individual data).
3. **Participant (tertiary)** — the client's employee. Sees their own enrolment status, consent notice, and answers ESM prompts. Can view *their own* data; cannot see others.
4. **System Admin (you)** — manages tenants, security, retention/deletion jobs.

---

## 4. System architecture

Four logical layers + supporting services.

```
[ Participant devices / cloud ]                 [ Consultant ]
   |  passive telemetry  |  ESM responses           |
   v                     v                          v
+----------------------------------------------+   +----------------------+
| Ingestion API (FastAPI)                      |   | Dashboard (Streamlit)|
|  - /events (passive)                         |   |  - flag review        |
|  - /esm (sampling responses)                 |   |  - standard-time set  |
|  - /connectors (M365 / Google pull jobs)     |   |  - manload + charts   |
+----------------------------------------------+   |  - report export      |
   |                                               +----------------------+
   v                                                        ^
+----------------------------------------------+            |
| PostgreSQL  (events, esm, catalog, results)  |------------+
+----------------------------------------------+
   |
   v
+----------------------------------------------+
| Classification engine (rules + Claude API)   |
| Manload engine (pandas)                       |
| Retention/deletion scheduler                  |
+----------------------------------------------+
```

**Data sources (pick per study):**
- **Telemetry (no install):** Microsoft Graph API + Google Workspace API — calendar, email/meeting metadata, file activity, Teams/Meet presence.
- **Desktop agent (optional):** local process that logs active app/window title, active-vs-idle, file open/save events. Metadata only.
- **ESM app:** lightweight web/PWA or system-tray prompt that fires sampling questions.

---

## 5. Data model (PostgreSQL)

Implement these tables. Types are indicative.

### 5.1 `organizations`
| field | type | notes |
|---|---|---|
| id | uuid PK | |
| name | text | client name |
| created_at | timestamptz | |

### 5.2 `studies`
| field | type | notes |
|---|---|---|
| id | uuid PK | |
| org_id | uuid FK | |
| name | text | |
| start_date | date | |
| end_date | date | study window |
| status | enum | `draft, consent, active, analysis, closed, deleted` |
| data_scope | jsonb | which sources enabled, retention days |
| created_at | timestamptz | |

### 5.3 `roles`
| field | type | notes |
|---|---|---|
| id | uuid PK | |
| study_id | uuid FK | |
| name | text | e.g. "Manager", "Staff A" |
| role_family | text | groups roles that do similar work |
| current_headcount | int | the denominator |
| available_minutes_per_day | int | net productive minutes (default 420) |
| cyclical | bool | true if load peaks on a cycle (e.g. month-end); triggers load-profile output |

### 5.4 `participants`
| field | type | notes |
|---|---|---|
| id | uuid PK | |
| study_id | uuid FK | |
| role_id | uuid FK | |
| pseudonym | text | **no real names stored**; map kept by client only |
| consent_status | enum | `pending, given, withdrawn` |
| esm_optin | bool | |

### 5.5 `activity_catalog`
| field | type | notes |
|---|---|---|
| id | uuid PK | |
| role_family | text | |
| activity_name | text | |
| default_classification | enum | `VA, NVA_necessary, NVA_waste` |
| keywords | text[] | app/window keywords that map to this activity |
| is_rework_category | bool | true for rework-type activities |

### 5.6 `activity_events` (passive)
| field | type | notes |
|---|---|---|
| id | bigserial PK | |
| participant_id | uuid FK | |
| source | enum | `agent, graph, gworkspace` |
| start_ts | timestamptz | |
| end_ts | timestamptz | |
| app_name | text | e.g. "Excel", "Outlook" |
| window_title_hash | text | hashed/redacted title or category, **not raw content** |
| category | text | derived (e.g. "email", "spreadsheet", "browser-internal") |
| is_active | bool | active vs idle |
| signal_flags | jsonb | e.g. `{file_reedit:true, switch_count:N}` |

### 5.7 `esm_responses` (active sampling)
| field | type | notes |
|---|---|---|
| id | bigserial PK | |
| participant_id | uuid FK | |
| prompt_ts | timestamptz | when fired |
| response_ts | timestamptz | when answered (null if ignored) |
| activity_id | uuid FK | chosen activity |
| is_rework | bool | |
| is_waiting | bool | waiting on someone/something |
| is_new_request | bool | |
| free_note | text | optional, short |

### 5.8 `classified_blocks` (engine output)
| field | type | notes |
|---|---|---|
| id | bigserial PK | |
| participant_id | uuid FK | |
| activity_id | uuid FK | |
| start_ts / end_ts | timestamptz | |
| minutes | numeric | |
| classification | enum | `VA, NVA_necessary, NVA_waste` |
| confidence | numeric | 0–1 |
| needs_review | bool | true if low confidence or divergence |
| divergence_flag | text | e.g. "esm_vs_passive_mismatch" |
| consultant_override | enum | nullable; set during review |

### 5.9 `volumes` (output anchoring)
| field | type | notes |
|---|---|---|
| id | uuid PK | |
| study_id | uuid FK | |
| activity_id | uuid FK | |
| period | date | |
| count | int | units produced (tickets, invoices…) |

### 5.10 `standard_times`
| field | type | notes |
|---|---|---|
| id | uuid PK | |
| study_id | uuid FK | |
| activity_id | uuid FK | |
| std_minutes_per_unit | numeric | the benchmark |
| method | enum | `percentile, engineered, waste_stripped` |
| set_by | text | consultant id |

### 5.11 `manload_results`
| field | type | notes |
|---|---|---|
| id | uuid PK | |
| study_id | uuid FK | |
| role_id | uuid FK | |
| required_headcount | numeric | |
| actual_headcount | int | |
| gap | numeric | |
| va_pct / nva_nec_pct / nva_waste_pct | numeric | |

---

## 6. Functional requirements by module

### MODULE A — Passive capture
**Purpose:** measure time spent per app/activity without self-report.

**A1. Telemetry connectors (no install).**
- A1.1 OAuth connect to Microsoft Graph (scopes: Calendars.Read, Mail.Read metadata, Files.Read activity, Reports). Use `msal`.
- A1.2 OAuth connect to Google Workspace (Calendar, Gmail metadata, Drive activity, Reports API). Use `google-api-python-client`.
- A1.3 Scheduled pull job (every N hours) writes to `activity_events` with `source = graph|gworkspace`.
- A1.4 Store **metadata only**: event durations, counts, categories. Never message bodies, never attachment content.
- A1.5 **Meeting capture.** Pull *scheduled* meetings from the calendar (start, end, attendee count, title-category) and *actual* attendance from video-call logs (Teams via Graph, Zoom/Meet via their APIs) so real join/leave times are recorded, not just the booking. Write as `activity_events` with `category = "meeting"`. This captures formal meetings automatically with no self-report.

**A2. Optional desktop agent.**
- A2.1 Cross-platform Python process (`psutil`, `pywin32` on Windows; `pyobjc` on macOS), packaged with PyInstaller, code-signed.
- A2.2 Logs: active window app name, window-title → hashed/categorised, active-vs-idle (idle threshold configurable, default 3 min), file open/save events.
- A2.3 Buffers locally; uploads to `/events` over TLS on interval; retries on failure.
- A2.4 Visible tray indicator that capture is on; one-click pause; auto-stop at study `end_date`.
- A2.5 Emits `signal_flags`: `file_reedit` (same file reopened/edited after close), `switch_count` (app switches per interval).

**A3. Acceptance criteria.**
- Active time per participant per day reconstructable to the minute.
- No raw window title, message body, or file content ever persisted (audit a sample to confirm).
- Agent uninstalls/stops automatically at study end.

---

### MODULE B — Active sampling (ESM)
**Purpose:** capture the judgmental layer (activity identity, rework, waiting) in the moment.

**B1. Prompt scheduling.**
- B1.1 Fire **3–6 prompts/day** at **randomised** times within working hours (randomisation prevents pre-staging answers). Configurable per study.
- B1.2 Non-blocking; dismissible; logs ignored prompts (response_ts null).

**B2. Prompt content (≤ 5 seconds to answer).**
- B2.1 Q1 (required): "What are you working on right now?" → pick from the participant's role-family activity list (searchable, recent-first).
- B2.2 Q2 (one tap each, optional): "Is this… [Redoing/fixing earlier work] [Waiting on someone] [A new request]".
- B2.3 Optional free note (short).

**B3. End-of-block confirmation (optional).**
- B3.1 Once/day, show the auto-classified timeline; participant can correct activity/classification of blocks.
- B3.2 Every correction is stored as an event (old → new, timestamp) for **correction-pattern analysis** (see Module G).

**B4. Idle-gap attribution (captures ad-hoc meetings, briefings, calls — off-screen work).**
- B4.1 When the passive layer detects inactivity (machine locked/idle) above a threshold (default 10 min) that is **not** matched by a scheduled calendar event, queue a single return-prompt: *"You were away HH:MM–HH:MM — was that: [Meeting] [Briefing] [Break] [Phone call] [Other]?"* One tap.
- B4.2 The attributed gap is written as a `classified_block` with the chosen category, so off-screen time becomes classified time without an interview.
- B4.3 Gaps below the idle threshold are merged into the adjacent activity (acceptable noise at aggregate level).

**B5. Acceptance criteria.**
- Prompt timing is verifiably randomised, not fixed.
- Response capture < 5 seconds median.
- All corrections logged with before/after, not just final state.

---

### MODULE C — Classification engine
**Purpose:** map raw signals + ESM into activities and VA/NVA.

**C1. Rule pass (deterministic, first).**
- C1.1 Match `app_name` + `category` + `window_title_hash` keywords against `activity_catalog.keywords`.
- C1.2 If an ESM response covers a time block, ESM activity **overrides** the rule guess for that block.

**C2. AI pass (for the remainder).**
- C2.1 For unmatched/ambiguous blocks, call the Anthropic Claude API with: the block's metadata, the candidate activity list for that role family, and any nearby ESM context. Ask it to return JSON: `{activity_id, classification, confidence, reason}`.
- C2.2 System prompt must instruct: return JSON only, choose from the provided list only, never invent activities, output confidence 0–1.
- C2.3 Parse safely (strip code fences); on parse failure, mark `needs_review = true`.

**C3. Confidence & review routing.**
- C3.1 Block flagged `needs_review = true` if confidence < threshold (default 0.6) OR divergence detected (Module G).
- C3.2 As studies accumulate labelled data, optionally train a `scikit-learn` classifier to reduce API calls.

**C4. Acceptance criteria.**
- 100% of time blocks receive an activity + classification + confidence.
- ESM-covered blocks always reflect the ESM answer.
- Low-confidence/divergent blocks surface in the review queue.

---

### MODULE D — Manload analytics & dashboard
**Purpose:** produce the answer the consultant sells.

**D1. Standard-time setting (consultant UI).** For each activity, set `std_minutes_per_unit` by one of:
- **Percentile method:** system suggests the 25th-percentile (efficient) observed time across participants; consultant accepts/edits.
- **Engineered method:** consultant enters a target cycle time.
- **Waste-stripped method:** system computes (VA time + NVA-necessary time) excluding rework/waiting; consultant accepts.

**D2. Manload calculation (compute & store `manload_results`).**
```
For each role:
  required_minutes = Σ over activities ( std_minutes_per_unit × volume_in_period )
  required_headcount = required_minutes ÷ (available_minutes_per_day × working_days)
  gap = required_headcount − current_headcount
  va_pct = VA_minutes ÷ total_minutes   (and likewise NVA_necessary, NVA_waste)
```

**D3. Dashboard views (Streamlit).**
- D3.1 Study overview: VA / NVA-necessary / NVA-waste split per role; required vs actual headcount; gap.
- D3.2 Activity breakdown: time per activity, peer variance (highlight outliers > X× median).
- D3.3 Waste view: rework %, waiting %, context-switch thrash, approval-loop counts.
- D3.4 Review queue: flagged blocks with one-click override.
- D3.5 Standard-time editor.
- D3.6 **Load-profile view:** activity volume and required-minutes plotted across the study cycle (e.g. by day/week) to expose peaks such as month-end close — not flattened to an average.

**D4. Load profile & cyclical load (e.g. accounting month-end).**
- D4.1 For roles flagged `cyclical = true`, do **not** report a single headcount. Compute and store **baseline load** (representative mid-cycle period) and **peak load** (busiest period, e.g. close week).
- D4.2 Required headcount is shown as a range/curve: baseline required vs. peak required vs. actual.
- D4.3 Surface the three staffing options as outputs: staff-to-peak (idle capacity off-peak), staff-to-average (overtime/backlog at peak), or smooth the peak (level-load / automate).
- D4.4 **Projection shortcut:** if a full-cycle study isn't feasible, multiply the measured `std_minutes_per_unit` by the client's *historical* transaction volumes per period (from their ERP/accounting system) to project peak load without observing every cycle.

**D5. Acceptance criteria.**
- Changing a standard time recomputes manload live.
- Required headcount and gap shown per role with the underlying numbers traceable.
- Peer outliers visibly flagged for follow-up.

---

### MODULE E — Report generation
**Purpose:** output the deliverable in your house format.
- E1. Generate a study report (`python-docx` and/or `python-pptx`) containing: scope, method, VA/NVA charts, manload table, waste findings, recommendations placeholder.
- E2. Aggregate by role; **never** an individual ranking.
- E3. Acceptance: one-click export produces a formatted, branded document with live numbers.

---

### MODULE F — Admin, consent, privacy & study lifecycle
**Purpose:** keep the tool deployable and legal.
- F1. Study wizard: define roles, headcount, available minutes, window, data sources, retention days.
- F1.1 **Study-window = full-cycle rule.** The study window must span at least one complete cycle of the work. For cyclical functions (accounting, payroll) the default minimum is **one full month covering month-end close plus a normal mid-month period**, and such roles are marked `cyclical = true`. The wizard warns if a chosen window is shorter than the role's stated cycle.
- F2. Consent flow: participant sees a plain-language notice (scope, what's collected, what's NOT, aggregate use, no individual punishment, deletion date) and opts in. Withdrawal stops their capture immediately.
- F3. Role-based access: Consultant (all aggregate + flags), Client Admin (deployment status only), Participant (own data only), System Admin (tenant + retention).
- F4. **Retention/deletion scheduler:** auto-delete raw `activity_events` + `esm_responses` N days after study close (default per `data_scope`); keep only aggregate `manload_results` unless told otherwise.
- F5. Audit log of all data access.
- F6. Acceptance: deletion job verifiably removes raw data; withdrawal halts capture within one cycle.

---

### MODULE G — Data validity / anti-gaming (the "how do we know they're truthful" layer)
**Purpose:** make truth the path of least resistance and make lies detectable. This is a **functional** module, not just a policy.

- G1. **Remove the motive (governance, enforced in product):** all participant-level data is pseudonymised; all reporting is role-aggregated; UI never exposes individual rankings to managers. The consent notice states this.
- G2. **Cross-signal divergence detection:** for each block, compare ESM-claimed activity/classification against passive signals. If a participant tags "deep/VA work" while passive shows idle or unrelated category + high switch_count → set `divergence_flag` and route to review. (Flag, not accusation.)
- G3. **Output anchoring:** wherever `volumes` exist, compute time-per-output and use it as the efficiency metric, since output is harder to fake than time.
- G4. **Correction-pattern analysis:** analyse the log of ESM/timeline corrections per participant. If corrections are systematically one-directional (always idle→productive, always waste→VA), surface a "directional-bias" indicator for the consultant.
- G5. **Aggregate robustness:** manload conclusions are computed at role level so a single participant's bias has limited effect; report the dispersion (e.g. interquartile range), not just the mean.
- G6. Acceptance: divergences and directional-bias indicators appear in the dashboard; no single participant's data can swing a role's required headcount beyond a configurable sensitivity bound without being flagged.

---

## 7. Standard-time & manload — worked logic (reference)

**Time needed vs time spent.** Time spent is measured. Time needed (`std_minutes_per_unit`) is *set* by one of three methods, ideally reconciling two:
1. **Best-demonstrated / percentile** — efficient percentile of observed time across peers.
2. **Engineered** — consultant's target cycle time × volume.
3. **Waste-stripped** — VA + necessary-NVA only, excluding rework/waiting/over-processing.

**Manload:**
```
required_minutes(role)   = Σ ( std_minutes_per_unit(activity) × volume(activity, period) )
available_minutes(role)  = available_minutes_per_day × working_days × current_headcount
required_headcount(role) = required_minutes ÷ (available_minutes_per_day × working_days)
gap(role)                = required_headcount − current_headcount
utilisation(role)        = required_minutes ÷ available_minutes
```

**Cyclical roles.** Because `volume` is recorded *per period*, peaks (e.g. month-end) flow through automatically: `std_minutes_per_unit` stays stable while `volume` spikes. For `cyclical = true` roles, compute `required_headcount` for the **baseline period** and the **peak period** separately and report both, plus the load curve across the cycle (see D4). Never collapse a cyclical role to a single average headcount.

---

## 8. Privacy, security & compliance requirements

- P1. **Metadata only.** No keystrokes, no screenshots, no message/file bodies. Window titles hashed or categorised.
- P2. **Lawful basis (Indonesia PDP Law, UU 27/2022):** documented purpose, data minimisation, retention limit, participant rights (access own data, withdraw).
- P3. **Time-boxed:** capture only within `start_date`–`end_date`; agent auto-stops.
- P4. **Pseudonymisation:** no real names in the system; client holds the name↔pseudonym map.
- P5. **Encryption:** TLS in transit; encryption at rest for the database.
- P6. **Deletion:** raw data deleted N days post-close by scheduler; aggregates retained.
- P7. **Data residency:** prefer in-region hosting; document any cross-border transfer.
- P8. **DPA:** a Data Processing Agreement template per client.
- P9. **No individual punitive use** — contractually and in-product.

---

## 9. Tech stack (Python)

| Layer | Choice | Library |
|---|---|---|
| Telemetry | M365 / Google APIs | `msal`, `google-api-python-client` |
| Agent (optional) | Desktop capture | `psutil`, `pywin32`/`pyobjc`, packaged via `PyInstaller` |
| Backend/API | Service + jobs | `FastAPI`, `uvicorn`, `APScheduler`/`celery` |
| ORM/DB | Relational store | `SQLAlchemy` + `PostgreSQL` |
| Analysis | Calc engine | `pandas`, `numpy` |
| Classification | Rules + AI | rule code + Anthropic `anthropic` SDK; later `scikit-learn` |
| Dashboard | Consultant UI | `Streamlit` |
| ESM app | Prompts | Streamlit/PWA web form, or tray app (`pystray`) |
| Reporting | Deliverables | `python-docx`, `python-pptx` |
| Auth | Access control | FastAPI auth + role-based permissions |

**Suggested repo layout:**
```
/agent          # optional desktop capture
/api            # FastAPI: ingestion + connectors + auth
/connectors     # graph.py, gworkspace.py (scheduled pulls)
/engine         # classify.py (rules+Claude), manload.py, validity.py
/dashboard      # Streamlit app
/reports        # docx/pptx generators
/db             # SQLAlchemy models, migrations
/scripts        # retention/deletion, seeding the catalog
```

---

## 10. Build phases & milestones (with acceptance gates)

**Phase 0 — Design (3–4 wks).** Finalise activity catalog (Appendix A), data model, VA/NVA rules, standard-time method, consent/privacy framework.
*Gate:* catalog + schema + consent notice approved.

**Phase 1 — MVP (3–4 mo).** Build Option C/B: telemetry connectors + ESM app + classification engine + manload dashboard + report export + consent/retention.
*Gate:* end-to-end run on synthetic data produces a manload result + report.

**Phase 2 — Internal dogfood (4–6 wks).** Run a real study on your own office.
*Gate:* manload output matches what you already know about your firm within tolerance; classifier calibrated; divergence detection working.

**Phase 3 — Friendly pilot (8–12 wks).** One department at a trusted client.
*Gate:* IT approves deployment; participants accept; a usable manload result is delivered.

**Phase 4 — Productise (6–8 wks).** Harden, deployment SOP, consent kit, DPA/contract templates, pricing.

**Phase 5 — Go to market (parallel).** Position as right-sizing & capacity (not surveillance); land-and-expand.

---

## 11. Non-functional requirements
- N1. Multi-tenant; data isolated per organization.
- N2. Handle ≥ 200 participants × 4-week study without manual intervention.
- N3. Connector pulls and classification run as idempotent scheduled jobs with retry.
- N4. Dashboard recompute on standard-time change ≤ a few seconds for a typical study.
- N5. All destructive actions (delete, withdraw) logged and reversible only within a grace window.

---

## 12. Open decisions (resolve in Phase 0)
1. **Client mix:** office/knowledge work (telemetry-friendly) vs. operations/floor (agent + observation heavy)? Changes which data source is primary.
2. **Build A/B/C order:** confirm starting with telemetry-only (Option C). 
3. **Standard-time default method** per activity type.
4. **Retention default** (e.g. 30 days post-close).
5. **ESM frequency** default (3 vs 6/day) — balance accuracy vs. intrusion.
6. **Layoff framing** with each client (capacity re-deployment vs. sizing) — affects participant honesty and must be decided before go-live.

---

## Appendix A — Example activity catalog (seed; expand per role family)

| role_family | activity_name | default_classification | is_rework |
|---|---|---|---|
| Finance | Prepare invoice | VA | no |
| Finance | Correct rejected invoice | NVA_waste | yes |
| Finance | Reconcile ledger | NVA_necessary | no |
| Finance | Wait for approval | NVA_waste | no |
| Finance | Compliance check | NVA_necessary | no |
| Ops | Process order | VA | no |
| Ops | Re-enter order (error) | NVA_waste | yes |
| Ops | Status meeting | NVA_necessary | no |
| Admin | Format/clean report | NVA_waste | no |
| (all) | Idle / break | NVA_waste | no |

## Appendix B — Example ESM question set
- Q1 (required): *What are you working on right now?* → activity picker (role-family list).
- Q2 (taps): *Is this…* □ Redoing/fixing earlier work □ Waiting on someone □ A new request.
- Q3 (optional): short note.

## Appendix C — Example API endpoints
```
POST /events        # batch passive events from agent
POST /esm           # one ESM response
POST /esm/correction# a timeline correction (logs before/after)
GET  /studies/{id}/manload     # computed result
POST /studies/{id}/standard-times  # set/override std times
POST /connectors/graph/sync    # trigger M365 pull
GET  /participants/me/data     # participant self-view
DELETE /studies/{id}/raw       # retention deletion (admin)
```

## Appendix D — Classification API call (shape)
- Input: block metadata + candidate activity list + nearby ESM context.
- System instruction: *"Return JSON only. Choose activity_id only from the provided list. Never invent activities. Output {activity_id, classification ∈ [VA, NVA_necessary, NVA_waste], confidence 0–1, reason}."*
- Parse defensively; on failure → `needs_review = true`.

---

*End of PRD v1.0.*
