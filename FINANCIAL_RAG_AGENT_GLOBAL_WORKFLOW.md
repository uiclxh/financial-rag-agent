# Financial RAG Agent Global Workflow v2.1

本文档定义一个面向公司财报、风险因素、现金流与估值假设的评估型 RAG Agent 构建规则。v2.1 的定位是：**保留金融 RAG 的关键安全线，但按阶段落地，避免第一版 MVP 被企业级规范拖慢。**

系统目标不是“能聊天”，而是可审计、可复现、可量化评估：

- `citation accuracy`: 引用是否支持对应 claim。
- `hallucination rate`: 回答中有多少 material claim 无证据、证据冲突或把假设说成事实。
- `answer faithfulness`: 回答是否由检索证据支撑。
- `retrieval precision / recall`: 检索结果是否取回正确证据，并减少噪声。

---

## 1. 总原则

### 1.1 先评估，后 Agent

第一阶段必须先建立离线评估闭环，不先做复杂聊天 UI 或 autonomous agent。

```text
fixed benchmark questions
  -> fixed document corpus
  -> ingestion
  -> hybrid retrieval
  -> cited answer generation
  -> claim-level verification
  -> metrics report
  -> failure review
```

只有当系统能稳定输出指标，并能解释失败原因后，才加入多步 agent planning。

### 1.2 Evidence First

所有回答都必须从 evidence 出发。系统不得凭模型常识回答公司财务事实、风险因素、现金流数字或估值假设。

每个 `material claim` 必须绑定 citation。MVP 阶段 citation 可以是：

```text
source document + page + section + paragraph_id / table_row_id
```

成熟阶段再升级为：

```text
source document + page + section + span_start / span_end / bounding_box
```

如果证据不足，系统必须返回结构化拒答或部分回答，而不是补全缺失事实。

### 1.3 区分事实、计算与假设

系统必须严格区分：

- `disclosed_fact`: 公司 filing、XBRL、官方年报或投资者关系披露中的事实。
- `calculated_metric`: 由披露数据经确定性公式计算得到的指标。
- `user_assumption`: 用户显式提供的估值假设。
- `external_estimate`: 授权外部数据源或分析师一致预期。
- `model_scenario`: 模型生成的情景假设，必须明确标注为 scenario。

估值问题中，模型不得把自己生成的假设描述为公司披露事实。

### 1.4 分层落地

v2.1 把规则分为四层：

```text
P0: MVP Must Have
P1: Financial QA Extension
P2: Advanced Governance
P3: Valuation System
```

P0 是第一版必须完成的最小闭环。P1-P3 是后续扩展，不应阻塞 MVP。

---

## 2. Implementation Priority

### 2.1 P0: MVP Must Have

第一版必须实现：

- fixed benchmark，例如 FinanceBench subset。
- fixed corpus，例如少量 SEC 10-K / 10-Q。
- 基础 metadata：company、ticker、CIK、filing type、fiscal year、page、section。
- BM25 + vector hybrid retrieval。
- reranker。
- paragraph-level 或 table-row-level citation。
- material claim extraction。
- claim-level citation verification。
- hallucination / unsupported / uncited claim metrics。
- retrieval recall@k。
- wrong company / wrong year rate。
- failure review report。
- config snapshot。
- reproducible run command。

P0 暂不强制：

- true `span_start` / `span_end` citation。
- 任意 PDF table extraction。
- 完整 XBRL concept mapping。
- valuation route。
- confidence calibration。
- formal human audit workflow。
- amended filing / restatement handling。
- permission-aware retrieval，除非 corpus 包含非公开数据。
- conflict resolution route。
- production dashboard。

### 2.2 P1: Financial QA Extension

第二阶段加入：

- verified table extraction。
- 可验证的 XBRL fact extraction。
- deterministic calculator。
- numeric error metrics。
- unit / scale / sign error metrics。
- period mismatch metrics。
- cash flow route。
- calculation input citation。

P1 的规则是：如果没有 XBRL 或人工验证表格，则 financial calculation route 只能做实验，不得作为可靠功能展示。

### 2.3 P2: Advanced Governance

第三阶段加入：

- permission-aware retrieval。
- amended filing policy。
- restatement handling。
- conflicting evidence policy。
- source hierarchy enforcement。
- targeted human audit workflow。
- basic confidence scoring。
- trace dashboard。

如果系统包含内部笔记、授权第三方数据、用户上传私密文档，则 permission-aware retrieval 从 P2 提前为 P0。

### 2.4 P3: Valuation System

估值系统最后实现：

- market data source。
- valuation date tracking。
- assumption management。
- DCF / multiple model。
- sensitivity table。
- valuation timestamp。
- valuation audit trail。

P0 不做实际估值输出，只允许识别估值假设缺失并拒答或要求用户补充。

---

## 3. Material Claim Definition

`material claim` 是任何可能影响投资、信用、估值、风险判断，或描述具体公司事实的陈述。

Material claims 包括：

- 任何公司特定事实。
- 任何财务数字、百分比、比率、增长率、现金流、利润率、债务、股数、市值或每股价值。
- 任何 fiscal year、quarter、period、date 或同比/环比比较。
- 任何风险因素总结、风险排序、风险重要性判断。
- 任何经营表现原因解释。
- 任何 liquidity、profitability、leverage、solvency、cash flow、growth、margin、risk exposure 相关判断。
- 任何估值假设、估值输出、target price、fair value、undervalued / overvalued 判断。
- 任何基于多个证据合成出的结论。

Non-material claims 包括：

- 结构性过渡句。
- 通用公式解释，不包含公司特定数据或结论。
- UI 文案。
- 与公司事实无关的免责声明。

Claim 必须足够 atomic，使 verifier 能判断它是否被 evidence 支持。一个 claim 不应混合多个公司、年份、指标或因果解释，除非明确标记为 multi-hop claim。

---

## 4. Core Metric Definitions

### 4.1 Support Labels

P0 使用简化标签：

```text
fully_supported
partially_supported
unsupported
contradicted
not_enough_information
```

P1+ 增加金融细分标签：

