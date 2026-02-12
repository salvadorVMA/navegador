# Open-Source Models Plan & Business Case

## Context

Navegador currently uses commercial API models (OpenAI GPT-4.1-mini, with Anthropic Claude and Google Gemini being tested). This document evaluates whether open-source models could replace or complement commercial APIs, and under what conditions it makes business sense.

---

## 1. Candidate Open-Source Models

### Tier 1: Top Performers (Production-Ready)

| Model | Parameters | Context Window | Strengths | License |
|-------|-----------|----------------|-----------|---------|
| **Llama 4 Scout** | 109B (17B active MoE) | 512K | Best open MoE model, multilingual, strong reasoning | Llama 4 Community |
| **Llama 4 Maverick** | 400B (17B active MoE) | 1M | Highest-quality open model, excellent Spanish | Llama 4 Community |
| **DeepSeek-V3** | 671B (37B active MoE) | 128K | Top benchmark scores, very efficient MoE | MIT |
| **Qwen 2.5-72B** | 72B | 128K | Strong multilingual, excellent Chinese/Spanish | Apache 2.0 |
| **Mistral Large 2** | 123B | 128K | Strong European languages, good structured output | Apache 2.0 |

### Tier 2: Efficient / Cost-Optimized

| Model | Parameters | Context Window | Strengths | License |
|-------|-----------|----------------|-----------|---------|
| **Llama 4 Scout (quantized)** | 109B (INT4) | 512K | Runs on single GPU with quantization | Llama 4 Community |
| **Qwen 2.5-32B** | 32B | 128K | Strong quality-per-parameter ratio | Apache 2.0 |
| **Mistral Small 3.1** | 24B | 128K | Fast, efficient, good for classification | Apache 2.0 |
| **Gemma 3 27B** | 27B | 128K | Google quality, compact size | Gemma license |
| **Phi-4** | 14B | 16K | Microsoft, strong reasoning for size | MIT |

### Tier 3: Lightweight / Edge

| Model | Parameters | Context Window | Use Case in Navegador |
|-------|-----------|----------------|----------------------|
| **Llama 3.2-3B** | 3B | 128K | Intent classification only |
| **Qwen 2.5-7B** | 7B | 128K | Variable grading, simple tasks |
| **Mistral 7B v0.3** | 7B | 32K | Fast classification, embeddings |

### Recommended for Navegador Testing

For our specific workloads (bilingual Spanish/English, survey analysis, JSON output, multi-step reasoning):

1. **Llama 4 Maverick** - Best overall candidate (excellent Spanish, large context, MoE efficiency)
2. **Qwen 2.5-72B** - Best multilingual alternative, Apache license
3. **DeepSeek-V3** - Highest benchmark performance, MIT license
4. **Mistral Small 3.1** - Best lightweight option for simple tasks (intent, grading)

---

## 2. Hosting Options

### Option A: Managed Inference APIs (Easiest)

Use hosted APIs that serve open-source models. Same API pattern as OpenAI, minimal code changes.

| Provider | Models Available | Pricing (per 1M tokens) | Pros | Cons |
|----------|-----------------|------------------------|------|------|
| **Together AI** | Llama 4, DeepSeek, Qwen, Mistral | $0.10-$0.90 input, $0.10-$0.90 output | Cheapest, OpenAI-compatible API | Less control |
| **Fireworks AI** | Llama 4, DeepSeek, Qwen, Mistral | $0.10-$0.90 | Very fast inference, speculative decoding | Fewer models |
| **Groq** | Llama 4, DeepSeek, Mistral, Gemma | Free tier, then ~$0.05-$0.50 | Fastest inference (LPU), free tier | Limited model sizes |
| **Anyscale/Ray** | All major open models | $0.15-$1.00 | Scalable, enterprise features | More complex setup |
| **AWS Bedrock** | Llama 4, Mistral | $0.20-$1.50 | AWS integration, SLAs | Higher cost |
| **Azure AI** | Llama 4, Mistral, Phi-4 | $0.20-$1.50 | Azure integration, compliance | Higher cost |

**Recommendation for Navegador**: Start with **HuggingFace Inference Providers** or **Groq** for testing. Both offer OpenAI-compatible APIs, so integration requires only changing the base URL and model name.

### Option A.2: HuggingFace (Best for Testing & Prototyping)

HuggingFace provides a particularly strong option for the **testing and evaluation stage** because it offers free tiers, hosts every major open-source model, and provides OpenAI-compatible endpoints.

#### HuggingFace Inference Providers (Serverless API)

