# Econometric Research Writing Skill

Reusable `SKILL.md`-based agent skill for econometric analysis, economics/management empirical writing, citation integrity, and Word document production.

## Overview

An end-to-end skill for professional economics and management empirical research. It supports:

- Econometric dataset profiling and model-readiness checks.
- Evidence-first research grilling with one or more dependency-aware questions, recommended answers, knowledge-adaptive explanations, and an explicit implementation gate.
- Agent-decided variable roles based on data values, names, timing, codebook evidence, and the research question, with economic meaning checks, mechanism-path mapping, and causal-language boundaries.
- Method selection for panel, time-series, causal inference, RDD, matching, IPW, staggered DiD, GARCH, Markov-switching, panel VAR, and spatial panel designs.
- Literature search, citation provenance, and reference-integrity workflows with a strict no-fabrication rule.
- Economics/management paper drafting, empirical-strategy writing, results interpretation, robustness framing, and polished academic prose.
- Publication-style Word document generation with editable OMML formulas, three-line tables, source notes, figure/table QA, and superscript citation markers.

## 中文说明

这是一个面向经济学、金融学和管理学实证研究的 Agent Skill，覆盖从数据检查、研究设计和计量方法选择，到文献核验、论文写作及 Word 文档交付的完整流程。

主要功能包括：

- 读取 CSV、Excel 和 Stata 数据，检查变量类型、缺失、异常值、面板结构与模型可用性。
- 由 Agent 综合研究问题、变量名称、实际取值、时间关系和 codebook 判断变量角色，不依赖简单关键词自动分类。
- 自动生成描述性统计、基准回归、聚类标准误、稳健性结果、共线性诊断和事件研究图。
- 支持面板模型、IV/GMM、DiD、事件研究、RDD、匹配与加权、时间序列、GARCH、Markov-switching、Panel VAR 和空间面板等方法的选择与解释。
- 核验文献元数据和引用来源，禁止使用无法验证或凭空生成的参考文献。
- 生成经济学/管理学论文风格的 Word 文档，包括可编辑 OMML 公式、三线表、图表注释和结构完整性检查。

### Research Grill：研究设计质询

用户可以要求 Agent 对论文、数据、识别策略或计量方案进行 `grill`、压力测试或模拟答辩。例如：

```text
请结合我的数据 grill 这个研究设计，在达成共同理解前不要开始跑回归。

请质询我的 DiD 识别策略，每个问题都给出你的推荐答案和利弊。

请检查数据和现有代码后，对这篇论文进行模拟答辩。
```

Research Grill 遵循以下规则：

- Agent 先检查数据、代码、codebook、论文草稿和已有结果；能够自行查明的事实不再询问用户。
- 根据问题之间的依赖关系，每轮提出一个问题，或同时提出最多三个彼此独立的问题。
- 每个问题附带 Agent 的推荐答案、推荐理由、主要收益以及成本或风险。
- Agent 根据用户在当前主题中的回答动态调整解释深度；如果用户反复询问基础概念，后续每个推荐答案都会补充通俗解释、适用原因、利弊、假设和必要示例。
- 真正涉及研究目标、estimand、范围、假设和取舍的决定由用户作出，Agent 不会把建议当作用户同意。
- 在关键问题解决且用户明确允许前，不运行正式回归、不修改论文、不生成最终报告，也不提交代码。
- Grill 不创建独立的共识摘要、研究设计锁、项目记忆或 session tracker，直接使用 Agent 产品已有的项目上下文和记忆能力。

详细协议见 [`research-grilling.md`](econometric-research-writing/references/research-grilling.md)。

### 中文调用示例

```text
使用 econometric-research-writing 检查这份面板数据，判断变量角色并推荐基准模型。

分析政府补贴对企业创新的影响，生成描述性统计、聚类标准误回归和稳健性结果。

核验论文中的参考文献，并生成带可编辑公式和三线表的 Word 报告。
```

## Repository Layout

```text
.
├── econometric-research-writing/
│   ├── SKILL.md
│   ├── agents/
│   │   └── openai.yaml
│   ├── assets/
│   │   └── econ-paper-template.docx
│   ├── references/
│   └── scripts/
├── scripts/
│   └── validate_repository.py
├── requirements.txt
└── LICENSE
```

The skill directory intentionally contains only files needed by a `SKILL.md`-compatible agent runtime: core instructions, optional UI metadata, references, scripts, and reusable assets. Repository-level documentation and validation live at the repository root.

## Install

Clone the repository and copy the skill folder into the skill directory used by your agent runtime:

```bash
git clone https://github.com/lixinglong27/econometric-research-writing.git
cp -R econometric-research-writing/econometric-research-writing "$AGENT_SKILLS_DIR/econometric-research-writing"
```

Replace `AGENT_SKILLS_DIR` with the directory your runtime uses for local skills.

## Use Helper Scripts

Install the Python dependencies when you want to run the bundled helper scripts directly:

```bash
python3 -m pip install -r requirements.txt
```

Example commands from the repository root:

```bash
python3 econometric-research-writing/scripts/profile_econ_dataset.py data.csv --out profile.md --json-out profile.json
python3 econometric-research-writing/scripts/run_empirical_analysis.py data.csv --roles-json roles.json --output-dir results
python3 econometric-research-writing/scripts/build_paper_docx.py paper.json paper.docx --template econometric-research-writing/assets/econ-paper-template.docx
python3 econometric-research-writing/scripts/check_docx_integrity.py paper.docx
python3 econometric-research-writing/scripts/verify_references.py references.json --out-json verification.json --out-enriched-json references_clean.json
```

DOCX rendering is optional and depends on an external document renderer. The skill supports renderer discovery through generic document-rendering environment variables documented in `econometric-research-writing/references/docx-workflow.md`.

## Validate

Run the lightweight repository checks:

```bash
python3 scripts/validate_repository.py
```

Run full smoke tests after installing dependencies:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate_repository.py --full
```

The full validation compiles helper scripts, checks for local-path leaks, verifies the DOCX template structure, profiles a small panel dataset, generates a paper DOCX with an editable formula and three-line table, and inspects the result for citation/table/style issues.

## Responsible Use

- Treat the skill as a research and writing assistant, not a substitute for econometric judgment. Review model choices, identifying assumptions, and result interpretation before relying on outputs.
- Verify data rights, privacy constraints, and institutional rules before using confidential or restricted datasets with any agent runtime.
- Treat literature and citation outputs as source-backed only after verification. If a paper, DOI, dataset, or claim cannot be verified, do not cite it as fact.
- Inspect generated Word documents before submission, especially formulas, table notes, source notes, citations, and figure placement.
- For repository maintenance and contribution standards, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License. See [LICENSE](LICENSE).