```text
supported_but_incomplete
overgeneralized
wrong_period
wrong_entity
wrong_unit
wrong_scale
wrong_sign
```

`fully_supported` 要求 cited evidence 完整支持 claim，包括公司、期间、单位、方向、数字大小和关键限定条件。

### 4.2 Citation Accuracy

```text
citation_accuracy =
fully_supported_cited_claims / total_cited_claims
```

P0 中，citation 可以是 paragraph-level 或 table-row-level。P2+ 中，citation accuracy 应升级到 sentence-level 或 span-level。

### 4.3 Unsupported Claim Rate

```text
unsupported_claim_rate =
material_claims_labeled_unsupported_contradicted_or_not_enough_information / total_material_claims
```

P1+ 中，`wrong_period`、`wrong_entity`、`wrong_unit`、`wrong_scale`、`wrong_sign` 也计入 unsupported family。

### 4.4 Hallucination Rate

Hallucinated claim 是任何 material claim 出现以下情况：

- unsupported。
- contradicted。
- not enough information。
- wrong company / entity。
- wrong fiscal period / date。
- wrong unit / scale / currency。
- wrong sign。
- 把 assumption 说成 disclosed fact。
- 把 model scenario 说成 objective fair value。

```text
hallucination_rate =
hallucinated_material_claims / total_material_claims
```

### 4.5 Uncited Claim Rate

```text
uncited_claim_rate =
material_claims_without_citation / total_material_claims
```

### 4.6 Answer Faithfulness

默认定义：

```text
answer_faithfulness =
1 - unsupported_claim_rate
```

如果同时使用 Ragas、TruLens 或 DeepEval 的 faithfulness score，必须保留工具原始分数和本协议定义的 claim-level score。

### 4.7 Optional Advanced Metrics

以下指标不阻塞 MVP，进入 P2 后逐步加入：

```text
claim_atomicity_score
claim_overmerge_rate
claim_oversplit_rate
claim_type_accuracy
evidence_completeness
confidence_calibration_error
```

### 4.8 Metric Denominator Rules

所有指标必须明确是 evidence-level、claim-level 还是 question-level。

Retrieval recall：

```text
evidence_level_retrieval_recall@k =
required_gold_evidence_units_retrieved_in_top_k / total_required_gold_evidence_units

question_recall@k =
questions_with_all_required_gold_evidence_in_top_k / total_questions
```

P0 可以同时报告两者，但报告必须清楚标注使用的是 evidence-level 还是 question-level。

Gold page hit：

```text
gold_page_hit@k =
questions_where_top_k_contains_at_least_one_gold_page / total_questions

complete_gold_page_hit@k =
questions_where_top_k_contains_all_required_gold_pages / total_multi_evidence_questions
```

Wrong company rate：

```text
wrong_company_rate =
retrieved_evidence_units_with_wrong_company / total_retrieved_evidence_units

question_wrong_company_rate =
questions_with_at_least_one_wrong_company_evidence_in_top_k / total_questions
```

Wrong year rate：

```text
wrong_year_rate =
retrieved_evidence_units_with_wrong_fiscal_year / total_retrieved_evidence_units
```

A retrieved evidence unit counts as wrong year if the question specifies or implies a fiscal year, the evidence belongs to another fiscal year, and the evidence is not needed as supporting context.

Refusal accuracy：

```text
refusal_accuracy =
unanswerable_questions_correctly_refused_or_partially_answered / total_unanswerable_questions
```

False answer rate：

```text
false_answer_rate =
unanswerable_questions_that_received_substantive_unsupported_answer / total_unanswerable_questions
```

A substantive unsupported answer means the system provides a company-specific factual, financial, risk, or valuation claim even though required evidence is missing.

False refusal rate：

```text
false_refusal_rate =
answerable_questions_incorrectly_refused / total_answerable_questions
```

`false_refusal_rate` is optional in P0 and required in P2+.

### 4.9 Claim Grounding Pass Rate

Citation accuracy alone can be misleading because it only evaluates cited claims. If the system leaves difficult material claims uncited, citation accuracy may look high while answer faithfulness is poor.

P0 should also report：

```text
claim_grounding_pass_rate =
fully_supported_material_claims / total_material_claims
```

Definitions：

```text
fully_supported_material_claims:
material claims that have at least one valid citation and are labeled fully_supported

total_material_claims:
all material claims in the final answer, including cited and uncited claims
```

Interpretation：

```text
citation_accuracy measures whether cited claims are supported.
uncited_claim_rate measures how many material claims lack citation.
claim_grounding_pass_rate measures whether all material claims are actually grounded.
```

Recommended P0 reporting：

```text
citation_accuracy
uncited_claim_rate
claim_grounding_pass_rate
hallucination_rate
answer_faithfulness
```

---

## 5. 数据与 Benchmark 规则

### 5.1 推荐数据源

P0 首选：

- FinanceBench subset。
- 少量 SEC 10-K / 10-Q HTML 或 PDF。

### 5.1.1 P0 Benchmark Scope

第一版 benchmark 范围必须足够小，优先跑通闭环：

```text
companies: 5
filings: 1 annual 10-K per company
answerable_questions: 50
unanswerable_questions: 10
question_types: factual, risk_factor, simple_comparison
calculation: disabled unless numeric evidence is manually verified
valuation: refuse or ask for missing assumptions only
```

P0 不追求行业覆盖或全市场覆盖。第一版目标是暴露 retrieval、citation、claim verification 和 failure review 的问题。

#### P0 Company Selection Principles

P0 公司选择应暴露基础 retrieval 和 citation 问题，同时避免第一版被行业会计复杂度拖慢。

Recommended selection rules：

```text
companies: 5
industries: at least 3 industries
filing_type: 10-K only for the first MVP
company_size: prefer large public companies with clear SEC filings
avoid_first_mvp: banks, insurers, REITs, and highly regulated financial institutions unless the project specifically targets them
filing_style: include companies with different risk factor length and MD&A structure
```

Rationale：

```text
The first MVP should test retrieval, citation, claim verification, and refusal behavior.
It should not be dominated by industry-specific accounting complexity.
Banks, insurers, and REITs often have specialized statements, regulatory capital disclosures, and non-standard financial metrics, so they are better added after the baseline is stable.
```

