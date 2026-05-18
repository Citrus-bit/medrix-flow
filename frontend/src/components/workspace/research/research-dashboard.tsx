"use client";

import {
  ArrowRightIcon,
  CheckCircle2Icon,
  FileTextIcon,
  FlaskConicalIcon,
  GitBranchIcon,
  LibraryIcon,
  PlusIcon,
  ShieldCheckIcon,
} from "lucide-react";
import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useAdvanceResearchQuest,
  useCreateResearchQuest,
  useDecideResearchGate,
  useResearchQuest,
  useResearchQuests,
} from "@/core/research";
import type {
  ClaimEvidenceRecord,
  ResearchGate,
  ResearchQuest,
  ResearchQuestSnapshot,
  ResearchStage,
} from "@/core/research";

const STAGES: ResearchStage[] = [
  "intake",
  "literature",
  "novelty_check",
  "evidence_verified",
  "experiment_planned",
  "experiment_running",
  "results_synthesized",
  "manuscript_draft",
  "review",
  "revision",
  "final_bundle",
];

const stageLabels: Record<ResearchStage, string> = {
  intake: "Intake",
  literature: "Literature",
  novelty_check: "Novelty",
  evidence_verified: "Evidence",
  experiment_planned: "Experiment plan",
  experiment_running: "Experiment run",
  results_synthesized: "Results",
  manuscript_draft: "Manuscript",
  review: "Review",
  revision: "Revision",
  final_bundle: "Final bundle",
};

function stageIndex(stage: ResearchStage) {
  return STAGES.indexOf(stage);
}

function statusVariant(status: string): "default" | "secondary" | "outline" | "destructive" {
  if (status === "completed" || status === "approved" || status === "supported" || status === "pass") {
    return "default";
  }
  if (status === "blocked" || status === "rejected" || status === "unsupported" || status === "block") {
    return "destructive";
  }
  if (status === "pending" || status === "revise") {
    return "secondary";
  }
  return "outline";
}

