# Gen AI Architect — One-Page Cheat Sheet

> Review time: ~8 minutes · Covers the 80/20 of production GenAI architecture
> **Revised: May 2026** — updated for 2025-26 model landscape, multi-agent systems, MCP, enterprise cloud AI

---

## 1. Core Mental Model

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        GEN AI APPLICATION STACK                          │
├──────────────────────────────────────────────────────────────────────────┤
│  UI / Client                                                             │
│    ↓                                                                     │
│  API Gateway + Auth + Rate Limiting + Cost Tracking                      │
│    ↓                                                                     │
│  ┌──────────────┐   ┌──────────────────────────┐   ┌───────────────────┐ │
│  │ INPUT RAILS  │ → │      ORCHESTRATOR        │ → │   OUTPUT RAILS    │ │
│  │ PII filter   │   │  Chains / Agents /       │   │  Toxicity filter  │ │
│  │ Injection    │   │  Multi-Agent Graph       │   │  Hallucination    │ │
│  │ Topic guard  │   │  (LangGraph / CrewAI)    │   │  Schema validate  │ │
│  └──────────────┘   └────────────┬─────────────┘   └───────────────────┘ │
│                                  │                                        │
│           ┌──────────────────────┼──────────────────┐                     │
│           ↓                      ↓                  ↓                     │
│    ┌─────────────┐       ┌──────────────┐    ┌────────────────┐           │
│    │  RAG        │       │  LLM         │    │  TOOLS via MCP │           │
│    │  Pipeline   │       │  Gateway     │    │  SQL/API/Code  │           │
│    └─────────────┘       └──────────────┘    └────────────────┘           │
│           ↓                      ↓                                        │
│    Vector Store            Model Pool                                     │
│    (pgvector,            (GPT-4o / Claude /                               │
│     Pinecone, Qdrant)     Llama / Gemini)                                 │
├──────────────────────────────────────────────────────────────────────────┤
│  OBSERVABILITY: Tracing · Evals · Cost per query · Prompt versions · Audit│
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Model Selection — Decision Matrix

| Need | Go-To Choice | Example |
|------|-------------|---------|
| Best quality, managed infra | **Closed API** (GPT-4o, Claude 3.7 Sonnet, Gemini 2.0) | Customer-facing chatbot |
| Multi-step complex reasoning | **Reasoning model** (o3, Claude 3.7 Thinking, Gemini 2.0 Flash Thinking) | Agentic research, code debugging |
| Data privacy / on-prem | **Open-weight** (Llama 3.1, Mistral, Qwen 2.5, DeepSeek) | Healthcare / finance app |
| High-volume, simple task | **Small model** (Phi-3, Gemma 2, fine-tuned 7B) | Classification, extraction, routing |
| Edge / mobile / offline | **Quantized small model** (GGUF 4-bit, Llama.cpp) | On-device assistant |
| Domain-specific style/format | **Fine-tuned model** (LoRA/QLoRA on base) | Legal doc drafting, clinical notes |
| Images, docs, charts, audio | **Multimodal** (GPT-4o vision, Claude 3.7, Gemini 2.0 Flash) | Document parsing, chart Q&A |

> **Rule of thumb:** Start with prompting → add RAG → use reasoning model → fine-tune only as last resort.
> **Reasoning model rule:** Don't add chain-of-thought instructions — they reason internally. Prompt clearly and concisely.

---

## 3. RAG — The #1 Architecture Pattern (60%+ of apps)

```
 INGESTION                           RETRIEVAL & GENERATION
 ─────────                           ──────────────────────
 Documents                           User Query
    ↓                                   ↓
 Chunking ──────┐                    Embed Query
 (recursive /   │                       ↓
  semantic /    │                    Hybrid Search (Dense + BM25)
  parent-doc)   │                       ↓
    ↓           │                    Reranker (cross-encoder)
 Embedding      │                       ↓
    ↓           │                    Top-K Chunks
 Vector DB ◄────┘                       ↓
                                     Prompt = Context + Query
                                        ↓
                                       LLM
                                        ↓
                                     Response (+ source citations)
```

**Chunking:** Recursive (general purpose), Semantic (variable topics), Parent-doc (preserve hierarchy)
**Hybrid search** = Dense vectors + Sparse BM25 → best recall (especially for codes, acronyms, exact terms)
**Reranker** (Cohere Rerank, BGE cross-encoder) → biggest single quality boost after basic RAG