Route requests to 200+ open-source models through a single OpenAI-compatible endpoint.

| Tier | Monthly Credit | Rate Limits | Pay-as-you-go |
|------|---------------|-------------|---------------|
| **Free** | $0.10 | Basic | No |
| **PRO ($9/mo)** | $2.00 | Higher + priority queue | Yes |
| **Team/Enterprise** | $2.00/seat | Highest | Yes |

```python
# Drop-in replacement using the OpenAI client
from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN")
)

response = client.chat.completions.create(
    model="meta-llama/Llama-4-Scout-17B-16E-Instruct",
    messages=[{"role": "user", "content": "Hello"}]
)
```

Append `:fastest` or `:cheapest` to the model name to let HuggingFace route to the optimal provider automatically (e.g., `meta-llama/Llama-4-Scout-17B-16E-Instruct:cheapest`).

#### HuggingFace Inference Endpoints (Dedicated)

Spin up a dedicated GPU endpoint for a specific model, billed by the minute.

| GPU | VRAM | Hourly Cost | Good For |
|-----|------|-------------|----------|
| T4 | 16GB | $0.50/hr | 7B models (Qwen 2.5-7B, Mistral 7B) |
| L40S | 48GB | $1.80/hr | 32B models (Qwen 2.5-32B) |
| A100 | 80GB | $2.50/hr | 72B models (Qwen 2.5-72B INT4) |
| H100 | 80GB | $4.50/hr | Large MoE models (Llama 4 Scout) |

Endpoints can auto-scale to zero when idle - **no cost when not in use**. This makes them ideal for testing stages where usage is intermittent.

#### HuggingFace Spaces (Free GPU Access)

| Option | Resources | Cost | Use Case |
|--------|-----------|------|----------|
| **CPU Basic** | 2 vCPU, 16GB RAM | Free | Ollama + small models |
| **ZeroGPU** | Dynamic H200 70GB | Free | Run any model via Gradio app |

ZeroGPU Spaces can run large models for free by dynamically allocating H200 GPUs. Latency is higher (cold start), but cost is zero - perfect for evaluation.

#### Why HuggingFace for Navegador Testing

1. **$0 to start**: Free tier gives enough credits to run the full test suite on 2-3 models
2. **Every model in one place**: All Llama, Qwen, Mistral, DeepSeek models on the same platform
3. **OpenAI-compatible API**: Same `call_llm()` code from the comparison notebook works directly
4. **Scale-to-zero endpoints**: Pay only during active testing sessions
5. **ZeroGPU**: Run even 70B+ models for free (with Gradio/Spaces wrapper)
6. **PRO at $9/month**: $2 in credits + pay-as-you-go covers extensive testing

### Option B: Self-Hosted (Maximum Control)

Run models on your own infrastructure.

| Platform | Setup Complexity | Cost Model | Best For |
|----------|-----------------|------------|----------|
| **vLLM on GPU VMs** | Medium | Pay for GPU time | High-volume production |
| **Ollama** | Low | Local hardware | Development/testing |
| **Text Generation Inference (TGI)** | Medium | Pay for GPU time | Production, HuggingFace ecosystem |
| **llama.cpp** | Low | CPU/local | Testing, small models |

**GPU Requirements for Key Models:**

| Model | VRAM Required | Recommended GPU | Monthly Cloud Cost |
|-------|--------------|-----------------|-------------------|
| Llama 4 Scout (INT4) | ~60GB | 1x A100 80GB | ~$1,500/mo |
| Llama 4 Maverick (INT4) | ~220GB | 4x A100 80GB | ~$6,000/mo |
| Qwen 2.5-72B (INT4) | ~40GB | 1x A100 80GB | ~$1,500/mo |
| DeepSeek-V3 (INT4) | ~350GB | 8x A100 80GB | ~$12,000/mo |
| Mistral Small 3.1 | ~14GB | 1x A10G 24GB | ~$400/mo |
| Qwen 2.5-7B | ~5GB | 1x T4 16GB | ~$150/mo |

### Option C: Hybrid Approach (Recommended)

Use HuggingFace for free evaluation, managed APIs for low-traffic production, self-host only for high-volume.

```
Evaluation/Testing:     HuggingFace free tier + ZeroGPU Spaces  ($0/month)
Active Testing:         HuggingFace PRO + scale-to-zero endpoints ($9 - $50/month)
Low Traffic Production: Together AI / HuggingFace APIs             ($50 - $500/month)
High Traffic Production: Self-hosted vLLM                          ($1,500+ /month)
```

---

