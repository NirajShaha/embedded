# ECU Security Testing & Test Plan Management — Business Document

**Audience:** Senior management, product, sales, marketing, operations, and customer-facing teams.

**Purpose:** explain, in business terms, what this application is, the problem it solves, the value it delivers, and how we should position and roll it out. Technical terms are explained as they appear; a glossary is included at the end.

**Status note:** items marked **(future)** are proposed enhancements, not yet built. No performance, cost, or adoption figures are quoted anywhere in this document; where a measured number would strengthen the argument, a placeholder `[ … ]` is shown so the organization can insert its own verified data.

---

## 1. Executive Summary

Vehicles are increasingly controlled by dozens of electronic computers (ECUs — Electronic Control Units). Before an ECU ships, security teams must plan a penetration test: a set of agreed, documented attack tests that a security partner will run against the device.

Today that planning is a **manual, document-heavy process**: a standard test-plan template is copied for each project, candidate tests are selected and reworded by hand, and the result is assembled into a PDF. The knowledge about *what to test* lives in a catalogue that is difficult to keep consistent and current.

This application replaces that manual loop with a secure web platform that:

- Holds the **security test catalogue in one governed place** (maintained by admins, reusable by everyone).
- Lets any authorized team **build a project-specific test plan** in the browser: pick the ECU, record its details, choose which tests apply, adjust wording where needed, and click once to download a **professionally formatted PDF test plan** in the corporate template style.
- Keeps a clean record of **what is the standard catalogue and what is project-specific**, with controlled access and an audit trail on test cases.

**In one sentence:** it turns a repeated, error-prone documentation exercise into a governed, repeatable, self-serve workflow — one shared catalogue in, a ready-to-send test plan PDF out.

---

## 2. Previous Manual Process