#### P0 Simple Comparison Boundary

P0 只支持不需要未验证财务计算的 simple comparison。

Allowed P0 simple comparison types：

```text
narrative_comparison:
The filing explicitly states that a metric, risk, cost, demand, or revenue item increased, decreased, improved, or worsened.

manually_verified_numeric_comparison:
Both compared numbers are manually labeled as gold evidence, including company, fiscal year, metric, unit, scale, and source.
```

Not allowed in P0 unless numeric evidence is manually verified：

```text
multi-year growth calculation
margin calculation
free cash flow calculation
ratio calculation
quarter-to-year conversion
TTM calculation
cross-company numeric comparison
```

Example allowed：

```text
Question:
Did the company report that supply chain risk increased in FY2023?

Reason:
This can be answered from narrative evidence.
```

Example allowed only with manually verified numeric evidence：

```text
Question:
Did operating cash flow increase from FY2022 to FY2023?

Required evidence:
FY2022 operating cash flow
FY2023 operating cash flow
unit
scale
cash flow statement source
```

P1+ 补充：

- FinDER。
- FinQA。
- SEC EDGAR XBRL facts。
- 自建 unanswerable benchmark。

### 5.2 MVP Benchmark Item Schema

```json
{
  "question_id": "string",
  "question": "string",
  "company": "string",
  "ticker": "string",
  "cik": "string",
  "filing_type": "10-K",
  "fiscal_year": 2023,
  "question_type": ["factual", "risk_factor"],
  "gold_answer": "string",
  "gold_evidence": [
    {
      "evidence_id": "string",
      "role": "primary | supporting | calculation_input",
      "required": true,
      "document_id": "string",
      "page": 42,
      "section": "MD&A",
      "paragraph_id": "p12",
      "table_row_id": null,
      "text": "string"
    }
  ],
  "expected_behavior": "answer | partial_answer | refuse"
}
```

P2+ 可增加 `span_start`、`span_end`、`negative evidence`、`distractor evidence`、`label_version` 等字段。

### 5.3 Unanswerable Benchmark

P0 至少加入少量 unanswerable cases，建议占 10%-15%。P2 后提升到 20%-30%。

Unanswerable categories：

- missing fiscal year。
- missing company identifier。
- missing valuation assumption。
- requested fact not disclosed。
- requested forecast not available。
- requested valuation input not disclosed。
- question asks for management intention not disclosed。
- question asks for exact risk probability。
- question asks for peer comparison without peer corpus。
- question asks for latest market price without market data source。
- question asks for analyst consensus without licensed source。
- insufficient evidence after retrieval。

P0 metrics：

```text
refusal_accuracy
false_answer_rate
```

P2+ metrics：

```text
false_refusal_rate
missing_evidence_identification_accuracy
partial_answer_accuracy
```

### 5.4 Benchmark Governance

P0 要求：

- 每个 benchmark 固定版本。
- 每次 run 记录 dataset version。
- 失败案例允许标记 `benchmark_label_error`。

P2+ 增加：

```text
annotator_id
reviewer_id
label_version
evidence_completeness_status
ambiguity_status
last_reviewed_at
change_log
```

---

## 6. Ingestion 与 Evidence Integrity

### 6.1 MVP Document Chunk Schema

P0 每个 chunk 至少保留：

```json
{
  "chunk_id": "string",
  "document_id": "string",
  "company": "string",
  "ticker": "string",
  "cik": "string",
  "filing_type": "10-K",
  "fiscal_year": 2023,
  "filing_date": "2024-02-01",
  "section": "Risk Factors",
  "page": 12,
  "paragraph_id": "p12",
  "table_row_id": null,
  "source_type": "sec_html | annual_report_pdf",
  "text": "string"
}
```

P2+ 可增加：

```text
accession_number
document_version
amendment_status
permission_scope
source_url
parent_page_id
table_id
xbrl_tags
```

### 6.2 Citation Granularity Strategy

MVP citation requirement：

```text
source document + page + section + paragraph_id / table_row_id
```

Evaluation citation requirement：

```text
the cited evidence must contain the exact supporting sentence, paragraph, or table row
```

Advanced citation requirement：

```text
span_start / span_end / bounding box
```

P0 不强制真实字符 offset，因为 PDF 解析、HTML alignment 和表格跨页会显著增加早期成本。

### 6.3 Financial Numeric Evidence Strategy

P0：

- 不承诺任意 PDF table extraction。
- 如果没有 verified table 或 verified XBRL，不启用 financial calculation route。
- 可先手工标注 FinanceBench / 小样本中的 numeric evidence。

P1：

- 标准化财务数字优先使用 verified SEC XBRL。
- 财务报表展示值使用 SEC HTML tables 或人工验证表格。
- XBRL 与表格尽量 cross-check。

P3：

- PDF table extraction 只有在 table quality 达标后启用。

### 6.4 Financial Numeric Evidence Schema

P1+ numeric evidence unit 应保留：

```json
{
  "evidence_id": "string",
  "company": "string",
  "ticker": "string",
  "cik": "string",
  "filing_type": "10-K",
  "filing_date": "2024-02-01",
  "fiscal_year": 2023,
  "period_start": "2023-01-01",
  "period_end": "2023-12-31",
  "statement_type": "cash_flow_statement",
  "row_label": "Net cash provided by operating activities",
  "column_label": "Year ended December 31, 2023",
  "unit": "USD",
  "scale": "millions",
  "currency": "USD",
  "sign_convention": "parentheses_are_negative",
  "value_raw": "110,543",
  "value_normalized": 110543000000,
  "xbrl_concept": "NetCashProvidedByUsedInOperatingActivities",
  "source_type": "xbrl | html_table | verified_pdf_table",
  "page": 42
}
```

Financial evidence integrity rules：

- Parentheses negative values must be normalized。
- Units such as millions, thousands, shares in millions, percentages, and basis points must not be inferred without evidence。
- A financial number cannot be used in calculation unless period, unit, scale, currency, sign, row label, column label, and source are known。
- Three-month, six-month, nine-month, trailing-twelve-month, and year-ended periods must not be mixed without explicit conversion。