## 3. Business Case: Commercial vs Open-Source

### Scenario: Navegador Production Usage

Assumptions based on current notebook tests:
- **Average call**: ~2,500 tokens (input + output)
- **Calls per user session**: ~15 (intent + grading + analysis + expert + transversal)
- **Monthly active users**: 100, 1,000, and 10,000 scenarios

### Cost Comparison: Per 1M Tokens

| Provider/Model | Input Cost | Output Cost | Effective Blend* |
|----------------|-----------|-------------|-----------------|
| **OpenAI GPT-4.1-mini** | $0.40 | $1.60 | $0.80 |
| **OpenAI GPT-4.1** | $2.00 | $8.00 | $4.00 |
| **Anthropic Claude 3.5 Haiku** | $0.80 | $4.00 | $1.88 |
| **Anthropic Claude Sonnet 4.5** | $3.00 | $15.00 | $7.05 |
| **Google Gemini 2.0 Flash** | $0.10 | $0.40 | $0.20 |
| **Together AI Llama 4 Scout** | $0.18 | $0.18 | $0.18 |
| **Together AI Llama 4 Maverick** | $0.27 | $0.85 | $0.47 |
| **Together AI Qwen 2.5-72B** | $0.54 | $0.54 | $0.54 |
| **Groq Llama 4 Scout** | $0.11 | $0.18 | $0.13 |
| **Self-hosted Qwen 72B** | ~$0.05** | ~$0.05** | ~$0.05** |

*Blend assumes 60% input, 40% output tokens. **Self-hosted cost amortized at moderate utilization.

### Monthly Cost Projections

| Scenario | Calls/Month | OpenAI GPT-4.1-mini | Anthropic Haiku | Gemini Flash | Together Llama 4 | Self-Hosted |
|----------|------------|---------------------|-----------------|--------------|-------------------|-------------|
| **100 users** | 1,500 | $3.00 | $7.05 | $0.75 | $0.68 | $1,500 (fixed) |
| **1,000 users** | 15,000 | $30.00 | $70.50 | $7.50 | $6.75 | $1,500 (fixed) |
| **10,000 users** | 150,000 | $300.00 | $705.00 | $75.00 | $67.50 | $1,500 (fixed) |
| **100,000 users** | 1,500,000 | $3,000.00 | $7,050.00 | $750.00 | $675.00 | $1,500 (fixed) |

**Break-even point for self-hosting**: Self-hosting Qwen 72B on a single A100 breaks even vs. Together AI at ~30M tokens/month (~800,000 calls), or roughly **30,000+ monthly active users**.

### Total Cost of Ownership (TCO) - 12 Months

| Factor | Commercial API | Managed Open-Source API | Self-Hosted |
|--------|---------------|------------------------|-------------|
| **Infrastructure** | $0 | $0 | $18,000 - $72,000 |
| **API Costs (1K users)** | $360 - $8,460 | $81 - $810 | $0 (included above) |
| **Engineering Setup** | 2-4 hours | 4-8 hours | 40-80 hours |
| **Maintenance** | 0 hours/month | 0-2 hours/month | 8-16 hours/month |
| **Monitoring** | Included | Included | Must build/buy |
| **12-Month Total (1K users)** | **$360 - $8,460** | **$81 - $810** | **$18,000 - $72,000** |

### Quality Considerations

| Dimension | Commercial APIs | Open-Source (Top Tier) | Impact on Navegador |
|-----------|----------------|----------------------|---------------------|
| **JSON compliance** | Excellent (native support) | Good (needs prompt engineering) | Critical for all prompts |
| **Spanish proficiency** | Excellent | Good-Excellent (Llama 4, Qwen) | Critical for survey data |
| **Instruction following** | Excellent | Good | Important for multi-step |
| **Reasoning depth** | Excellent | Good-Excellent (DeepSeek, Llama 4) | Important for cross-analysis |
| **Consistency** | Very high | Moderate-High | Important for grading |
| **Rate limits** | Enforced | None (self-hosted) / Generous (managed) | Important at scale |
| **Uptime SLA** | 99.9%+ | 99.5%+ (managed) / You manage | Important for production |
| **Data privacy** | Data sent to third party | Data stays local (self-hosted) | May matter for sensitive data |

---

## 4. Recommended Strategy