Based on the current working practice (see the corporate template that the application's PDF mirrors):

1. The security engineer **copies the standard test-plan template** (cover, distribution list, introduction, testing approach, test scope, references, appendices).
2. **ECU details** (name, part number, risk rating, architecture, vehicle line, year, chip provider, availability dates, export-control class, pentest partner) are typed into the document by hand, from emails, BOMs, and program records.
3. The engineer **reviews the test catalogue** (categories → objectives → specific test actions) and hand-picks which tests apply to this ECU.
4. Applicable tests are **reworded and tailored** in the document: project-specific test steps, tools to be used, and references.
5. The finished document is **assembled, reviewed, and circulated** as a PDF to the program team and the external pentest partner.
6. For the next project, steps 1–5 start again from scratch; catalogue knowledge is carried in people's heads and in diverging document copies.

*(If your organization's current process differs in detail, replace this section with your own baseline description. The improvement logic below still applies.)*

---

## 3. Need for the Application

- **Every ECU program repeats the same work.** The test-plan structure and most candidate tests are shared across programs, yet each program rebuilds the document manually.
- **The catalogue must stay authoritative.** When a new test, tool, or threat model entry is agreed, it must appear consistently in every future plan. Today that discipline is manual.
- **Security work is time-boxed.** Programs have fixed windows for hardware availability and production software; a faster, more reliable path to a signed test plan directly protects the test schedule.
- **Compliance and audit expectations are rising.** Regulated vehicle cybersecurity programs need traceable documentation: who changed which test, when, and what was project-specific.
- **Knowledge is concentrated in few people.** A single governed catalogue makes the knowledge an organizational asset rather than individual memory.

---

## 4. Problems Solved

| Problem (manual process) | What the application does |
|---|---|
| Test knowledge scattered across documents and individuals | One governed, searchable catalogue maintained by admins |
| Each plan re-created from a blank template copy | Plans are generated from live data: ECU details + selected tests |
| Hand-picking and rewording of tests per project | Filter the catalogue (by test category and test type), then customize any test's wording per project |
| Same value (e.g., a tool name) re-typed everywhere, drifting over time | Reusable master values: stored once, selected everywhere; new values can be created inline without leaving the form |
| No clear separation of "standard" vs "project-specific" content | Project edits live as *overrides*; the master catalogue is never altered |
| No access control or audit trail on the catalogue | Login with role-based permissions (admin vs. user); test cases record who created/updated/deleted them and when |
| Inconsistent, slow document assembly | One click produces the formatted PDF in the corporate template style |

---

## 5. Proposed New Process

The new end-to-end workflow (all steps available today):

1. **Admin (security engineering lead):** keeps the catalogue current — adds or edits test cases, adds new tools/threats/protocols as they are agreed, reviews catalogue statistics.
2. **Project team:** creates the project and records the ECU details in a structured form (12 fields — no hunting through emails).
3. **Project team:** optionally completes the multi-step **configuration wizard** (four pages of predefined attribute selections describing the system).
4. **Project team:** opens the test dashboard, filters the catalogue by **category** and **test type**, expands any test to read the full detail (description, attack path, steps, expected output, impacts, tools, references).
5. **Project team:** customizes any test for this project — wording, tools, references. A small "Edited" badge marks customized tests; any test can be reset to the master version at any time.
6. **Project team:** selects the tests to include and clicks **Generate PDF Report**. A ready-to-review test-plan PDF downloads, with the project's ECU details on the cover and in the introduction, and the selected (and project-edited) tests in the test-scope section.
7. **Review & send:** the document is reviewed by the program team and shared with the pentest partner as before — but the assembly work is done.

**What stays human:** deciding *which* tests apply, *how* they are tailored, and the review/sign-off. The application removes the mechanical part.

---

## 6. Before-and-After Comparison

| Dimension | Before (manual) | After (application) |
|---|---|---|
| Catalogue location | Spreadsheets/documents/people's heads | One governed web catalogue, admin-controlled |
| Creating a new test plan | Copy template, re-type details, re-pick and reword tests by hand | Create project, fill ECU form, filter, customize, click to export |
| Keeping catalogue current | Manual, easy to drift | Admins edit in one place; all new plans use the current catalogue |
| Reusing values (tools, threats, protocols) | Re-typed per document, typo-prone | Selected from master lists; new values created once, reused everywhere |
| Standard vs. project content | Mixed together in the document | Clearly separated (master catalogue vs. project overrides) |
| Who can change the catalogue | Anyone with the document | Admin role only; other users customize per project without touching master |
| Audit trail | None | Created/updated/deleted by whom, and when, on every test case |
| Document formatting | Manual assembly, inconsistent | Consistent corporate-template PDF generated by the system |
| Onboarding a new engineer | Shadowing + document archaeology | Login, follow the guided workflow |

**Not a replacement for judgment:** the before/after is about the *mechanics* of plan production. Test selection, tailoring, and sign-off remain expert activities.

---

## 7. Stakeholder Benefits

| Stakeholder | Benefit |
|---|---|
| **Senior management / program leadership** | A reliable, repeatable path to a signed test plan; reduced dependence on individuals; visibility of catalogue health via admin statistics |
| **Cybersecurity / security engineering** | Governed, current test catalogue; less time formatting, more time analyzing; consistent language across programs |
| **EE / ECU program teams** | Self-serve: no waiting on a security engineer to re-prepare a template; structured ECU data captured once |
| **External pentest partners** | Receive a complete, consistently structured, project-specific test plan — fewer clarification rounds *(expected; partner feedback to be measured during pilot)* |
| **Compliance / quality** | Traceable catalogue changes (who/when); project-specific deviations visible as overrides |
| **Sales / marketing** | A concrete capability story for customers: "we plan ECU penetration testing from a governed, reusable catalogue and produce the test plan in-system" |
| **IT / operations** | A standard, documented web application with controlled access (see technical document for security details) |

---

## 8. Business and Operational Value

Stated without invented numbers — each item below is a qualitative improvement; the brackets are where verified organizational data should be inserted:

- **Cycle time:** time from "project started" to "first complete test plan PDF" — baseline `[X days, measure in pilot]` vs. post-adoption `[Y days]`.
- **Repetitive effort:** manual re-typing of ECU details, test selection, and formatting per project is replaced by form entry and one click — engineering hours freed per plan: `[estimate hours/project before and after]`.
- **Consistency & quality:** every plan follows the same template; catalogue wording is single-sourced; fewer formatting and transcription errors to catch in review `[count errors found in plan reviews before vs. after]`.
- **Schedule risk reduction:** faster plan production protects the fixed security-testing windows in ECU programs.
- **Knowledge retention:** the catalogue is now an organizational asset; staff changes no longer strand the test knowledge.
- **Audit readiness:** built-in record of catalogue changes supports internal and customer audits without retroactive reconstruction.
- **Foundation for more:** the same platform can grow into test *execution* tracking, findings management, and compliance reporting (see §13) — protecting the investment.

**Costs to consider (for the business case):** infrastructure (web servers + database), admin time to maintain the catalogue, training, and any customization. Baseline figures: `[insert procurement/ops estimates]`.

---

## 9. Sales and Marketing Positioning

**Positioning statement (internal and customer-facing):**

> "A governed ECU penetration-test planning platform: one authoritative test catalogue, project-specific tailoring without losing the standard, and a ready-to-send, template-perfect test plan PDF — instead of a manual document exercise for every program."

**Message pillars:**

1. **One catalogue, every program.** The test knowledge is centralized, controlled, and always current.
2. **Self-serve for program teams.** Authorized engineers build their own test plans without waiting on document preparation.
3. **Audit-ready by design.** Role-based access and change tracking on every test case.
4. **Familiar output, faster.** The delivered document looks like the corporate template your partners already know — the work to produce it is what changed.

**Use cases in pitches:** new ECU program kickoff, pre-production security gate, customer demonstration of a mature cybersecurity process, onboarding of new engineers/partners.

**What to say (true today):** plan generation, catalogue governance, project customization, access control, audit fields, PDF in corporate template style.
**What to say is coming, not here (future):** test execution and findings tracking, configurable document sections, partner portal, compliance dashboards.

---

## 10. Example Business Scenario

*(Illustrative; names and values are placeholders.)*

1. A new vehicle gateway program (**"VG-2026"**) reaches its security-testing phase. The program needs a penetration test plan for the gateway ECU before the external partner's scheduled window.
2. The program's security engineer logs in, creates project **VG-2026**, and fills the ECU form once: part number, risk rating (High), architecture, vehicle line, chip provider, hardware/harness/software availability dates, export-control class, pentest partner.
3. On the test dashboard, the engineer filters the catalogue to the relevant **categories** (e.g., communication and firmware) and **test types** (e.g., black-box).
4. Two tests need project-specific steps (different diagnostic access on this platform). The engineer edits only those two — each now carries an "Edited" badge; everything else remains the approved standard wording.
5. The engineer clicks **Generate PDF Report** and receives the test plan: cover page and introduction populated with VG-2026's ECU data, test-scope section containing exactly the selected tests with the two tailored entries.
6. The document is reviewed in the program meeting and sent to the pentest partner — complete, current, and traceable.
7. Weeks later, a second program needs the same gateway family tested with a different chip provider. It reuses the catalogue (now including any new tests added since), applies its own overrides, and exports its own plan.

*Measured outcome for this scenario (cycle time, review findings, partner feedback): to be captured during pilot — `[placeholder for measured data]`.*

---

## 11. Proposed KPIs

To be baselined before/after rollout so every figure is our own, verified data:

| KPI | What it measures | Baseline target |
|---|---|---|
| Plan cycle time | Days from project start to first complete PDF | `[measure 2–3 manual plans first]` |
| Engineering hours per plan | Manual effort spent producing each plan | `[time-box 2–3 plans]` |
| Catalogue reuse rate | % of plan test cases taken from the shared catalogue vs. newly written | `[define]` |
| Catalogue drift incidents | Cases where a plan diverged from the agreed catalogue | `[track via reviews]` |
| Review error count | Formatting/transcription errors caught in plan review | `[track via review notes]` |
| Adoption | % of eligible ECU programs using the platform for their plans | `[target at 3/6/12 months]` |
| Catalogue health | Active test cases, changes in last 30 days (visible in admin statistics) | `[report monthly]` |
| Schedule protection | Number of programs whose pentest window was at risk due to late plan preparation | `[track in program reviews]` |

---

## 12. Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Low adoption; teams keep using manual templates | Medium | High | Pilot with 1–2 willing programs; keep the output format familiar (same template look); make admin effort visible via statistics; management sponsorship |
| Catalogue quality degrades (stale or conflicting entries) | Medium | High | Admin-only catalogue edits; role separation; change audit fields; periodic catalogue review owned by a named security lead |
| Users over-rely on the generated PDF without expert review | Low–Medium | High | Position the tool explicitly as plan *production*, not plan *approval*; keep the human review/sign-off step in the process |
| Some template sections still need manual input (distribution list, schedules, references are currently static in the PDF) | Certain (today) | Medium | Document the manual steps; make these sections data-driven **(future)**; until then, treat the generated PDF as a near-final draft |
| Single point of knowledge for catalogue administration | Medium | Medium | Document admin responsibilities; train a second admin; admin UI is self-explanatory (pick-or-create fields) |
| Security of the platform itself (credentials, unauthorized access) | Low | High | Login with strong hashed passwords, expiring session tokens, role-based access; production environment forbids dev defaults; further hardening (SSO, MFA, rate limiting) is on the roadmap **(future)** |
| Change fatigue from new process | Medium | Medium | Training sessions, quick-reference guide, dedicated support channel during pilot |

---

## 13. Future Opportunities

All items below are **proposed enhancements — not currently built** (detailed in the technical roadmap):

1. **From planning to execution:** record test execution status, findings, severity, and remediation per project — turning the platform into the system of record for the whole pentest lifecycle.
2. **Fully configurable document:** make the currently static sections (distribution list, document history, roles, schedules, references, appendices) project-editable in the app; per-project document versioning.
3. **Enterprise identity:** SSO (e.g., company login), MFA, user self-service, and per-project access rights.
4. **Deeper catalogue tooling:** full-text search, more filters, bulk import/export, management of test categories/objectives in-app.
5. **Compliance mapping:** link catalogue tests to standards (e.g., ISO/SAE 21434, UN R155) and produce compliance-ready reports.
6. **Partner collaboration:** a controlled portal or export flow for external pentest partners.
7. **Insight:** dashboards on catalogue usage, plan production times, and open items across programs.

Each extends the existing platform; none requires replacing it.

---

## 14. Recommendation and Conclusion

**Recommendation: adopt.** The application solves a real, recurring, and well-understood pain point with a low-risk, incremental approach:

- Start a **pilot with 1–2 ECU programs** and a named catalogue owner.
- **Baseline the KPIs in §11 first** (manual cycle time, hours, review errors) so the business case is built on our own numbers.
- Run the pilot in parallel with the manual process for one full plan cycle; compare; then **roll out to all eligible programs** with a short training.
- Sequence the roadmap (§13) with security engineering: execution tracking and configurable document sections have the highest follow-on value.

**Conclusion:** today, producing an ECU test plan is a manual craft that competes with real analysis work for security engineers' time. The platform turns that craft into a governed, self-serve workflow: one catalogue, project-tailored plans, audit-ready records, and a one-click professional PDF. It is a modest system doing one job very well — and it is the natural foundation for the full pentest lifecycle tooling we will want next.

---

## Key Takeaways

- Replaces manual template copying with a governed catalogue + self-serve plan building + one-click PDF.
- Master catalogue vs. project edits are cleanly separated — standard stays standard, projects stay flexible.
- Access-controlled and audited: admins govern the catalogue; users build plans; changes are traceable.
- No invented numbers anywhere in this document — baselining KPIs before rollout is a condition of the business case.
- Clear, sequenced future value: execution tracking, configurable document, enterprise login, compliance mapping.

## Next Steps

1. Agree the pilot program(s), pilot owner, and catalogue owner.
2. Baseline KPIs on 2–3 manual plans (cycle time, hours, review errors).
3. Provide the initial catalogue content (categories, objectives, test cases) to the admin role.
4. Run the pilot cycle; capture measured results against §11; present adoption decision.
5. Commission the security/IT deployment review (see technical document, deployment flow).

## Assumptions

- Program teams have web access and are comfortable with modern web forms (training provided regardless).
- Security engineering will own the catalogue and the admin role from day one.
- The corporate template structure (mirrored in the PDF) remains the accepted output format.
- Infrastructure for a standard web application + relational database is available within existing IT budgets.
- Manual sign-off of the generated plan remains part of the quality process.

## Limitations

- **Static PDF sections today:** distribution list, document history, supporting documents, roles, attacker model, assumptions, schedules, references, and appendices A–C are not yet editable in the app and must be reviewed/completed manually.
- **Planning tool only:** it does not track test execution, findings, or remediation **(future)**.
- **Filtering scope:** catalogue filtering is by category and test type; free-text search and additional filters are not yet available **(future)**.
- **Access model:** every authorized user can see all projects; per-project permissions are not yet available **(future)**.
- **No measured benefits yet:** all quantitative claims are placeholders to be filled with pilot data.

## Glossary (plain language)

| Term | Simple explanation |
|---|---|
| ECU | Electronic Control Unit — a computer inside the vehicle that controls a function (e.g., a gateway, brake system, infotainment). |
| Penetration test (pentest) | Authorized, documented attempts to attack a system to find weaknesses before real attackers do. |
| Test plan | The document that agrees, before testing starts, what will be tested, how, and by whom. |
| Test catalogue | The master library of candidate security tests, organized by category (e.g., communication, firmware) and objective. |
| Category → Objective | The catalogue's two-level organization: a broad test category contains specific objectives; each test case belongs to one objective under one category. |
| Test type (black-box / gray-box / white-box) | How much insider knowledge the tester has during the test. "Both" is a special filter meaning "all types". |
| Master data | Reusable reference values (tools, protocols, threats, assets) stored once and selected everywhere. |
| Override | A project's own edit to a catalogue test (wording, tools, references). It changes what *that project* sees and exports, without altering the master catalogue. |
| "Edited" badge | A marker showing a test in a project has been customized from the master version. |
| Configuration wizard | Four guided pages of predefined selections that describe the project's system attributes. |
| JWT / session token | A short-lived, signed "badge" the browser receives at login and presents with each request, so the server knows who is working. It expires automatically. |
| Role-based access (RBAC) | Different capabilities per role: **ADMIN** (governs the catalogue) and **USER** (builds project plans). |
| Soft delete | Marking a test case as deleted (keeping it for the audit trail) instead of erasing it; it disappears from all views. |
| Audit fields | Automatic records of who created/updated/deleted a test case and when. |
| Normalized tables | Storing each value once in its own table and linking by reference — the database way of preventing duplication and drift. |
| PDF generation | The server assembles the formatted test-plan document from live data when the user clicks "Generate PDF Report". |
| Pilot | A controlled first rollout to a small set of programs to measure real results before full adoption. |
| KPI | Key Performance Indicator — a named, measured number used to track success (see §11). |