### 6.5 Ingestion Quality Gates

P0 gates：

```text
required_metadata_present_rate >= 0.95
page_number_available_rate >= 0.95
section_available_rate >= 0.90
```

P1 gates before calculation route：

```text
numeric_metadata_completeness_rate >= 0.95
verified_numeric_value_accuracy >= 0.98 on sampled calculation inputs
```

P3 gates before PDF table extraction production use：

```text
table_cell_accuracy >= 0.95
header_inheritance_accuracy >= 0.95
xbrl_fact_extraction_accuracy >= 0.98 for verified concepts
```

---

## 7. Retrieval Workflow

### 7.1 MVP Pipeline

```text
query normalization
  -> entity / period / section extraction
  -> metadata filters
  -> BM25 top 50
  -> vector top 50
  -> merge and deduplicate
  -> rerank top 20
  -> parent page / paragraph expansion
  -> final evidence
```

禁止只用 dense embedding。金融文档检索必须保留 BM25 或 lexical retrieval，因为年份、会计科目、公司名、ticker、表格名称经常依赖精确匹配。

### 7.2 Metadata Filters

P0 必须支持：

```text
company / ticker / CIK
fiscal year
filing type
section
page
```

P1+ 支持：

```text
period start / period end
statement type
row label
column label
source type
```

P2+ 支持：

```text
filing date
accession number
document version
amendment status
permission scope
```

### 7.3 Multi-Label Classification

P0 可以用简单规则或 LLM classifier 输出：

```json
{
  "question_types": ["risk_factor"],
  "classification_confidence": 0.86,
  "entities": [],
  "periods": [],
  "missing_slots": []
}
```

P0 不要求复杂 route planner，但必须支持多标签，不得把复杂问题强行压成单标签。

### 7.4 Retrieval Metrics

P0 metrics：

```text
recall@k
precision@k
gold_page_hit@k
wrong_company_rate
wrong_year_rate
```

Precision definition：

```text
retrieval_precision@k =
relevant_retrieved_evidence_units / k
```

A relevant evidence unit must satisfy:

```text
same company
correct fiscal year or period
correct filing type if specified
contains information needed to answer the question
or provides necessary supporting context
```

P0 同时报告两个版本：

```text
strict_precision@k:
only required gold evidence counts

relaxed_precision@k:
equivalent evidence or necessary supporting evidence also counts
```

如果一个 chunk 同公司但年份错误、同年份但 section 错误、或只是主题相似但不能支持回答，不得计入 relevant。

P1+ metrics：

```text
calculation_input_recall@k
complete_multi_evidence_recall@k
wrong_period_rate
```

P2+ metrics：

```text
gold_span_hit@k
wrong_document_version_rate
permission_violation_rate
```

---

## 8. Answer Generation Contract

### 8.1 MVP Structured Output

```json
{
  "question_id": "string",
  "answer": "string",
  "claims": [
    {
      "claim_id": "string",
      "claim": "string",
      "claim_type": "factual | comparison | risk_summary | calculation | assumption | refusal",
      "citation_ids": ["citation_id"],
      "confidence": "high | medium | low"
    }
  ],
  "citations": [
    {
      "citation_id": "string",
      "document_id": "string",
      "page": 42,
      "section": "MD&A",
      "paragraph_id": "p12",
      "table_row_id": null,
      "supporting_text": "string"
    }
  ],
  "insufficient_evidence": []
}
```

P1+ 增加 `calculations`。P2+ 增加 span offsets、document version、source hierarchy、permission decision。

### 8.2 Generation Prompt Rules

Generation prompt 必须包含：

```text
Use only the provided evidence.
Every material claim must cite evidence.
Do not use prior knowledge.
Do not infer missing numbers.
Do not invent valuation assumptions.
If evidence is insufficient, say so.
Preserve company, fiscal year, period, unit, scale, sign, and currency when available.
Do not present a scenario output as a disclosed fact.
The answer should be concise and claim-aligned.
Do not add broad financial commentary that is not directly required by the question.
```

### 8.3 Multi-Evidence Claim Rules

P0：

- Comparison claim should cite all compared periods if available。
- Risk summary claim should cite every risk category used in the summary。

P1：

- Calculation claim must cite every numeric input。
- Causal explanation must cite both performance change and management explanation, if the answer attributes causality。

P3：

- Valuation claim must cite all historical inputs and label all assumptions。

### 8.4 Insufficient Evidence Response

当无法完整回答时，返回：

```json
{
  "status": "insufficient_evidence | partially_answered | refused",
  "answerable_parts": [],
  "missing_evidence": [],
  "documents_searched": [],
  "retrieved_but_insufficient": [],
  "suggested_next_step": "string"
}
```

### 8.5 P0 Claim Extraction Rule

P0 不应只依赖 post-hoc claim extractor。Answer generator 必须在同一个 structured output 中显式输出 `answer`、`claims` 和 `citations`。

P0 claim extraction process：

```text
1. Generator produces answer + claims + citations in one structured output.
2. Each material claim in the answer must appear in the claims list.
3. A lightweight claim-auditor pass may check whether the answer contains material claims missing from the claims list.
4. Human spot checks should review whether the claims list covers all material claims in sampled cases.
```

Required P0 check：

```text
claim_list_coverage_check:
Does every material claim in the natural-language answer appear in the structured claims list?
```

If a material claim appears in the answer but not in the claims list, count it as：

```text
claim_extraction_error
uncited_claim
potential_hallucination depending on evidence support
```

Prompt requirement：

```text
Do not include any material claim in the answer unless it is also represented in the claims list and linked to citation_ids.
```

Optional metric：

```text
claim_list_coverage_rate =
material_claims_present_in_claims_list / material_claims_in_answer
```

---

## 9. Citation Verification

### 9.1 MVP Verifier

P0 verifier 包含两层：

1. Rule-based checks：

```text
citation_id exists
page / paragraph / table_row exists
company match
fiscal year match
filing type match when available
```

2. Semantic support check：