**Advanced patterns:**

| Pattern | When to Use |
|---------|-------------|
| **HyDE** | Vague short queries — LLM generates hypothetical answer, embed that instead of raw query |
| **Multi-query** | Ambiguous queries — generate 3 rephrasings, merge results |
| **Self-RAG** | Low faithfulness — model assesses and regenerates if grounded score too low |
| **GraphRAG** | Multi-hop reasoning across connected entities (org charts, legal structures) |
| **Agentic RAG** | Dynamic retrieval — agent decides what/when to retrieve via tools |

**Long-context vs RAG (2025 tradeoff):**
- Use **RAG** when: corpus > 100K docs, high noise, freshness required, cost-sensitive
- Use **long-context** when: small doc set (<50 docs), reasoning over full document, ordering matters

---

## 4. Multi-Agent Systems — 2025's Growth Pattern

```
TOPOLOGIES
──────────

Sequential:     A → B → C → Output          (predictable, fast)
Parallel:       A → [B, C, D] → Merge       (faster for independent tasks)
Hierarchical:   Supervisor → [Specialist1, Specialist2] → Synthesizer
Cyclic (Graph): A ⇄ B (with loop guard)    (iterative refinement, LangGraph)

ORCHESTRATOR / WORKER PATTERN (most common in production)
─────────────────────────────
User Query
    ↓
Orchestrator (plans, routes, aggregates)
    ├── Research Agent   (web search + RAG)
    ├── Code Agent       (writes + executes code)
    └── Critic Agent     (fact-checks output)
         ↓
    Synthesizer → Response
```

**Framework selection:**

| Framework | Best For | Key Feature |
|-----------|---------|-------------|
| **LangGraph** | Complex stateful agents | Graph-based control flow, cycles, human-in-the-loop |
| **CrewAI** | Role-based collaboration | Role/goal/backstory per agent, crew orchestration |
| **AutoGen** | Conversational multi-agent | Two-agent and group-chat patterns |
| **Semantic Kernel** | .NET / Microsoft enterprise | Deep Azure OpenAI integration |

**Failure modes & mitigations:**
- **Infinite loops** → add max_iterations, loop detection
- **Context overflow** → summarize intermediate results, use memory tools
- **Agent hallucination** → add critic agent, verify tool outputs
- **Runaway cost** → budget cap per request, model cascading within agents

---

## 5. Context & Prompt Engineering

**Context engineering (2025):** Strategic control of the context window — what goes in, in what order, how compressed.

```
Context Window Budget
─────────────────────
System Prompt       ~5–10%   (persona, rules, output format)
Retrieved Context   ~60–70%  (RAG chunks, ranked by relevance)
Conversation Memory ~10–15%  (summarized history, not raw turns)
User Query          ~5%      (the actual question)
Output Reserve      ~10%     (leave room for response)
```

**High-impact prompt patterns:**

| Pattern | What It Does | When to Use |
|---------|-------------|-------------|
| **Zero-shot** | Direct instruction | Simple, well-defined tasks |
| **Few-shot (2–5 examples)** | Anchor format/style | Consistency, domain-specific output |
| **Chain-of-Thought** | "Think step by step" | Reasoning, math, multi-step logic |
| **Structured Output** | "Return JSON with schema…" | API integrations, downstream parsing |
| **System Prompt** | Persona, rules, constraints | Every production app |
| **XML structuring** | `<context>`, `<question>` tags | Complex multi-part prompts (Claude) |

> **Reasoning models (o3, Claude Thinking):** Skip CoT instructions — they think internally. Focus on clear problem framing.

---

## 6. MCP — Model Context Protocol

**What it is:** Anthropic's open standard for connecting LLMs to external data sources and tools. Replaces ad-hoc tool integrations with a standardized client-server protocol.

```
LLM Application (MCP Client)
         │
    MCP Protocol
         │
    ┌────┴────────────────────────────────┐
    │              MCP Servers            │
    ├────────────┬────────────┬───────────┤
    │  Database  │  File      │  API      │
    │  Server    │  System    │  Services │
    │  (SQL/NoSQL│  Server    │  (REST,   │
    │   queries) │  (read/    │   GraphQL)│
    │            │   write)   │           │
    └────────────┴────────────┴───────────┘
```