function compactDate(value: string) {
  if (!value) return "";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function confidenceLabel(value: number) {
  return `${Math.round(value * 100)}%`;
}

function uniqueArtifacts(snapshot: ResearchQuestSnapshot | null) {
  if (!snapshot) return [];
  return Array.from(
    new Set([
      ...(Array.isArray(snapshot.quest.metadata.final_bundle_artifacts)
        ? snapshot.quest.metadata.final_bundle_artifacts.filter((artifact): artifact is string => typeof artifact === "string")
        : []),
      ...(Array.isArray(snapshot.quest.metadata.draft_artifacts)
        ? snapshot.quest.metadata.draft_artifacts.filter((artifact): artifact is string => typeof artifact === "string")
        : []),
      ...snapshot.ledger.flatMap((entry) => entry.artifacts),
      ...snapshot.experiment_branches.flatMap((branch) => branch.artifact_paths),
      ...snapshot.manuscript_sections.flatMap((section) => section.artifact_paths),
    ]),
  ).filter(Boolean);
}

function researchDeliveryStatus(snapshot: ResearchQuestSnapshot) {
  const draftReadyAt = typeof snapshot.quest.metadata.draft_ready_at === "string"
    ? snapshot.quest.metadata.draft_ready_at
    : null;
  const finalBundleReadyAt = typeof snapshot.quest.metadata.final_bundle_ready_at === "string"
    ? snapshot.quest.metadata.final_bundle_ready_at
    : null;
  const finalBundleExportMessage = typeof snapshot.quest.metadata.final_bundle_export_message === "string"
    ? snapshot.quest.metadata.final_bundle_export_message
    : null;
  const finalBundleExportStatus = snapshot.quest.metadata.final_bundle_export_status;
  const finalizationRunId = typeof snapshot.quest.metadata.finalization_run_id === "string"
    ? snapshot.quest.metadata.finalization_run_id
    : null;
  if (finalBundleExportStatus === "passed") {
    return {
      label: "Final PDF ready",
      detail: finalBundleReadyAt ? `Exported ${compactDate(finalBundleReadyAt)}` : "PDF export passed",
      variant: "default" as const,
    };
  }
  if (finalBundleExportStatus === "blocked" || finalBundleExportStatus === "error") {
    return {
      label: "Final bundle blocked",
      detail: finalBundleExportMessage ?? "Final PDF export did not complete",
      variant: "destructive" as const,
    };
  }
  if (snapshot.quest.stage === "final_bundle" || snapshot.quest.status === "completed") {
    return {
      label: "Final bundle ready",
      detail: draftReadyAt ? `Draft created ${compactDate(draftReadyAt)}` : "Final audits completed",
      variant: "default" as const,
    };
  }
  if (draftReadyAt && finalizationRunId) {
    return {
      label: "Finalizing",
      detail: `Draft ready ${compactDate(draftReadyAt)} · run ${finalizationRunId}`,
      variant: "secondary" as const,
    };
  }
  if (draftReadyAt || snapshot.manuscript_sections.some((section) => section.status === "draft_ready")) {
    return {
      label: "Draft ready",
      detail: draftReadyAt ? `Created ${compactDate(draftReadyAt)}` : "Editable manuscript sections available",
      variant: "secondary" as const,
    };
  }
  return {
    label: "In progress",
    detail: "Draft has not been generated yet",
    variant: "outline" as const,
  };
}

function nextStageLabel(stage: ResearchStage) {
  const index = stageIndex(stage);
  if (index < 0 || index === STAGES.length - 1) return "Complete";
  return `Advance to ${stageLabels[STAGES[index + 1]!]}`;
}

function EvidenceRow({ item }: { item: ClaimEvidenceRecord }) {
  return (
    <tr className="border-b last:border-0">
      <td className="max-w-[22rem] px-3 py-3 align-top text-sm">
        <div className="font-medium">{item.claim}</div>
        {item.snippet ? (
          <div className="text-muted-foreground mt-1 line-clamp-2 text-xs">
            {item.snippet}
          </div>
        ) : null}
      </td>
      <td className="px-3 py-3 align-top text-sm">
        <div>{item.source_title ?? "Unattached source"}</div>
        <div className="text-muted-foreground text-xs">{item.locator ?? item.paper_id ?? "No locator"}</div>
      </td>
      <td className="px-3 py-3 align-top">
        <Badge variant={statusVariant(item.support_status)}>{item.support_status}</Badge>
      </td>
      <td className="px-3 py-3 align-top text-sm">{confidenceLabel(item.confidence)}</td>
    </tr>
  );
}

export function ResearchQuestSnapshotView({
  snapshot,
  isAdvancing = false,
  onAdvance,
  onApproveGate,
}: {
  snapshot: ResearchQuestSnapshot | null;
  isAdvancing?: boolean;
  onAdvance?: () => void;
  onApproveGate?: (gate: ResearchGate) => void;
}) {
  const pendingGate = snapshot?.gates.find((gate) => gate.status === "pending") ?? null;
  const artifacts = uniqueArtifacts(snapshot);

  if (!snapshot) {
    return (
      <div className="text-muted-foreground flex h-64 items-center justify-center text-sm">
        Select or create a research quest.
      </div>
    );
  }

  const { quest } = snapshot;
  const currentStageIndex = stageIndex(quest.stage);
  const deliveryStatus = researchDeliveryStatus(snapshot);

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <div className="border-b px-6 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="truncate text-xl font-semibold">{quest.title}</h1>
              <Badge variant={statusVariant(quest.status)}>{quest.status}</Badge>
              <Badge variant="outline">{stageLabels[quest.stage]}</Badge>
              <Badge variant={deliveryStatus.variant}>{deliveryStatus.label}</Badge>
            </div>
            <p className="text-muted-foreground mt-1 max-w-3xl text-sm">
              {quest.topic}
            </p>
            <p className="text-muted-foreground mt-1 text-xs">{deliveryStatus.detail}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {pendingGate ? (
              <Button
                variant="outline"
                onClick={() => onApproveGate?.(pendingGate)}
                disabled={isAdvancing}
              >
                <ShieldCheckIcon className="size-4" />
                Approve {pendingGate.gate_type}
              </Button>
            ) : null}
            <Button onClick={onAdvance} disabled={isAdvancing || quest.stage === "final_bundle"}>
              <ArrowRightIcon className="size-4" />
              {nextStageLabel(quest.stage)}
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(20rem,0.8fr)]">
          <Card className="rounded-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <CheckCircle2Icon className="size-4" />
                Quest Timeline
              </CardTitle>
              <CardDescription>
                Stage gates keep the assistant auditable and interruptible.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                {STAGES.map((stage, index) => {
                  const reached = index <= currentStageIndex;
                  const active = stage === quest.stage;
                  return (
                    <div
                      key={stage}
                      className={[
                        "rounded-md border p-3 text-sm",
                        active ? "border-primary bg-primary/5" : "",
                        reached && !active ? "bg-muted/40" : "",
                      ].join(" ")}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">{stageLabels[stage]}</span>
                        <Badge variant={active ? "default" : reached ? "secondary" : "outline"}>
                          {active ? "current" : reached ? "done" : "queued"}
                        </Badge>
                      </div>
                      <div className="text-muted-foreground mt-1 text-xs">
                        {index + 1}. {stage}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <ShieldCheckIcon className="size-4" />
                Gates
              </CardTitle>
              <CardDescription>Human approvals for risky transitions.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {snapshot.gates.length === 0 ? (
                <div className="text-muted-foreground text-sm">No gates created yet.</div>
              ) : (
                snapshot.gates.map((gate) => (
                  <div key={gate.gate_id} className="rounded-md border p-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="font-medium">{gate.gate_type}</div>
                      <Badge variant={statusVariant(gate.status)}>{gate.status}</Badge>
                    </div>
                    <div className="text-muted-foreground mt-1 text-xs">
                      {stageLabels[gate.stage]} · {gate.reason ?? "No reason recorded"}
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="evidence" className="mt-6">
          <TabsList>
            <TabsTrigger value="evidence">
              <LibraryIcon />
              Evidence
            </TabsTrigger>
            <TabsTrigger value="experiments">
              <GitBranchIcon />
              Experiments
            </TabsTrigger>
            <TabsTrigger value="manuscript">
              <FileTextIcon />
              Manuscript
            </TabsTrigger>
            <TabsTrigger value="review">
              <FlaskConicalIcon />
              Review
            </TabsTrigger>
          </TabsList>

          <TabsContent value="evidence" className="mt-4" forceMount>
            <Card className="rounded-lg">
              <CardHeader>
                <CardTitle className="text-base">Claim Evidence Map</CardTitle>
                <CardDescription>
                  Every manuscript-level claim should resolve to evidence or remain explicitly unsupported.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {snapshot.evidence.length === 0 ? (
                  <div className="text-muted-foreground text-sm">No evidence claims yet.</div>
                ) : (
                  <div className="overflow-x-auto rounded-md border">
                    <table className="w-full min-w-[48rem] border-collapse">
                      <thead className="bg-muted/60 text-left text-xs">
                        <tr>
                          <th className="px-3 py-2 font-medium">Claim</th>
                          <th className="px-3 py-2 font-medium">Source</th>
                          <th className="px-3 py-2 font-medium">Status</th>
                          <th className="px-3 py-2 font-medium">Confidence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {snapshot.evidence.map((item) => (
                          <EvidenceRow key={item.claim_id} item={item} />
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="experiments" className="mt-4" forceMount>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {snapshot.experiment_branches.length === 0 ? (
                <Card className="rounded-lg">
                  <CardContent className="text-muted-foreground pt-6 text-sm">
                    No experiment branches yet.
                  </CardContent>
                </Card>
              ) : (
                snapshot.experiment_branches.map((branch) => (
                  <Card key={branch.branch_id} className="rounded-lg">
                    <CardHeader>
                      <CardTitle className="text-base">{branch.name}</CardTitle>
                      <CardDescription>
                        {branch.branch_type} · priority {branch.priority.toFixed(2)}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3 text-sm">
                      <Badge variant={statusVariant(branch.status)}>{branch.status}</Badge>
                      <div className="text-muted-foreground">
                        Seed: {branch.seed ?? "not set"}
                      </div>
                      <div className="rounded-md bg-muted/50 p-2 text-xs">
                        Metrics: {Object.keys(branch.metrics).join(", ") || "pending"}
                      </div>
                      {branch.failure_summary ? (
                        <div className="text-destructive text-xs">{branch.failure_summary}</div>
                      ) : null}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          <TabsContent value="manuscript" className="mt-4" forceMount>
            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
              <Card className="rounded-lg">
                <CardHeader>
                  <CardTitle className="text-base">Manuscript Workspace</CardTitle>
                  <CardDescription>
                    {deliveryStatus.label} · {deliveryStatus.detail}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {snapshot.manuscript_sections.length === 0 ? (
                    <div className="text-muted-foreground text-sm">No manuscript sections yet.</div>
                  ) : (
                    snapshot.manuscript_sections.map((section) => (
                      <div key={section.section_id} className="rounded-md border p-3">
                        <div className="flex items-center justify-between gap-2">
                          <div className="font-medium">{section.title}</div>
                          <Badge variant="outline">{section.status}</Badge>
                        </div>
                        <div className="text-muted-foreground mt-1 text-xs">
                          {section.claim_ids.length} linked claim(s) · {section.artifact_paths.length} artifact(s)
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
              <Card className="rounded-lg">
                <CardHeader>
                  <CardTitle className="text-base">Artifact Bundle</CardTitle>
                  <CardDescription>Files linked through ledger, results, and manuscript sections.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {artifacts.length === 0 ? (
                    <div className="text-muted-foreground text-sm">No artifacts attached.</div>
                  ) : (
                    artifacts.map((artifact) => (
                      <div key={artifact} className="truncate rounded-md border px-3 py-2 text-sm">
                        {artifact}
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="review" className="mt-4" forceMount>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {snapshot.reviewer_reports.length === 0 ? (
                <Card className="rounded-lg">
                  <CardContent className="text-muted-foreground pt-6 text-sm">
                    No reviewer scorecards yet.
                  </CardContent>
                </Card>
              ) : (
                snapshot.reviewer_reports.map((report) => (
                  <Card key={report.report_id} className="rounded-lg">
                    <CardHeader>
                      <CardTitle className="text-base">{report.reviewer_profile}</CardTitle>
                      <CardDescription>{compactDate(report.created_at)}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3 text-sm">
                      <div className="flex items-center justify-between">
                        <span>Score</span>
                        <span className="font-medium">{confidenceLabel(report.score)}</span>
                      </div>
                      <Badge variant={statusVariant(report.verdict)}>{report.verdict}</Badge>
                      <ul className="text-muted-foreground list-inside list-disc space-y-1 text-xs">
                        {report.findings.map((finding) => (
                          <li key={finding}>{finding}</li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function QuestList({
  quests,
  selectedQuestId,
  onSelect,
}: {
  quests: ResearchQuest[];
  selectedQuestId: string | null;
  onSelect: (questId: string) => void;
}) {
  return (
    <div className="space-y-2">
      {quests.map((quest) => (
        <button
          key={quest.quest_id}
          type="button"
          onClick={() => onSelect(quest.quest_id)}
          className={[
            "w-full rounded-md border px-3 py-2 text-left text-sm transition-colors",
            selectedQuestId === quest.quest_id ? "border-primary bg-primary/5" : "hover:bg-muted/60",
          ].join(" ")}
        >
          <div className="truncate font-medium">{quest.title}</div>
          <div className="text-muted-foreground mt-1 flex items-center justify-between gap-2 text-xs">
            <span>{stageLabels[quest.stage]}</span>
            <span>{compactDate(quest.updated_at)}</span>
          </div>
        </button>
      ))}
    </div>
  );
}

export function ResearchDashboard() {
  const [selectedQuestId, setSelectedQuestId] = useState<string | null>(null);
  const [threadId, setThreadId] = useState("research-thread");
  const [topic, setTopic] = useState("");
  const questsQuery = useResearchQuests();
  const snapshotQuery = useResearchQuest(selectedQuestId);
  const createQuest = useCreateResearchQuest();
  const advanceQuest = useAdvanceResearchQuest();
  const decideGate = useDecideResearchGate();

  const quests = useMemo(() => questsQuery.data ?? [], [questsQuery.data]);
  const snapshot = snapshotQuery.data ?? null;
  const isBusy = createQuest.isPending || advanceQuest.isPending || decideGate.isPending;

  useEffect(() => {
    if (!selectedQuestId && quests.length > 0) {
      setSelectedQuestId(quests[0]!.quest_id);
    }
  }, [quests, selectedQuestId]);

  const latestLedgerSummary = useMemo(() => {
    const entries = snapshot?.ledger ?? [];
    return entries.at(-1)?.summary ?? "No lifecycle event recorded yet.";
  }, [snapshot]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedTopic = topic.trim();
    const normalizedThread = threadId.trim();
    if (!normalizedTopic || !normalizedThread) {
      toast.error("Thread ID and topic are required");
      return;
    }
    try {
      const quest = await createQuest.mutateAsync({
        thread_id: normalizedThread,
        topic: normalizedTopic,
      });
      setSelectedQuestId(quest.quest_id);
      setTopic("");
      toast.success("Research quest created");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create research quest");
    }
  }

  async function handleAdvance() {
    if (!snapshot) return;
    try {
      const result = await advanceQuest.mutateAsync({ questId: snapshot.quest.quest_id });
      if (result.blocked) {
        toast.warning("Human gate required");
      } else {
        toast.success(`Advanced to ${stageLabels[result.quest.stage]}`);
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to advance research quest");
    }
  }

  async function handleApproveGate(gate: ResearchGate) {
    try {
      await decideGate.mutateAsync({
        questId: gate.quest_id,
        stage: gate.stage,
        gateType: gate.gate_type,
        status: "approved",
        reason: "Approved from Research dashboard",
      });
      toast.success("Gate approved");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to approve gate");
    }
  }

  return (
    <div className="flex size-full min-h-0">
      <aside className="bg-background hidden w-80 shrink-0 border-r p-4 lg:block">
        <div className="mb-4">
          <h2 className="text-base font-semibold">Research Projects</h2>
          <p className="text-muted-foreground mt-1 text-sm">
            Persistent quests with evidence, gates, experiments, and review.
          </p>
        </div>
        <form className="mb-4 space-y-2" onSubmit={handleCreate}>
          <Input
            value={threadId}
            onChange={(event) => setThreadId(event.target.value)}
            placeholder="Thread ID"
            aria-label="Thread ID"
          />
          <Input
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Research topic"
            aria-label="Research topic"
          />
          <Button className="w-full" type="submit" disabled={isBusy}>
            <PlusIcon className="size-4" />
            New research quest
          </Button>
        </form>
        {questsQuery.isLoading ? (
          <div className="text-muted-foreground text-sm">Loading research quests...</div>
        ) : (
          <QuestList quests={quests} selectedQuestId={selectedQuestId} onSelect={setSelectedQuestId} />
        )}
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <div className="border-b px-6 py-3 lg:hidden">
          <form className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]" onSubmit={handleCreate}>
            <Input
              value={threadId}
              onChange={(event) => setThreadId(event.target.value)}
              placeholder="Thread ID"
              aria-label="Thread ID"
            />
            <Input
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="Research topic"
              aria-label="Research topic"
            />
            <Button type="submit" disabled={isBusy}>
              <PlusIcon className="size-4" />
              New
            </Button>
          </form>
        </div>
        {snapshotQuery.isLoading ? (
          <div className="text-muted-foreground flex h-64 items-center justify-center text-sm">
            Loading research quest...
          </div>
        ) : (
          <>
            {snapshot ? (
              <div className="text-muted-foreground border-b px-6 py-2 text-xs">
                Latest ledger: {latestLedgerSummary}
              </div>
            ) : null}
            <ResearchQuestSnapshotView
              snapshot={snapshot}
              isAdvancing={isBusy}
              onAdvance={handleAdvance}
              onApproveGate={handleApproveGate}
            />
          </>
        )}
      </main>
    </div>
  );
}