```text
claim + cited evidence -> support label
```

Semantic verifier 可以用 LLM 或 NLI model，但必须记录 verifier label 和 rationale。

### 9.2 P1 Financial Checks

P1 增加：

```text
unit match
scale match
currency match
sign match
period match
numeric exact match or tolerance check
```

### 9.3 Verification Label Examples

P0 verifier 必须使用以下判定样例校准：

| Claim | Evidence | Label | Reason |
|---|---|---|---|
| Revenue increased in 2023. | Revenue increased from X to Y in 2023. | fully_supported | 指标、方向、年份一致。 |
| Revenue increased mainly due to subscriptions. | Revenue increased due to subscriptions, partially offset by hardware decline. | partially_supported | 支持主要原因，但省略了 offset。 |
| Operating cash flow was $10 billion. | Evidence only shows net income was $10 billion. | unsupported | 指标不一致。 |
| Revenue decreased in 2023. | Evidence says revenue increased in 2023. | contradicted | 方向相反。 |
| WACC was 8%. | Filing contains no WACC disclosure. | not_enough_information | 证据缺失。 |

判定原则：

- 如果 citation 只支持 claim 的一部分，标记 `partially_supported`。
- 如果 evidence 与 claim 方向、数字、公司、期间或指标冲突，标记 `contradicted` 或 P1+ 的具体 wrong label。
- 如果 evidence 没有提供所需事实，不得用模型常识补足，标记 `not_enough_information`。
- 如果 claim 使用了未引用的限定词，例如 “mainly”、“strong”、“materially”、“reasonable”，verifier 必须检查 evidence 是否支持该限定词。

### 9.4 Human Review

P0 不设置 formal human audit workflow。每次 run 只要求人工抽查：

```text
20-30 failed cases
at least 5 cases per major question type when available
all obvious numeric failures
all high-confidence unsupported answers
```

P2+ 再引入正式 human audit metrics：

```text
verifier_agreement_rate
human_audit_pass_rate
false_supported_rate
false_unsupported_rate
```

---

## 10. Calculation Rules

### 10.1 Phase Scope

P0 不强制实现 calculation route。

P1 起，所有财务计算必须使用 deterministic arithmetic，例如 Python `Decimal` 或等价机制。

不允许：

```text
LLM mental math
uncited numeric inputs
unit inference without evidence
float-only financial arithmetic for reported metrics
```

### 10.2 Calculation Trace

P1 calculation output 必须包含：

```text
formula
input values
input citations
period start / period end
unit
scale
currency
sign convention
rounding rule
result
```

### 10.3 Tolerance and Rounding

默认 rounding：

```text
monetary value: nearest million unless source uses another scale
percentage: 2 decimal places
ratio: 2 decimal places
growth rate: 2 decimal places
per-share value: 2 decimal places
```

默认 tolerance：

```text
exact financial table value: 0 tolerance after normalization
calculated percentage: absolute tolerance <= 0.01 percentage point
calculated ratio: relative tolerance <= 0.1%
DCF output: evaluate formula/input correctness rather than one exact value unless all assumptions are fixed
```

---

## 11. Source Hierarchy and XBRL Strategy

### 11.1 Task-Specific Source Hierarchy

不要把 XBRL 简单当成所有任务的最高来源。

For standardized numeric facts：

```text
1. SEC XBRL facts when concept mapping is verified
2. SEC HTML filing tables
3. official annual report PDF tables
4. company investor relations release
5. licensed third-party data
```

For narrative disclosures and risk factors：

```text
1. SEC HTML filing text
2. official annual report PDF
3. company investor relations release
4. licensed third-party data
5. analyst reports / internal notes
```

For valuation assumptions：

```text
1. user-provided assumptions
2. licensed external estimate
3. clearly labeled model scenario
```

如果使用低权威来源，而更高权威来源存在，P2+ 必须解释原因。

### 11.2 XBRL / Table Strategy

P0：

- XBRL optional but recommended for standardized numeric facts。
- 如果 XBRL 未实现，financial calculation route 只能使用人工验证的 table values。

P1：

- Use XBRL for standardized facts when concept mapping is verified。
- Use SEC HTML tables for displayed statement values。
- Cross-check XBRL and table values when possible。

P3：

- Support PDF table extraction only after table quality gates are met。

---

## 12. Latest、Amended、Restatement 与 Conflict

这些规则不阻塞 P0，但必须作为接口预留。

### 12.1 Latest Filing

P0：

- 如果用户问 latest，必须输出实际使用的 filing type、fiscal year、filing date。

P2：

- Latest risk factors 同时检索 latest 10-K Item 1A 和 subsequent 10-Q risk factor updates。
- 如果 10-Q 声明 no material changes，必须同时引用 10-Q statement 和 prior 10-K Item 1A。

### 12.2 Amended Filing and Restatement

P0：

- 记录 filing date 和 document id。

P2：

- 如果 amended filing 存在，默认使用最新 amended filing，除非用户明确要求 original filing。
- 不得在同一答案中混用 original 和 amended filing，除非解释 amendment。

### 12.3 Conflicting Evidence

P0：

- 如果检索结果中明显出现冲突，回答应提示 evidence conflict，而不是强行给确定答案。

P2：

- 实现正式 conflict detection 和 conflict resolution metrics。

---

## 13. Valuation Rules

P0 不输出实际估值结论，只做假设识别和拒答。

如果用户问估值但缺少必要输入，系统必须说明缺失项：

```text
valuation date
market price source
shares outstanding source
net debt source
WACC assumption
terminal growth assumption
forecast period
currency
```

P3 才允许实际 valuation output。Valuation outputs must be framed as scenario outputs, not disclosed facts。

Required wording：

```text
Under the stated assumptions, the implied value is X. This is not a disclosed company fact. The result is sensitive to WACC, terminal growth, margin, FCF, and shares outstanding assumptions.
```

Agent 不得说：

```text
undervalued
overvalued
fair value
target price
```

除非 market price、valuation date、model assumptions、data sources、currency、shares outstanding source、net debt source 和 sensitivity table 全部明确可用。

---

## 14. Confidence Strategy

