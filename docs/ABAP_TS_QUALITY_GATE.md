# ABAP TS Quality Gate

Purpose: reduce syntax, ATC, runtime, and requirement-fit errors when creating ABAP from a technical specification.

## Tool Roles

- SAP/styleguides: source of Clean ABAP and ABAP code review rules.
- ABAP cleaner: formatting and mechanical cleanup. It does not prove semantic correctness.
- abaplint: offline static analysis for abapGit-serialized ABAP repositories. It does not replace SAP syntax check, activation, or ATC.
- ATC/ADT/MCP: authoritative SAP-side validation. Use this for syntax, activation, released API, cloud readiness, and system-specific checks.

## Required Workflow

1. Read the TS first.
   - Extract object list, input/output fields, tables, transactions, exits/BAdIs, authorization points, background jobs, and acceptance criteria.
   - Keep unsupported or missing TS fields blank. Do not invent values.
   - Create a traceability list from TS requirement to ABAP object or method.

2. Check system and local context before writing.
   - Inspect existing active SAP objects when available.
   - Use where-used/search before changing shared logic.
   - Verify DDIC fields from the real system before relying on table or structure names.
   - Follow the naming-standard document supplied for the task. If none is supplied, stop and state the naming assumption before creating objects.

3. Draft the smallest correct implementation.
   - Prefer released APIs, standard framework behavior, Open SQL, CDS/RAP patterns, and existing project utilities.
   - Do not add speculative abstractions, generic frameworks, unused extension points, or dead code.
   - Validate all trust-boundary input and all data-loss paths.
   - Add ABAP Unit or a minimal runnable check for non-trivial logic.

4. Run local cleanup and offline checks when applicable.
   - Run ABAP cleaner on the changed ABAP source or use its read-only preview before applying broad cleanup.
   - Run abaplint only when the ABAP code exists as abapGit-style local files and an `abaplint.json` is present or intentionally created.
   - Treat abaplint results as early feedback, not as SAP-system proof.

5. Run SAP-side validation before calling the code ready.
   - Activate or syntax-check each changed object in SAP.
   - Run ATC for each changed ABAP object.
   - Run GetReleasedAPI or SAP Help checks for non-released or classic APIs when clean-core/cloud readiness matters.
   - Fix critical/high ATC findings before completion, or explicitly list the blocker with evidence.

6. Review gate when code is versioned.
   - Review must use this file and `AGENTS.md`.
   - PR or delivery notes should include TS source, object list, validation results, and known unvalidated items.
   - AI review comments do not override ATC/activation findings.

## Completion Report

Every ABAP delivery must state:

- TS artifact read.
- Objects created or changed.
- Naming source used.
- DDIC/system checks performed.
- ABAP cleaner status.
- abaplint status, or why not applicable.
- Activation/syntax status.
- ATC status.
- ABAP Unit/manual test status.
- Remaining risks or missing TS data.
