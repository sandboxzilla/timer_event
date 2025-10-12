# QA Policy and Bug Reporting Guidelines

This document outlines the Quality Assurance (QA) process and bug reporting policy for the `timer_event` project. Adhering to these guidelines ensures that we maintain a high level of quality and consistency in our development process.

## QA Process

The QA process is initiated when a bug is reported or a new feature is implemented. The process is as follows:

1.  **Bug Validation:** When a bug is reported, a QA engineer (or the reporter if acting as QA) first validates the bug to ensure it is reproducible. The validation process typically includes reviewing the affected files and running the test suite.
2.  **Fix Implementation:** Once a bug is validated, a developer implements a fix. Every fix should include targeted test coverage to prevent regressions.
3.  **Fix Validation:** After a fix is implemented, a QA engineer (or an assignee acting as QA) validates the fix. Validation includes:
    *   Reviewing the code changes to ensure they are correct and follow the project's coding standards.
    *   Running the relevant test suite to ensure the fix works as expected and has not introduced new bugs.
    *   Updating the bug report with a timestamped validation section. **Developers who implement the fix should not author the validation entry unless they were explicitly assigned the QA role for that bug.**

## Bug Reporting

All bugs are tracked in the `docs/bug_report.md` file. The bug report is a living document that is updated as bugs are found, fixed, and validated. Every entry must clearly identify who recorded each action (reporting, resolution, validation) using the user initial suffix described below.

### Bug ID Generation

Each bug is assigned a unique ID with the format `TE:YY.MM.DD.HH.mm.ss PT - UI`.

*   **TE:** Represents the Project ID for "Timer Event".
*   **YY.MM.DD.HH.mm.ss:** Represents the Pacific Time (PT) timestamp when the issue was logged.
*   **PT:** Represents Pacific Time for time zone context.
*   **UI:** Represents the User Initial of the person making the entry (e.g., EY for Erol Yesin, GG for Google Gemini, OC for OpenAI Codex).

To generate a new bug ID, use the current date and time in the format `YY.MM.DD.HH.mm.ss`, append it to the `TE:` prefix, and add your user initial. For example, if a bug is found on October 11, 2025, at 3:05:06 PM PT by Erol Yesin, the bug ID would be `TE:25.10.11.15.05.06 PT - EY`.

### Bug Report Format

Bug entries in the bug report are stored in stack order (latest entries first) and must follow this format. Each section records the initials of the contributor responsible for that action.

```markdown
### **ID:** TE:YY.MM.DD.HH.mm.ss PT - UI
**Title:** A brief, descriptive title of the bug.

**Details:**
Describe the issue, including observed behaviour, expected behaviour, and reproduction steps.

**Affected Files:**
List the files/modules impacted by the defect.

**Resolution (YYYY-MM-DD - UI):**
Summarise the fix that was applied.
- Updated files: enumerate the files modified to implement the fix.

**Validation of Bug Fixes (YYYY-MM-DD HH:mm:ss PT - UI):**
*(Optional; completed by QA personnel only.)* Document the validation steps and results. Developers implementing the fix should leave this section for QA.
```