P0 不做正式 calibration，只输出规则型 confidence：

High confidence：

```text
retrieval hit required evidence
citation fully supported
no wrong company / wrong year
no obvious missing evidence
```

Medium confidence：

```text
evidence supports main claim
minor qualifier or evidence completeness issue
```

Low confidence：

```text
evidence incomplete
route classification uncertain
missing required input
possible conflict
```

P2+ 再评估：

```text
confidence_calibration_error
high_confidence_error_rate
low_confidence_refusal_rate
```

---

## 15. Evaluation Metrics and Gates

### 15.1 P0 Metrics

MVP 必须输出：

```text
retrieval_recall@k
retrieval_precision@k
gold_page_hit@k
wrong_company_rate
wrong_year_rate
citation_accuracy
claim_grounding_pass_rate
unsupported_claim_rate
uncited_claim_rate
hallucination_rate
answer_faithfulness
refusal_accuracy
false_answer_rate
```

### 15.2 P0 Gates

MVP development baseline gate：

```text
retrieval_recall@10 >= 0.70
gold_page_hit@10 >= 0.70
wrong_company_rate <= 0.03
wrong_year_rate <= 0.10
uncited_claim_rate <= 0.15
unsupported_claim_rate <= 0.20
hallucination_rate <= 0.15
required_metadata_present_rate >= 0.95
```

这些是开发基准，不是最终质量目标，更不是生产门槛。未达标时，优先修 ingestion、metadata、chunking、retrieval，不先调复杂 agent。

质量分级：

```text
P0 development gate:
hallucination_rate <= 0.15
unsupported_claim_rate <= 0.20

P1 demo gate:
hallucination_rate <= 0.10
unsupported_claim_rate <= 0.15

P2 research-quality gate:
hallucination_rate <= 0.05
unsupported_claim_rate <= 0.10

Production gate:
requires human review, route-specific thresholds, permission checks if needed, and stricter task-specific validation
```

### 15.3 P1 Metrics and Gates

Financial QA extension：

```text
calculation_input_recall@10 >= 0.90
numeric_error_rate <= 0.05
unit_error_rate <= 0.03
period_mismatch_rate <= 0.05
sign_error_rate <= 0.03
```

### 15.4 P2 Metrics and Gates

Advanced governance：

```text
permission_violation_rate = 0 if private or licensed data exists
amended_filing_resolution_accuracy >= 0.90 when evaluated
conflict_detection_rate >= 0.80 when evaluated
high_confidence_error_rate <= 0.05
```

### 15.5 P3 Metrics and Gates

Valuation system：

```text
assumption_mislabel_rate <= 0.01
uncited_input_rate = 0
sensitivity_present_rate >= 0.95
valuation_date_present_rate >= 0.95
```

---

## 16. Failure Review Protocol

每次 benchmark run 后，必须按以下顺序分析失败案例：

```text
1. Did ingestion preserve the required evidence?
2. Did metadata preserve company, year, filing type, page, and section?
3. Did retrieval find the gold evidence?
4. Did reranker keep relevant evidence in top k?
5. Did citation point to the right paragraph, table row, sentence, or span?
6. Did answer generator use the right evidence?
7. Did every material claim get cited?
8. Did verifier judge support correctly?
9. Was the question supposed to be refused or partially answered?
10. Was the gold label incomplete or ambiguous?
```

P1+ 增加：

```text
Did numeric evidence preserve unit, scale, sign, period, and row/column labels?
Did calculation use deterministic arithmetic and cited inputs?
```

失败归因标签：

```text
ingestion_error
chunking_error
metadata_error
retrieval_error
rerank_error
citation_error
claim_decomposition_error
generation_error
verification_error
refusal_error
calculation_error
benchmark_label_error
```

禁止把所有失败笼统归因于 “LLM hallucination”。

Fix order：

```text
1. metadata / ingestion errors
2. retrieval errors
3. reranking errors
4. citation selection errors
5. claim decomposition errors
6. generation errors
7. verifier errors
8. benchmark label errors
```

如果 metadata 或 ingestion 错误尚未修复，不应优先做 prompt engineering。

---

## 17. Observability and Trace

P0 trace 必须记录：

```json
{
  "run_id": "string",
  "question_id": "string",
  "query_raw": "string",
  "query_normalized": "string",
  "question_types": [],
  "metadata_filters": {},
  "retrieved_chunks": [],
  "reranked_chunks": [],
  "selected_citations": [],
  "generated_answer": {},
  "claims": [],
  "verification_results": [],
  "metrics": {},
  "latency_ms": 0,
  "cost_usd": 0,
  "config_snapshot": {}
}
```

P2+ trace 增加：

```text
permission_filters
document_version
amendment_status
calculation_trace
source_authority
model_versions
prompt_versions
confidence_signals
```

Trace 必须能从 final answer 回溯到 claim、citation、source document、retrieval score、reranker score、verifier label 和 config version。

---

## 18. Security and Governance

P0 如果只使用 public filings，可以暂不实现 permission-aware retrieval，但仍应在 schema 中预留 `source_type`。

如果包含以下任何数据，permission-aware retrieval 立即变为 P0：

```text
licensed third-party data
internal research notes
private company data
user uploaded documents
```

此时必须：

- 在 retrieval 和 reranking 前应用 permission filters。
- 禁止 unauthorized citation。
- 记录 document access logs。
- 输出 permission_violation_rate。

---

## 19. 推荐技术架构

第一版技术栈：

```text
Language: Python
RAG framework: LlamaIndex first, LangGraph later
API layer: FastAPI only after local scripts are stable
Vector DB: pgvector or local vector store for MVP
Keyword search: BM25 first, OpenSearch later
Evaluation: custom metrics first, Ragas / DeepEval optional
Storage: local filesystem first, object storage later
Dashboard: report markdown / CSV first, Streamlit later
```

MVP 不需要一开始部署完整服务器。建议先本地跑通：

```text
ingestion script
retrieval script
evaluation script
report builder
```

---

## 20. 推荐开发顺序

### Week 1: Retrieval Baseline

