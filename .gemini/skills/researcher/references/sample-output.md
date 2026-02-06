# Sample Research Brief Output (with Parallel Sub-Agent Research)

**Input:** "Write a blog post about AI in Healthcare"

---

## Phase 1: Sub-topic Identification

After analyzing the main topic "AI in Healthcare", the following sub-topics were identified:

1. AI Diagnostics & Medical Imaging
2. Drug Discovery & Development
3. Patient Care & Virtual Health
4. Regulatory & Ethical Considerations

## Phase 2: Parallel Sub-Agent Execution

Four sub-agents were spawned simultaneously using the `browser_subagent` tool:

```
browser_subagent 1 → Researching "AI Diagnostics & Medical Imaging"
browser_subagent 2 → Researching "Drug Discovery & Development"
browser_subagent 3 → Researching "Patient Care & Virtual Health"
browser_subagent 4 → Researching "Regulatory & Ethical Considerations"
```

## Phase 3: Compiled Output

---

```markdown
# Research Brief: AI in Healthcare

## Executive Summary
Artificial Intelligence is revolutionizing healthcare across diagnostics, drug discovery, patient care, and operational efficiency. The global AI healthcare market is projected to reach $188 billion by 2030, with medical imaging AI leading adoption. However, regulatory frameworks and ethical considerations around bias and privacy remain critical challenges.

## Sub-Topics Researched
1. AI Diagnostics & Medical Imaging
2. Drug Discovery & Development
3. Patient Care & Virtual Health
4. Regulatory & Ethical Considerations

---

## AI Diagnostics & Medical Imaging

### Key Facts
- AI can analyze medical images 30x faster than radiologists (Source: Nature Medicine, 2024)
- FDA has approved over 700 AI/ML-enabled medical devices as of 2024 (Source: FDA)
- Deep learning models achieve 94.5% accuracy in detecting diabetic retinopathy (Source: Google Health)

### Statistics & Data
- Medical imaging AI market: $2.1B in 2024, growing 35% annually (Source: Grand View Research)
- AI-assisted diagnosis reduces diagnostic errors by 11% (Source: JAMA, 2024)

### Recent Developments
- Google's Med-PaLM 2 achieves expert-level performance on medical licensing exams (2024)
- Hospitals report 40% reduction in radiology report turnaround time with AI (2024)

---

## Drug Discovery & Development

### Key Facts
- AI can reduce drug discovery timeline from 10-15 years to 3-5 years (Source: McKinsey)
- Over 150 AI-discovered drugs are currently in clinical trials (Source: BioPharma Dive)
- AI models can screen 1 billion compounds in hours vs. years traditionally (Source: MIT)

### Statistics & Data
- AI drug discovery market: $1.5B in 2024 (Source: Markets and Markets)
- Average cost savings: 30-50% in early-stage drug discovery (Source: Deloitte)

### Recent Developments
- Insilico Medicine's AI-discovered drug enters Phase 2 trials for fibrosis (2024)
- Pfizer partners with AI startups to accelerate oncology drug pipeline (2024)

---

## Patient Care & Virtual Health

### Key Facts
- AI chatbots handle 70% of routine patient inquiries (Source: Accenture Health)
- Remote patient monitoring with AI reduces hospital readmissions by 25% (Source: Cleveland Clinic)
- Predictive AI identifies high-risk patients 48 hours before deterioration (Source: Epic Systems)

### Statistics & Data
- Virtual health visits increased 3800% since 2019 (Source: McKinsey)
- AI-powered triage reduces ER wait times by 35% (Source: Johns Hopkins)

### Recent Developments
- Major health systems deploy ambient AI for clinical documentation (2024)
- AI wearables gain FDA clearance for continuous health monitoring (2024)

---

## Regulatory & Ethical Considerations

### Key Facts
- FDA's Digital Health Center of Excellence oversees AI medical device approvals (Source: FDA)
- EU AI Act classifies medical AI as "high-risk" requiring strict compliance (Source: EU Commission)
- Studies show AI diagnostic tools exhibit racial bias in up to 40% of cases (Source: Stanford HAI)

### Statistics & Data
- 78% of healthcare executives cite regulatory uncertainty as top AI barrier (Source: HIMSS)
- Only 15% of hospitals have formal AI governance frameworks (Source: CHIME)

### Recent Developments
- WHO releases global guidance on AI ethics in healthcare (2024)
- California passes AI transparency law for healthcare algorithms (2024)

---

## Cross-Cutting Insights
- **Speed vs Safety tension**: AI dramatically accelerates diagnostics and drug discovery, but regulatory frameworks struggle to keep pace
- **Data as foundation**: All AI healthcare applications depend on large, diverse training datasets—highlighting the importance of data sharing initiatives
- **Human-AI collaboration**: Most successful implementations augment rather than replace clinicians

## Interesting Angles for Writing
- The race between AI innovation and healthcare regulation
- How AI is democratizing healthcare access in underserved areas
- The hidden bias problem in medical AI
- Real patient stories: lives saved (or complicated) by AI diagnosis

## Sources

- [Nature Medicine - AI in Medical Imaging](https://nature.com/nm) - Peer-reviewed research on AI diagnostics
- [FDA AI/ML Medical Devices](https://fda.gov) - Official regulatory database
- [McKinsey Healthcare AI Report](https://mckinsey.com) - Industry analysis
- [Stanford HAI Healthcare Study](https://hai.stanford.edu) - Bias and ethics research
- [JAMA AI Diagnostics Study](https://jama.com) - Clinical outcomes data
- [Google Health Research](https://health.google) - Diabetic retinopathy AI
- [BioPharma Dive AI Drug Discovery](https://biopharmadive.com) - Pipeline tracking
- [HIMSS Digital Health Survey](https://himss.org) - Healthcare executive insights
- [WHO AI Ethics Guidelines](https://who.int) - Global policy framework
```

---

## What Makes This Good

- **Parallel research execution** - 4 sub-agents worked simultaneously
- **Comprehensive coverage** - Each sub-topic deeply researched
- **9 distinct sources** across multiple sub-topics
- **Rich statistics** - Multiple data points per sub-topic
- **Cross-cutting insights** - Connections identified between sub-topics
- **Actionable angles** - Clear directions for the Writer skill
- **Clean structure** - Easy for downstream skills to consume
