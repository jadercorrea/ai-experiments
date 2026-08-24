# Scoped related-work map

## Scope and method

This is a scoped primary-source review supporting protocol design, not a
systematic review or meta-analysis. Searches through **2026-08-24** covered ACL
Anthology, ICLR and NeurIPS proceedings, PMLR, arXiv, and official benchmark
pages. Query families combined terms for coding-agent evaluation, repository
benchmarks, agent memory, reflection, failed trajectories, context or prompt
compression, evidence attribution, stochastic agent evaluation, language
effects, and preregistration.

Inclusion favored peer-reviewed papers and official proceedings. Preprints and
industry sources are labeled and do not carry more evidentiary weight than
their review status supports. The search did not use duplicate independent
screeners, a registered query, citation-network saturation, or a formal risk-of-
bias instrument. Accordingly, the map can justify design choices and bound a
novelty statement, but cannot establish exhaustive priority.

## Evidence map

| Stream | Representative evidence | What it supports here | Boundary |
| --- | --- | --- | --- |
| Repository-level coding evaluation | [SWE-bench (Jimenez et al., ICLR 2024)](https://proceedings.iclr.cc/paper_files/paper/2024/hash/edac78c3e300629acfe6cbe9ca88fb84-Abstract-Conference.html) | Real issues, full repositories, patches, and executable tests are a meaningful evaluation unit | It evaluates issue resolution, not recovery-context policy after a matched failure |
| Freshness and decontamination | [SWE-rebench (Badertdinov et al., NeurIPS 2025)](https://proceedings.nips.cc/paper_files/paper/2025/hash/21bec6ace947b1b58967b945c8ac0f10-Abstract-Datasets_and_Benchmarks_Track.html); [Automated Benchmark Generation (Vergopoulos et al., ICML 2025)](https://proceedings.mlr.press/v267/vergopoulos25a.html) | Fresh tasks, reproducible environments, and continuously generated evaluations reduce contamination and staleness | Automated construction does not remove the need for solvability, leakage, and construct-validity audits |
| Benchmark validity | [SWE-Bench+ (Aleithan et al., preprint 2024)](https://arxiv.org/abs/2410.06992) | Issue text and evaluation design can permit shortcutting or misclassify success | This is a preprint and audits a specific benchmark, so its rates must not be generalized to this task set |
| Stochastic evaluation | [On Randomness in Agentic Evals (Bjarnason et al., preprint 2026)](https://arxiv.org/abs/2602.07150) | Multiple runs, explicit minimum effects, and power analysis are needed when trajectory variance can rival reported improvements | Preprint evidence informs design; calibration must estimate variance for this harness rather than import it |
| Reflection after failure | [Reflexion (Shinn et al., NeurIPS 2023)](https://papers.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html) | Linguistic feedback and episodic memory can improve later attempts without weight updates | Reflection is agent-authored memory, not an evidence-linked handoff compared against both raw and clean policies in isolated repositories |
| Structured experience memory | [SAMULE (EMNLP 2025)](https://aclanthology.org/2025.emnlp-main.839/) | Selecting and organizing prior experience is an active intervention rather than neutral context transfer | Its tasks and memory mechanism do not answer the proposed matched coding-recovery contrast |
| Error propagation from memory | [Xiong et al. (ACL 2026)](https://aclanthology.org/2026.acl-long.27/) | Experience-following can propagate errors and replay apparently relevant but misleading experiences | Memory addition/deletion across tasks differs from a successor inheriting one failed repository trajectory |
| Prompt compression | [LLMLingua (Jiang et al., EMNLP 2023)](https://aclanthology.org/2023.emnlp-main.825/); [LongLLMLingua (Jiang et al., ACL 2024)](https://aclanthology.org/2024.acl-long.91/) | Compression changes information density, position, cost, and downstream performance; compact context is not a neutral transport | General prompt compression does not enforce repository evidence attribution or isolate recovery after failure |
| Compression and grounding | [Li et al. (CustomNLP4U at ACL 2026)](https://aclanthology.org/2026.customnlp4u-1.19/) | Answer quality can degrade much less than citation grounding under compression, motivating separate evidence-integrity checks | Workshop RAG results are not coding-agent causal evidence; they motivate an integrity invariant |
| Evidence attribution | [RARR (Gao et al., ACL 2023)](https://aclanthology.org/2023.acl-long.910/); [Self-RAG (Asai et al., ICLR 2024)](https://proceedings.iclr.cc/paper_files/paper/2024/hash/25f7be9694d7b32d5cc670927b8091e1-Abstract-Conference.html) | Generated claims should be externally attributable and unsupported text should be detectable | Citations can be wrong or incomplete; event hashes establish provenance, not semantic truth |
| Language and lexicalization | [Talmy (1985)](https://dingo.sbs.arizona.edu/~hharley/courses/PDF/TalmyLexicalizationPatterns.pdf); [Slobin (1991)](https://benjamins.com/catalog/prag.1.1.01slo); [Papafragou et al. (2002)](https://www.sciencedirect.com/science/article/pii/S0010027701001664); [Papafragou and Selimis (2010)](https://doi.org/10.1080/01690960903017000) | Languages can package event components differently, making realization language a plausible treatment-integrity variable | Effects beyond speaking are mixed; these studies do not establish an effect in coding-agent summaries |
| Multilingual LLM behavior | [Huang et al. (Findings of EMNLP 2023)](https://aclanthology.org/2023.findings-emnlp.826/); [Behzad et al. (Findings of EMNLP 2024)](https://aclanthology.org/2024.findings-emnlp.916/); [Wang et al. (EMNLP 2025)](https://aclanthology.org/2025.emnlp-main.132/) | Prompt language and mixed-language reasoning can affect measured LLM performance | This motivates logging and control, not a multilingual efficacy claim in v0.1 |
| Preregistration | [Nosek et al. (PNAS 2018)](https://doi.org/10.1073/pnas.1708274114) | Separating prediction from postdiction makes confirmatory claims interpretable and constrains undisclosed flexibility | Preregistration does not repair a weak design; tasks, estimands, power, and integrity still require review |

## Directly relevant synthesis

The strongest prior evidence for the sender/handoff design is the conjunction of
three observations:

1. later agent attempts can benefit from linguistic feedback or stored
   experiences;
2. similar stored experiences can also induce similar outputs, error
   propagation, and misaligned replay;
3. compression can preserve apparent answer quality while losing grounding.

Together, these findings make “give the receiver a good summary” an
insufficient intervention definition. The study needs three explicit policies,
matched failed trajectories, evidence-level integrity checks, clean workspaces,
and an outcome evaluator independent of the agent's narrative.

## Review-bounded gap

The review identified work on repository-level coding benchmarks, reflective or
episodic memory, experience management, context compression, and evidence
attribution. It did not identify a controlled study combining all of these
features:

- one qualifying coding-agent failure reused across treatment arms;
- clean restart, full raw trajectory, and structured evidence-linked handoff;
- a fresh and verified receiver workspace in every arm;
- independent executable resolution rather than answer plausibility;
- attribution of model, harness, runtime, evaluator, and workflow failures;
- preservation and publication of invalid and failed trajectories.

The proposed contribution is therefore a **recovery harness and its causal
evaluation**, not a new general theory of memory and not a claim that structured
handoffs are superior. This gap statement must be updated if new or missed work
provides the combined comparison.

## Engineering context, not scientific validation

The following first-party materials show that the operational problem matters
to current coding-agent systems, but they are not substitutes for scientific
evidence and do not endorse this study:

- [OpenAI — Harness engineering](https://openai.com/index/harness-engineering/)
- [OpenAI — Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
- [Anthropic — Effective harnesses for long-running agents](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic — Infrastructure noise](https://www.anthropic.com/engineering/infrastructure-noise)

## Update rule

Before confirmatory freeze, repeat the search, follow backward and forward citations
from the most directly relevant works, publish the query strings and screening
ledger, and obtain an independent review of included and excluded close prior
art. A material change to the novelty claim does not by itself invalidate the
experiment; a material change to treatments, outcomes, or analysis requires a
new checksummed protocol version.