### Phase 1: Evaluate (Now - 2 weeks)
- **Run the multi-model comparison notebook** with OpenAI and Anthropic (done)
- **Add HuggingFace Inference Providers** to the comparison notebook (OpenAI-compatible, free tier)
- Sign up for HuggingFace PRO ($9/mo) if free credits are insufficient
- Test **Llama 4 Scout** and **Qwen 2.5-72B** on all 7 test categories via HuggingFace router
- Optionally test with **Groq** (free tier, fastest inference) as secondary
- Focus on: JSON compliance, Spanish quality, cross-analysis accuracy

### Phase 2: Integrate Best Open-Source Option (2-4 weeks)
- Add a `provider` parameter to the existing `call_llm()` / `get_answer()` functions
- Make model selection configurable via `config.py` or environment variables
- Run the A/B testing framework (`meta_prompting.py`) with open-source vs commercial
- Implement fallback: if open-source fails JSON parsing, retry with commercial

### Phase 3: Optimize for Production (1-2 months)
- **Tiered model strategy**:
  - Intent classification: Lightweight model (Mistral Small 3.1 / Llama 3.2-3B) - cheapest
  - Variable grading: Mid-tier (Qwen 2.5-32B) - good cost/quality
  - Cross-analysis + Expert + Transversal: Top-tier (Llama 4 Maverick or commercial) - best quality
- Evaluate self-hosting if traffic exceeds 10,000 monthly users
- Set up quality monitoring to detect model degradation

### Phase 4: Scale Decision (3-6 months)
- If <10K users: Stay on managed APIs (Together AI + OpenAI fallback)
- If >10K users: Evaluate self-hosting economics
- If data privacy required: Self-host with vLLM on dedicated infrastructure

---

## 5. Integration Code Sketch

Adding open-source model support via Together AI or Groq requires minimal code changes since both provide OpenAI-compatible APIs:

```python
# In config.py or .env
LLM_PROVIDER=together  # or: openai, anthropic, groq, self-hosted
LLM_MODEL=meta-llama/Llama-4-Scout-17B-16E-Instruct

# In utility_functions.py - only the client initialization changes
from openai import OpenAI

providers = {
    'openai': OpenAI(api_key=os.getenv('OPENAI_API_KEY')),
    'huggingface': OpenAI(
        api_key=os.getenv('HF_TOKEN'),
        base_url='https://router.huggingface.co/v1'
    ),
    'together': OpenAI(
        api_key=os.getenv('TOGETHER_API_KEY'),
        base_url='https://api.together.xyz/v1'
    ),
    'groq': OpenAI(
        api_key=os.getenv('GROQ_API_KEY'),
        base_url='https://api.groq.com/openai/v1'
    ),
}

# All existing call_llm / get_answer code works unchanged
# HuggingFace model names use the HF Hub format:
#   "meta-llama/Llama-4-Scout-17B-16E-Instruct"
#   "Qwen/Qwen2.5-72B-Instruct"
#   "mistralai/Mistral-Small-3.1-24B-Instruct-2503"
# Append :cheapest or :fastest for automatic provider routing
```

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Open-source model produces invalid JSON | Medium | High | JSON retry logic, fallback to commercial |
| Spanish quality below commercial models | Low | Medium | Test extensively before switching |
| Model hosting costs exceed API costs | Medium | Medium | Start with managed APIs, self-host only at scale |
| Open-source model discontinued/deprecated | Low | Low | Multiple options available, easy to switch |
| Latency higher than commercial APIs | Medium | Medium | Use managed APIs with edge inference (Groq) |
| Prompt engineering effort for new models | High | Low | Reuse existing A/B testing framework |

---

## 7. Decision Framework

**Use commercial APIs (OpenAI/Anthropic) when:**
- Quality is non-negotiable (flagship demo, public-facing)
- Volume is low (<10K users)
- Speed to market matters more than cost
- You need enterprise SLAs and support

**Use managed open-source APIs (Together/Groq) when:**
- Cost optimization is important
- You want to reduce vendor lock-in
- Volume is moderate (1K-100K users)
- You can tolerate slightly lower quality on some tasks

**Self-host open-source models when:**
- Volume is very high (>100K users)
- Data privacy is a hard requirement
- You have ML engineering capacity for operations
- You need full control over model behavior and updates

### For Navegador Specifically

Given that Navegador is a **demonstration project** being prepared for public access:

**Recommended approach**: **Commercial APIs (OpenAI GPT-4.1-mini) as primary, with Together AI (Llama 4 Scout) as tested alternative**

Rationale:
- Demo quality matters more than cost at current scale
- Monthly cost at 1K users is ~$30 with GPT-4.1-mini - negligible
- Having a tested open-source path ready shows the platform's flexibility
- Can switch to open-source if usage grows significantly
