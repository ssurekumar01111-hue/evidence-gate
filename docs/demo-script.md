# Evidence Gate — Hackathon Demo Video Script & Shot List

> **Target Total Duration:** **2:48** (Hard Ceiling: 3:00 per Hackathon Rules)  
> **Source:** Based on real output from `scripts/run_demo_timeline.py` executed against live DataHub GMS.

---

### Beat 1: Context Discovery (0:00 – 0:20) | Duration: 0:20
* **Visual:** Terminal showing `python scripts/run_demo_timeline.py` [Step 1] output and DataHub UI dataset overview for `order_details`.
* **Voiceover:** "An engineer submits Pull Request #42 proposing to rename column `order_total` to `recognized_revenue` on Snowflake dataset `order_details`. Before any PR is merged, Evidence Gate queries DataHub's context graph via the Agent Context Kit, discovering dataset owners David Kim and Julia Novak, the 'Revenue by Customer Class' glossary term, and 13 downstream lineage consumers."

---

### Beat 2: Deterministic Risk Assessment (0:20 – 0:40) | Duration: 0:20
* **Visual:** Terminal output [Step 2] showing Risk Score `75/100`, leaning `NEEDS-REVIEW`, and the 6 required approvers.
* **Voiceover:** "Evidence Gate evaluates deterministic risk rules: because the column is linked to a core Revenue glossary term and has real downstream BI consumers across PowerBI, Looker, and Tableau, the risk score rises to 75 out of 100 with a leaning of NEEDS-REVIEW — naming six specific owners, pulled straight from DataHub, who need to sign off."

---

### Beat 3: Read-Only Metric Validation (0:40 – 1:05) | Duration: 0:25
* **Visual:** DuckDB metric validation query execution [Step 3] showing aggregate comparison values: `$18,789.67` vs `$16,317.15`.
* **Voiceover:** "Next, Evidence Gate runs a read-only DuckDB metric validation query comparing old gross transaction totals against the proposed recognized revenue definition. The aggregate drops from $18,789.67 to $16,317.15 — a 13.16% shift that far exceeds our strict 1.00% tolerance threshold."

---

### Beat 4: Decision Blocking & Remediation Patch (1:05 – 1:30) | Duration: 0:25
* **Visual:** Final DecisionReceipt output [Step 4] showing status `BLOCKED`, final Risk `100/100`, and generated dbt patch `examples/recognized_revenue_patch.sql`.
* **Voiceover:** "Combining risk rules and failed metric validation, the decision engine deterministically BLOCKS the change. It doesn't leave the engineer stranded: Evidence Gate automatically generates a dbt SQL compatibility model patch and a migration test suite in `examples/`."

---

### Beat 5: Decision Provenance Write-Back (1:30 – 1:50) | Duration: 0:20
* **Visual:** DataHub UI dataset page showing the 13 custom properties, PR #42 documentation link, and open Operational Incident banner.
* **Voiceover:** "Evidence Gate writes a Decision Provenance artifact directly back to DataHub: emitting 13 structured custom properties, linking PR #42, and raising a native DataHub operational incident on the asset. The reasoning is now an active node in the organization's metadata graph."

---

### Beat 6: Independent Decision Retrieval (1:50 – 2:10) | Duration: 0:20
* **Visual:** Fresh process invocation of `python scripts/retrieve_decision.py` [Step 6] printing stored provenance.
* **Voiceover:** "Six months later, an auditor or fresh agent asks 'why was this migration blocked?' Running an independent retrieval script with only the asset URN queries DataHub GMS directly. With zero application memory state, it retrieves the exact reasoning and 13.16% validation delta."

---

### Beat 7: Graph-Change Invalidation Watcher (2:10 – 2:30) | Duration: 0:20
* **Visual:** Graph-change watcher output [Step 7] showing term removal and provenance status flipping to `STALE`.
* **Voiceover:** "What happens when the context graph changes? We simulate removing the 'Revenue by Customer Class' glossary term link from DataHub. The Evidence Gate watcher inspects the graph, detects the broken dependency, and automatically updates the provenance status on DataHub from ACTIVE to STALE."

---

### Beat 8: Precedent Retrieval (2:30 – 2:48) | Duration: 0:18
* **Visual:** Precedent retrieval CLI output [Step 8] detailing 'What Still Applies' vs 'What Differs'.
* **Voiceover:** "Finally, a second team proposes a similar rename on `order_details_replica`. Evidence Gate retrieves the prior decision as precedent, explicitly identifying that the 1.00% revenue tolerance threshold still applies while highlighting differences in asset URN and PR URL."

---

### Summary Timeline
| Beat | Title | Start Time | Duration |
|---|---|---|---|
| 1 | Context Discovery | 0:00 | 0:20 |
| 2 | Risk Assessment | 0:20 | 0:20 |
| 3 | Read-Only Metric Validation | 0:40 | 0:25 |
| 4 | Block & Remediation Patch | 1:05 | 0:25 |
| 5 | Provenance Write-Back | 1:30 | 0:20 |
| 6 | Independent Decision Retrieval | 1:50 | 0:20 |
| 7 | Staleness Invalidation Watcher | 2:10 | 0:20 |
| 8 | Precedent Retrieval | 2:30 | 0:18 |
| **Total** | **Full Demo Video Path** | **0:00** | **2:48** |
