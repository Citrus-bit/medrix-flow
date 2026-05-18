export type ResearchStage =
  | "intake"
  | "literature"
  | "novelty_check"
  | "evidence_verified"
  | "experiment_planned"
  | "experiment_running"
  | "results_synthesized"
  | "manuscript_draft"
  | "review"
  | "revision"
  | "final_bundle";

export type ResearchQuestStatus = "active" | "blocked" | "completed" | "error";
export type GateStatus = "pending" | "approved" | "rejected";
export type ResearchDeliveryMode = "fast_draft_first" | "final_only";
export type ResearchFinalBundleExportStatus = "passed" | "blocked" | "error";
export type ResearchQuestMetadata = Record<string, unknown> & {
  delivery_mode?: ResearchDeliveryMode;
  draft_ready_at?: string;
  finalization_run_id?: string;
  draft_artifacts?: string[];
  final_bundle_artifacts?: string[];
  final_bundle_ready_at?: string;
  final_bundle_export_status?: ResearchFinalBundleExportStatus;
  final_bundle_export_message?: string;
};
export type SupportStatus =
  | "supported"
  | "unsupported"
  | "contradicted"
  | "uncertain";

export type ResearchQuest = {
  quest_id: string;
  thread_id: string;
  title: string;
  topic: string;
  scope: string | null;
  objective: string | null;
  domain: string;
  stage: ResearchStage;
  status: ResearchQuestStatus;
  academic_project_id: string | null;
  experiment_project_ids: string[];
  metadata: ResearchQuestMetadata;
  created_at: string;
  updated_at: string;
};

export type ResearchLedgerEntry = {
  entry_id: string;
  quest_id: string;
  stage: ResearchStage;
  event_type: string;
  summary: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  artifacts: string[];
  tool_name: string | null;
  model_name: string | null;
  error: string | null;
  gate_decision: string | null;
  created_at: string;
};

export type ResearchGate = {
  gate_id: string;
  quest_id: string;
  stage: ResearchStage;
  gate_type: string;
  status: GateStatus;
  decision: string | null;
  reason: string | null;
  required: boolean;
  created_at: string;
  decided_at: string | null;
};

export type ClaimEvidenceRecord = {
  claim_id: string;
  quest_id: string;
  claim: string;
  paper_id: string | null;
  source_title: string | null;
  locator: string | null;
  snippet: string | null;
  quote: string | null;
  support_status: SupportStatus;
  confidence: number;
  artifact_path: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type NoveltyCheckRecord = {
  check_id: string;
  quest_id: string;
  idea: string;
  overlap_risk: "low" | "medium" | "high";
  closest_papers: Record<string, unknown>[];
  hypotheses: string[];
  minimum_experiment: string | null;
  decision: string;
  created_at: string;
};

export type ExperimentBranchRecord = {
  branch_id: string;
  quest_id: string;
  experiment_project_id: string | null;
  parent_branch_id: string | null;
  name: string;
  branch_type: string;
  status: "planned" | "running" | "completed" | "failed" | "skipped";
  priority: number;
  seed: number | null;
  metrics: Record<string, unknown>;
  artifact_paths: string[];
  failure_summary: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ManuscriptSectionRecord = {
  section_id: string;
  quest_id: string;
  section_key: string;
  title: string;
  content: string;
  claim_ids: string[];
  artifact_paths: string[];
  status: string;
  created_at: string;
  updated_at: string;
};

export type ReviewerReportRecord = {
  report_id: string;
  quest_id: string;
  stage: ResearchStage;
  reviewer_profile: string;
  score: number;
  verdict: "pass" | "revise" | "block";
  findings: string[];
  required_actions: string[];
  created_at: string;
};

export type ResearchQuestSnapshot = {
  quest: ResearchQuest;
  ledger: ResearchLedgerEntry[];
  gates: ResearchGate[];
  evidence: ClaimEvidenceRecord[];
  novelty_checks: NoveltyCheckRecord[];
  experiment_branches: ExperimentBranchRecord[];
  manuscript_sections: ManuscriptSectionRecord[];
  reviewer_reports: ReviewerReportRecord[];
};

export type CreateResearchQuestRequest = {
  thread_id: string;
  topic: string;
  title?: string;
  scope?: string;
  objective?: string;
  domain?: string;
  metadata?: Record<string, unknown>;
};

export type AdvanceResearchQuestRequest = {
  target_stage?: ResearchStage;
  inputs?: Record<string, unknown>;
  artifacts?: string[];
  tool_name?: string;
  model_name?: string;
};

export type ResearchAdvanceResult = {
  quest: ResearchQuest;
  advanced: boolean;
  blocked: boolean;
  required_gate: ResearchGate | null;
  ledger_entry: ResearchLedgerEntry | null;
  generated: Record<string, unknown>;
};