**Three primitives:**
- **Resources** — read-only data (files, DB records, API responses)
- **Tools** — actions the LLM can invoke (write to DB, call API, run code)
- **Prompts** — reusable prompt templates served by the server

**Why it matters for architects:** Instead of custom integrations per LLM provider, one MCP server works with any MCP-compatible client. Huge for enterprise systems with many data sources.

---

## 7. Fine-Tuning — Decision Ladder

```
 Can prompting solve it?      ──YES──→  Stop. Use prompts.
        │ NO
 Can few-shot solve it?       ──YES──→  Stop. Use few-shot.
        │ NO
 Can RAG solve it?            ──YES──→  Stop. Use RAG.
        │ NO
 Can context distillation?    ──YES──→  Use large model to generate
        │ NO                            training data for small model.
 Fine-tune with LoRA/QLoRA  ←──────── You are here.
        │
 Need entirely new knowledge? ──YES──→  Continued pre-training first.
```

- **LoRA** — train only low-rank adapters (~0.1% of params) → cheap, fast, mergeable
- **QLoRA** — LoRA + 4-bit quantization → fine-tune 70B on a single GPU
- **SFT** — Supervised Fine-Tuning (input/output pairs); format/style/domain adaptation
- **DPO** — Direct Preference Optimization (preferred vs rejected pairs); cheaper than RLHF
- **RLHF** — Reinforcement Learning from Human Feedback; for safety/alignment alignment
- Need **1K–10K high-quality examples** for most fine-tuning tasks

---

## 8. Guardrails & Safety

```
 INPUT RAILS                         OUTPUT RAILS
 ───────────                         ────────────
 ✓ PII detection/redaction           ✓ Toxicity filter
 ✓ Prompt injection detection        ✓ Hallucination check (vs retrieved context)
 ✓ Topic boundary enforcement        ✓ Schema / format validation
 ✓ Rate limiting (per user/tenant)   ✓ Sensitive content filter
 ✓ Jailbreak detection               ✓ PII re-identification after generation
```

**Top 3 Threats (OWASP LLM Top 10):**

| Threat | Attack | Mitigation |
|--------|--------|------------|
| **Prompt Injection** | Crafted input hijacks LLM behavior | Input sanitization, separate system/user context, LLM-based detection |
| **Data Leakage** | Model reveals training data or PII | PII redaction, output filtering, data minimization |
| **Insecure Output Handling** | App trusts LLM output blindly | Schema validation, sandboxed execution, human-in-the-loop |

**EU AI Act (2025) — key tiers for architects:**

| Risk Level | Examples | Obligations |
|-----------|---------|-------------|
| **Unacceptable** | Social scoring, subliminal manipulation | Banned — cannot deploy |
| **High-risk** | HR systems, credit scoring, medical, biometrics | Conformity assessment, human oversight, audit trail |
| **Limited risk** | Chatbots, deepfake disclosure | Transparency obligations only |
| **Minimal risk** | Spam filters, AI in video games | No specific obligations |

> Enterprise GenAI copilots used in HR, lending, or healthcare = **high-risk**. Design compliance in from day one.

---

## 9. Evaluation — Measure Everything

| Metric | What It Measures | Tool |
|--------|-----------------|------|
| **Faithfulness** | Is the answer grounded in retrieved context? | RAGAS |
| **Answer Relevancy** | Does it actually address the question? | RAGAS |
| **Context Precision** | Are retrieved chunks relevant (not noise)? | RAGAS |
| **Context Recall** | Are all relevant chunks retrieved? | RAGAS |
| **Hallucination Rate** | % of unsupported claims in output | Custom + LLM-as-judge |
| **Latency (P50/P99)** | Response time percentiles | LangSmith / LangFuse |
| **Cost per query** | Token usage × price | Observability platform |

**LLM-as-Judge:** Use a stronger model to score a weaker model's output. Cheap and scalable, but watch for:
- **Position bias** — prefers first answer in comparisons
- **Verbosity bias** — prefers longer answers
- **Self-preference** — GPT-4 prefers GPT-4-generated answers

**Data flywheel:** User feedback → annotation → eval dataset grows → prompt/model improves → repeat. This is how production AI compounds quality over time.

**CI/CD integration:** Fail the PR/deploy if hallucination rate > threshold or answer relevancy drops below baseline.

---

## 10. Enterprise Cloud AI Platforms

