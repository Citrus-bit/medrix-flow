import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ResearchQuestSnapshot } from "@/core/research";

import { ResearchQuestSnapshotView } from "./research-dashboard";

const snapshot: ResearchQuestSnapshot = {
  quest: {
    quest_id: "rq-demo",
    thread_id: "thread-demo",
    title: "Evidence grounded research agents",
    topic: "Evidence grounded research agents",
    scope: null,
    objective: null,
    domain: "cs_ai",
    stage: "review",
    status: "blocked",
    academic_project_id: "academic-1",
    experiment_project_ids: ["exp-1"],
    metadata: {
      delivery_mode: "fast_draft_first",
      draft_ready_at: "2026-05-09T00:03:30Z",
      finalization_run_id: "run-finalization",
      draft_artifacts: ["/mnt/user-data/outputs/fast-draft-rq-demo.tex"],
    },
    created_at: "2026-05-09T00:00:00Z",
    updated_at: "2026-05-09T00:05:00Z",
  },
  ledger: [
    {
      entry_id: "ledger-1",
      quest_id: "rq-demo",
      stage: "results_synthesized",
      event_type: "stage_advanced",
      summary: "Results ready.",
      inputs: {},
      outputs: {},
      artifacts: ["/mnt/user-data/outputs/metrics.json"],
      tool_name: null,
      model_name: null,
      error: null,
      gate_decision: null,
      created_at: "2026-05-09T00:03:00Z",
    },
  ],
  gates: [
    {
      gate_id: "gate-1",
      quest_id: "rq-demo",
      stage: "final_bundle",
      gate_type: "final_release",
      status: "pending",
      decision: null,
      reason: null,
      required: true,
      created_at: "2026-05-09T00:04:00Z",
      decided_at: null,
    },
  ],
  evidence: [
    {
      claim_id: "claim-1",
      quest_id: "rq-demo",
      claim: "Claim-level evidence maps reduce unsupported manuscript claims.",
      paper_id: "paper-1",
      source_title: "Evidence Maps for Research Agents",
      locator: "p. 4",
      snippet: "Evidence maps identify unsupported claims.",
      quote: null,
      support_status: "supported",
      confidence: 0.82,
      artifact_path: null,
      metadata: {},
      created_at: "2026-05-09T00:01:00Z",
    },
  ],
  novelty_checks: [],
  experiment_branches: [
    {
      branch_id: "branch-1",
      quest_id: "rq-demo",
      experiment_project_id: "exp-1",
      parent_branch_id: null,
      name: "Baseline verifier",
      branch_type: "baseline",
      status: "completed",
      priority: 1,
      seed: 42,
      metrics: { unsupported_claim_rate: 0.1 },
      artifact_paths: ["/mnt/user-data/outputs/metrics.json"],
      failure_summary: null,
      metadata: {},
      created_at: "2026-05-09T00:02:00Z",
      updated_at: "2026-05-09T00:03:00Z",
    },
  ],
  manuscript_sections: [
    {
      section_id: "section-1",
      quest_id: "rq-demo",
      section_key: "methods",
      title: "Methods",
      content: "",
      claim_ids: ["claim-1"],
      artifact_paths: ["/mnt/user-data/outputs/methods.md"],
      status: "draft_ready",
      created_at: "2026-05-09T00:03:00Z",
      updated_at: "2026-05-09T00:03:00Z",
    },
  ],
  reviewer_reports: [
    {
      report_id: "review-1",
      quest_id: "rq-demo",
      stage: "review",
      reviewer_profile: "citation-integrity",
      score: 0.78,
      verdict: "pass",
      findings: ["citation-integrity review completed with structured integrity checks."],
      required_actions: [],
      created_at: "2026-05-09T00:04:00Z",
    },
  ],
};

describe("ResearchQuestSnapshotView", () => {
  it("renders lifecycle, evidence, branches, manuscript, review, and gates", () => {
    const onAdvance = vi.fn();
    const onApproveGate = vi.fn();

    render(
      <ResearchQuestSnapshotView
        snapshot={snapshot}
        onAdvance={onAdvance}
        onApproveGate={onApproveGate}
      />,
    );

    expect(screen.getByText("Quest Timeline")).toBeInTheDocument();
    expect(screen.getByText("Claim Evidence Map")).toBeInTheDocument();
    expect(screen.getByText("final_release")).toBeInTheDocument();
    expect(screen.getByText("Finalizing")).toBeInTheDocument();
    expect(screen.getAllByText(/run run-finalization/).length).toBeGreaterThan(0);
    expect(screen.getByText("Claim-level evidence maps reduce unsupported manuscript claims.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Approve final_release/i }));
    expect(onApproveGate).toHaveBeenCalledWith(snapshot.gates[0]);

    fireEvent.click(screen.getByRole("button", { name: /Advance to Revision/i }));
    expect(onAdvance).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("tab", { name: /Experiments/i }));
    expect(screen.getByText("Baseline verifier")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: /Manuscript/i }));
    expect(screen.getByText("Artifact Bundle")).toBeInTheDocument();
    expect(screen.getByText("/mnt/user-data/outputs/methods.md")).toBeInTheDocument();
    expect(screen.getByText("/mnt/user-data/outputs/fast-draft-rq-demo.tex")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: /Review/i }));
    expect(screen.getByText("citation-integrity")).toBeInTheDocument();
  });

  it("shows final PDF artifacts from quest metadata", () => {
    const finalSnapshot: ResearchQuestSnapshot = {
      ...snapshot,
      quest: {
        ...snapshot.quest,
        stage: "final_bundle",
        status: "completed",
        metadata: {
          delivery_mode: "final_only",
          final_bundle_artifacts: [
            "/mnt/user-data/outputs/manuscript-rq-demo.pdf",
            "/mnt/user-data/outputs/manuscript-rq-demo.tex",
            "/mnt/user-data/outputs/references.bib",
            "/mnt/user-data/outputs/citation_audit.json",
          ],
          final_bundle_ready_at: "2026-05-09T00:06:00Z",
          final_bundle_export_status: "passed",
          final_bundle_export_message: "PASS: manuscript_export wrote `/mnt/user-data/outputs/manuscript-rq-demo.pdf`.",
        },
      },
    };

    render(<ResearchQuestSnapshotView snapshot={finalSnapshot} />);

    expect(screen.getByText("Final PDF ready")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: /Manuscript/i }));
    expect(screen.getByText("/mnt/user-data/outputs/manuscript-rq-demo.pdf")).toBeInTheDocument();
  });
});
