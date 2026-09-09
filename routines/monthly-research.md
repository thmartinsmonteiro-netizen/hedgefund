# Routine: monthly research pass (Claude Code cloud routine)

Create with `/schedule`, monthly, first Saturday, 09:00 America/Sao_Paulo. Give it web search. Prompt:

---

You maintain research/literature.md for a special-situations paper fund. Read it, then read mandate/screens.md and mandate/amendments.md.

1. For every row marked [UNVERIFIED], find the paper (SSRN, NBER, journal page, author site or university repository), confirm title, authors, year and the finding, and rewrite the row with a working link. If you cannot find it, delete the row and say so in the PR.
2. For every lens, search for papers published or posted in the last 18 months on: spin-off and carve-out returns, merger arbitrage and deal completion, post-bankruptcy equity, closed-end fund and holdco discounts, index reconstitution flow, rights issues, regulated-utility regulatory events, Brazilian recuperação judicial outcomes, option-implied event risk, and event-driven strategy capacity and costs. Use SSRN, NBER, arXiv q-fin, Journal of Finance, JFE, RFS, Review of Finance, JFQA, Management Science, and the CFA Institute Financial Analysts Journal. Read the abstract and, where the finding matters, the main results table.
3. Add a row only when the finding would change a screen, a gate, a holding period, a sizing rule, or a base rate the memo uses. One line for the finding, one line for the rule implication. No summaries of papers that change nothing.
4. Where a finding argues for changing a rule, do not edit screens.md. Draft the change as a proposed dated amendment at the bottom of research/literature.md under "Proposed amendments", with the paper it rests on.
5. Update the "Last pass" date. Commit on a branch research/YYYY-MM and open a pull request titled "Research pass YYYY-MM" whose body lists: rows verified, rows added, rows deleted, amendments proposed.

Rules: never cite a paper you did not open this session; never state a number the paper's own text does not contain; paraphrase, do not quote at length; prefer peer-reviewed or top working-paper series over blogs and vendor reports, and label practitioner sources as such.