- 跑通 ingestion。
- 保留 basic metadata。
- 建 BM25 baseline。
- 输出 retrieval recall@k 和 failure report。

### Week 2: Hybrid Retrieval

- 加入 vector retrieval。
- 加入 reranker。
- 加入 metadata filters。
- 输出 wrong company / wrong year 分析。

### Week 3: Cited Answer Generation

- 加入 structured answer。
- 加入 material claim extraction。
- 加入 paragraph-level citation。
- 加入 basic verifier。

### Week 4: First Full Evaluation

- 加入 hallucination rate。
- 加入 unsupported claim rate。
- 加入 uncited claim rate。
- 加入 answer faithfulness。
- 输出第一份完整 evaluation report。

### Week 5: Financial Numeric QA

- 加入 cash flow numeric QA。
- 只使用 verified table / XBRL evidence。
- 加入 deterministic calculator。

### Week 6: Unanswerable and Refusal

- 加入 unanswerable benchmark。
- 加入 refusal metrics。
- 加入 partial answer schema。

### Week 7+

- XBRL 完整接入。
- table extraction。
- sentence / span-level offsets。
- latest filing resolution。
- amended filing。
- conflict detection。
- permission-aware retrieval。
- valuation route。
- dashboard。

---

## 21. MVP Command Contract

未来项目 CLI 建议遵守以下接口：

```bash
python -m src.ingestion.run --config configs/ingestion/financebench.yaml
python -m src.retrieval.index --config configs/retrieval/baseline.yaml
python -m src.evaluation.run --config configs/evaluation/financebench_baseline.yaml
python -m src.reports.build --run-id RUN_ID
```

每个命令必须可重复运行，并且不得依赖隐式 notebook 状态。

---

## 22. Definition of Done

P0 功能只有同时满足以下条件才算完成：

```text
has benchmark cases
has fixed corpus
has basic metadata
has retrieval metrics
has answer metrics
has citation metrics
has failure examples
has trace records
has config snapshot
has reproducible run command
```

P1+ 功能如果涉及财务数字，还必须满足：

```text
has verified numeric evidence
has calculation trace
has numeric / unit / period / sign metrics
has calculation regression threshold
```

P3 估值功能还必须满足：

```text
has explicit assumptions
has valuation date
has source for market data
has sensitivity table
has assumption mislabel check
```

如果没有评估报告，则不算完成。

---

## 23. Minimal Running Example

本章节给出一个最小可运行案例，作为 ingestion、retrieval、generation、verification 和 metrics 的共同对齐样例。

### 23.1 Benchmark Item

```json
{
  "question_id": "q001",
  "question": "What were the company's main risk factors in FY2023?",
  "company": "Example Company",
  "ticker": "EXM",
  "cik": "0000000000",
  "filing_type": "10-K",
  "fiscal_year": 2023,
  "question_type": ["risk_factor"],
  "expected_behavior": "answer",
  "gold_evidence": [
    {
      "evidence_id": "ev001",
      "document_id": "doc_2023_10k",
      "page": 12,
      "section": "Item 1A. Risk Factors",
      "paragraph_id": "p12",
      "table_row_id": null,
      "text": "The company faces risks related to supply chain disruption, customer concentration, and regulatory changes."
    }
  ]
}
```

### 23.2 Chunk Example

```json
{
  "chunk_id": "chunk_001",
  "document_id": "doc_2023_10k",
  "company": "Example Company",
  "ticker": "EXM",
  "cik": "0000000000",
  "filing_type": "10-K",
  "fiscal_year": 2023,
  "filing_date": "2024-02-01",
  "section": "Item 1A. Risk Factors",
  "page": 12,
  "paragraph_id": "p12",
  "table_row_id": null,
  "source_type": "sec_html",
  "text": "The company faces risks related to supply chain disruption, customer concentration, and regulatory changes."
}
```

### 23.3 Retrieved Evidence Example

```json
{
  "question_id": "q001",
  "retrieved_chunks": [
    {
      "chunk_id": "chunk_001",
      "rank": 1,
      "bm25_score": 12.4,
      "vector_score": 0.83,
      "reranker_score": 0.91,
      "is_gold_evidence": true
    }
  ]
}
```

### 23.4 Structured Answer

```json
{
  "question_id": "q001",
  "answer": "In FY2023, the company disclosed risks related to supply chain disruption, customer concentration, and regulatory changes.",
  "claims": [
    {
      "claim_id": "claim_001",
      "claim": "In FY2023, the company disclosed risks related to supply chain disruption, customer concentration, and regulatory changes.",
      "claim_type": "risk_summary",
      "citation_ids": ["cit_001"],
      "confidence": "high"
    }
  ],
  "citations": [
    {
      "citation_id": "cit_001",
      "document_id": "doc_2023_10k",
      "page": 12,
      "section": "Item 1A. Risk Factors",
      "paragraph_id": "p12",
      "table_row_id": null,
      "supporting_text": "The company faces risks related to supply chain disruption, customer concentration, and regulatory changes."
    }
  ],
  "insufficient_evidence": []
}
```

### 23.5 Verification Result

```json
{
  "claim_id": "claim_001",
  "citation_id": "cit_001",
  "support_label": "fully_supported",
  "rationale": "The cited paragraph explicitly lists the same three risk factors for FY2023."
}
```

### 23.6 Metrics Example

```text
retrieval_recall@10 = 1.0
strict_precision@10 = 0.1
gold_page_hit@10 = 1.0
citation_accuracy = 1.0
unsupported_claim_rate = 0.0
uncited_claim_rate = 0.0
hallucination_rate = 0.0
answer_faithfulness = 1.0
```

### 23.7 Failure Review Example

如果模型回答：

```text
The company's main FY2023 risks were supply chain disruption and cybersecurity threats.
```

但 evidence 只包含：

```text
supply chain disruption, customer concentration, and regulatory changes
```

则 failure labels：

```text
generation_error
citation_error
unsupported_claim_rate increases because cybersecurity threats are not supported
```

修复优先级：

