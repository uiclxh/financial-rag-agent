const release = {
  version: "1.0.0",
  runId: "20260505T154304Z",
  benchmarkSize: 60,
  chunks: 52,
  missingMetadata: 0,
  companies: ["3M", "AMD", "Adobe", "Amcor", "Best Buy", "Boeing", "PepsiCo", "Pfizer"],
  metrics: [
    ["Recall@5", 0.914],
    ["Recall@10", 1.0],
    ["Question Recall@10", 1.0],
    ["Strict Precision@10", 0.116],
    ["Relaxed Precision@10", 0.42],
    ["Gold Page Hit@10", 1.0],
    ["Wrong Company", 0.0],
    ["Wrong Year", 0.0]
  ],
  completed: [
    "Downloaded FinanceBench open-source QA and SEC metadata",
    "Cleaned FinanceBench evidence pages into P0 chunks",
    "Aligned ticker, CIK, filing type, fiscal year, filing date, page, and section metadata",
    "Built BM25 lexical retrieval baseline",
    "Generated retrieval metrics and Markdown report",
    "Recorded reproducible run commands"
  ],
  deferred: [
    "Answer generation",
    "Claim extraction",
    "Citation verification",
    "Hallucination and faithfulness scoring",
    "Vector retrieval and reranking",
    "Valuation workflows"
  ],
  nextSteps: [
    "Add vector retrieval and reranking in Week 2",
    "Review low recall@5 cases before changing prompts",
    "Keep metadata filters visible in every per-question trace"
  ]
};

function pct(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

setText("run-id", release.runId);
setText("benchmark-size", `${release.benchmarkSize} questions`);
setText("chunk-count", `${release.chunks}`);
setText("missing-metadata", `${release.missingMetadata}`);

const metricGrid = document.getElementById("metrics");
release.metrics.forEach(([label, value]) => {
  const card = document.createElement("div");
  card.className = "metric";
  card.innerHTML = `<span>${label}</span><strong>${pct(value)}</strong>`;
  metricGrid.appendChild(card);
});

const companies = document.getElementById("companies");
release.companies.forEach((company) => {
  const pill = document.createElement("span");
  pill.textContent = company;
  companies.appendChild(pill);
});

const completed = document.getElementById("completed-list");
release.completed.forEach((item) => {
  const li = document.createElement("li");
  li.textContent = item;
  completed.appendChild(li);
});

const deferred = document.getElementById("deferred-list");
release.deferred.forEach((item) => {
  const li = document.createElement("li");
  li.textContent = item;
  deferred.appendChild(li);
});

const steps = document.getElementById("next-steps");
release.nextSteps.forEach((item) => {
  const li = document.createElement("li");
  li.textContent = item;
  steps.appendChild(li);
});