| Platform | Best For | Standout Features |
|----------|---------|-------------------|
| **AWS Bedrock** | AWS-native enterprises | Bedrock Agents, Knowledge Bases, Guardrails, model variety (Claude, Llama, Titan) |
| **Azure OpenAI Service** | Microsoft/regulated industries | PTU (reserved throughput), private endpoints, HIPAA/SOC2, GPT-4o + o3 |
| **Google Vertex AI** | GCP shops, multimodal-heavy | Gemini 2.0 native, Grounding (Google Search), Model Garden, Agent Engine |

**Decision guide:**
- Already on AWS? → **Bedrock** (native IAM, VPC, CloudTrail audit)
- Regulated industry + Microsoft stack? → **Azure OpenAI** (PTU for predictable cost/latency, compliance certifications)
- Multimodal or Google Search grounding? → **Vertex AI**
- Need multi-cloud or model diversity? → **Model Gateway** layer over all three

> **Managed platform vs direct API:** Use managed platforms (Bedrock/Vertex/Azure) for enterprise — they provide compliance, audit logs, VPC isolation, and SLAs. Use direct APIs (Anthropic/OpenAI) for early-stage projects or when you need bleeding-edge model versions faster.

---

## 11. Serving & Cost Optimization

| Strategy | Cost Savings | Tradeoff |
|----------|-------------|----------|
| **Model cascading** (small → large fallback) | 40–70% | Slight latency for hard queries |
| **Semantic caching** (cache similar queries) | 30–50% | Cache staleness risk |
| **Quantization** (4-bit / 8-bit) | 2–4× memory reduction | Minor quality loss |
| **Prompt compression** (LLMLingua) | 20–40% fewer tokens | Possible context loss |
| **Batching** (continuous batching via vLLM) | 2–5× throughput | Slight latency increase |
| **Provisioned Throughput** (Azure PTU / Bedrock) | Predictable cost at scale | Upfront commitment |

> **GPU Memory Rule:** Model size (GB) ≈ Params (B) × bytes/param
> FP16 = 2 bytes, INT8 = 1 byte, INT4 = 0.5 bytes
> *Example:* Llama 3 70B at INT4 ≈ 70 × 0.5 = **35 GB** → fits on 1× A100 80GB

---

## 12. Production Checklist

**Architecture:**
- [ ] **Model Gateway** — abstraction layer over multiple LLM providers (swap without code change)
- [ ] **Multi-agent topology defined** — sequential/parallel/hierarchical based on task complexity
- [ ] **MCP servers** — standardized tool/data integration layer where applicable
- [ ] **Fallback strategy** — graceful degradation when primary LLM is down or slow

**Safety & Compliance:**
- [ ] **Guardrails** — input/output filtering pipeline active
- [ ] **PII Handling** — redaction before LLM, re-identification gating after
- [ ] **EU AI Act risk tier assessed** — compliance architecture in place if high-risk
- [ ] **Red-teaming** — adversarial testing done before production launch

**Quality & Observability:**
- [ ] **Eval Pipeline** — automated evals run on every prompt/model change (CI/CD gated)
- [ ] **Observability** — traces, latency (P50/P99), cost, quality metrics dashboarded
- [ ] **Human-in-the-loop** — escalation path for low-confidence responses
- [ ] **Data flywheel** — feedback → annotation → eval dataset growth cycle defined

**Operations:**
- [ ] **Caching** — semantic cache for repeated/similar queries
- [ ] **Rate Limiting** — per-user and per-tenant limits enforced
- [ ] **Versioning** — prompts, models, and RAG indices versioned together
- [ ] **Cost alerting** — budget thresholds with auto-alerts configured

---

## Key Formulas

```
Cost per query  = (input_tokens × input_price) + (output_tokens × output_price)
Monthly budget  = daily_queries × avg_tokens × model_price × 30
GPU memory (GB) = params(B) × bytes_per_param + KV_cache_overhead
Latency         = TTFT (time to first token) + (output_tokens × time_per_token)
RAG quality     = f(chunking, embedding model, retrieval, reranker, prompt)
Hallucination   ↓ with: stronger system prompt + reranker + self-RAG + output guardrails
```

---

> **The GenAI Architect's Mantra:**
> *"Prompt first. Retrieve second. Orchestrate third. Fine-tune last. Guard always. Measure everything."*