```text
1. 检查 retrieval 是否取回了 cybersecurity evidence。
2. 如果没有，判断问题是否需要该 evidence。
3. 如果不需要，修 generation prompt，禁止添加未检索风险。
4. 如果 benchmark gold evidence 缺失，标记 benchmark_label_error。
```

### 23.8 Unanswerable Example

#### Benchmark Item

```json
{
  "question_id": "q002",
  "question": "What WACC did the company disclose in its FY2023 10-K?",
  "company": "Example Company",
  "ticker": "EXM",
  "cik": "0000000000",
  "filing_type": "10-K",
  "fiscal_year": 2023,
  "question_type": ["valuation", "unanswerable"],
  "expected_behavior": "refuse",
  "gold_evidence": []
}
```

#### Expected Answer

```json
{
  "question_id": "q002",
  "answer": "The FY2023 10-K evidence provided does not disclose a WACC. I cannot treat any WACC as a company-disclosed fact without an explicit source.",
  "claims": [
    {
      "claim_id": "claim_001",
      "claim": "The FY2023 10-K evidence provided does not disclose a WACC.",
      "claim_type": "refusal",
      "citation_ids": [],
      "confidence": "high"
    }
  ],
  "insufficient_evidence": [
    {
      "missing_evidence": "company-disclosed WACC",
      "reason": "WACC is not disclosed in the retrieved filing evidence."
    }
  ]
}
```

Metrics：

```text
refusal_accuracy = 1.0
false_answer_rate = 0.0
hallucination_rate = 0.0
```

Failure condition：

```text
If the system answers "The WACC was 8%" without evidence, count as:
false_answer
hallucinated_claim
assumption_mislabel_error
```

### 23.9 Partially Supported Example

Evidence：

```text
Revenue increased in FY2023 due to higher subscription revenue, partially offset by lower hardware sales.
```

Model claim：

```text
Revenue increased in FY2023 mainly due to higher subscription revenue.
```

Verification：

```json
{
  "claim_id": "claim_partial_001",
  "support_label": "partially_supported",
  "rationale": "The evidence supports higher subscription revenue as a driver, but the claim omits the offset from lower hardware sales and adds 'mainly' without explicit support."
}
```

Metric impact：

```text
citation_accuracy: this claim does not count as fully supported
unsupported_claim_rate: not counted as unsupported in P0 unless the omitted qualifier materially changes the answer
evidence completeness: should be reviewed in P2+
```

### 23.10 Contradicted Example

Evidence：

```text
Operating cash flow decreased from $12.0 billion in FY2022 to $10.0 billion in FY2023.
```

Model claim：

```text
Operating cash flow increased in FY2023.
```

Verification：

```json
{
  "claim_id": "claim_contra_001",
  "support_label": "contradicted",
  "rationale": "The evidence states that operating cash flow decreased, while the claim says it increased."
}
```

Metric impact：

```text
unsupported_claim_rate increases
hallucination_rate increases
citation_accuracy decreases
```

### 23.11 Wrong Citation Example

Question：

```text
What was the company's operating cash flow in FY2023?
```

Evidence cited：

```text
Net income was $10.0 billion in FY2023.
```

Model claim：

```text
Operating cash flow was $10.0 billion in FY2023.
```

Verification：

```json
{
  "claim_id": "claim_wrong_citation_001",
  "support_label": "unsupported",
  "rationale": "The cited evidence reports net income, not operating cash flow."
}
```

Failure labels：

```text
citation_error
generation_error
financial_metric_mismatch
```

---

## 24. MVP Evaluation Report Template

Each P0 run must generate a fixed evaluation report in Markdown, CSV, or JSON format.

### 24.1 Run Summary

```text
run_id:
run_date:
git_commit:
dataset_version:
corpus_version:
benchmark_size:
model:
embedding_model:
reranker_model:
retrieval_config:
generation_prompt_version:
verification_prompt_version:
```

### 24.2 Dataset Summary

```text
number_of_companies:
number_of_filings:
number_of_answerable_questions:
number_of_unanswerable_questions:
question_type_distribution:
average_gold_evidence_per_question:
```

### 24.3 Retrieval Metrics

```text
retrieval_recall@5:
retrieval_recall@10:
question_recall@10:
strict_precision@5:
strict_precision@10:
relaxed_precision@5:
relaxed_precision@10:
gold_page_hit@10:
wrong_company_rate:
wrong_year_rate:
```

### 24.4 Answer and Citation Metrics

```text
citation_accuracy:
claim_grounding_pass_rate:
unsupported_claim_rate:
uncited_claim_rate:
hallucination_rate:
answer_faithfulness:
```

### 24.5 Refusal Metrics

```text
refusal_accuracy:
false_answer_rate:
false_refusal_rate:
```

### 24.6 Failure Breakdown

```text
ingestion_error:
chunking_error:
metadata_error:
retrieval_error:
rerank_error:
citation_error:
claim_decomposition_error:
generation_error:
verification_error:
refusal_error:
benchmark_label_error:
```

### 24.7 Top Failed Cases

Each failed case should include：

```text
question_id:
question:
expected_behavior:
actual_behavior:
gold_evidence:
retrieved_evidence:
answer:
claims:
citations:
verification_labels:
failure_labels:
root_cause:
next_fix:
```

### 24.8 Config Snapshot

Attach or link to：

```text
ingestion_config
retrieval_config
generation_config
verification_config
evaluation_config
```

### 24.9 Next Fix Priority

The report must end with a ranked fix list：

```text
1. highest-impact issue
2. second issue
3. third issue
```

Fix order should generally follow：

```text
metadata / ingestion
retrieval
reranking
citation selection
claim decomposition
generation
verification
benchmark labels
```

---

## 25. Documentation Maintenance Rule

After v2.1, this document should not continue expanding broad rules unless a new failure mode is observed in benchmark runs.

Future changes should be driven by：

```text
failed benchmark cases
metric instability
unclear verifier labels
missing report fields
repeated engineering blockers
```

Avoid adding new governance or valuation rules before P0 is implemented.

Priority after v2.1：

```text
1. implement P0 ingestion
2. implement P0 retrieval baseline
3. implement P0 evaluation report
4. run failure review
5. update rules only when failures reveal ambiguity
```
