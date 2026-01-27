# Security Fellow Application - Draft Sections

Use these sections as starting points for your application. Customize with your voice and additional context.

---

## Research Interests (for "What topics are you interested in?" question)

My primary research interest is understanding and improving the adversarial robustness of language models, particularly as they become more capable and widely deployed.

I recently built ARIA, an automated red-teaming agent that systematically tests LLM safety mechanisms. I ran a full campaign of 1,078 attacks (77 variants × 14 behaviors) against Claude 3.5 Sonnet and found:

1. **Roleplay and novel strategies dominate**: Roleplay (23.21% ASR) and novel professional framings (21.43%) are 4-6x more effective than persona injection like DAN (6.12%) or combination attacks (3.57%). The most-discussed jailbreak techniques are among the least effective.

2. **Harm calibration works**: Models show calibrated responses—cybersecurity education topics (~30% ASR) are treated as more legitimate than violence or financial crime (~0% ASR). Overall ASR: 12.06%.

3. **Preliminary safety-capability gap**: Small-scale multi-model testing suggests smaller models (Haiku) may be ~2x more vulnerable than larger models (Opus 4.5). Directional finding that needs full-scale validation.

These findings point to concrete improvements: hardening against roleplay/professional framings, expanding adversarial training data beyond DAN-style attacks, and validating whether safety scales with capability.

I'm interested in extending this work to:
- Test against Constitutional Classifiers and other defensive mechanisms
- Develop automated attack generation using LLMs themselves
- Study transfer attacks across model families
- Build real-time adversarial monitoring for production deployments

---

## Relevant Experience (for background/experience questions)

**Technical Background:**
- MS in Information Studies (2025), BS in Computer Science (2020)
- ML engineering experience including distributed training (DDP-LoRA trainer), agentic systems (reflexive LLM agents), and production deployments

**Security Background:**
- Bug bounty experience (2016) understanding attacker mindset
- Built automated security testing tools
- Familiar with offensive security methodology and red-teaming practices

**AI Safety Work:**
- Built ARIA: Automated Red-teaming & Iterative Attack Agent (github.com/rtj1/aria)
- Ran full campaign: 1,078 attacks against Claude 3.5 Sonnet across 14 behaviors with 77 variants, achieving 12.06% overall ASR
- Found roleplay/novel strategies are 4-6x more effective than DAN-style persona injection
- Developed 12 novel attack strategies not well-documented in existing literature

---

## Why Anthropic / Why Security Fellow

I'm drawn to Anthropic's Security Fellow program because it sits at the intersection of my two core interests: AI safety and adversarial security.

The findings from my ARIA project convinced me that LLM security is a critical and underexplored problem. Running 1,078 attacks across 14 behaviors revealed that roleplay framings achieve 23% success rates—4x higher than DAN-style persona injection—yet DAN receives far more attention. The model's defenses also vary significantly by topic: cybersecurity education topics saw ~30% ASR while financial crime saw 0%. We need more systematic approaches to identifying and patching these vulnerabilities.

Anthropic's focus on building safe AI systems, combined with the resources and expertise to work on these problems at scale, makes this the ideal environment for the security research I want to pursue. The fellowship structure—learning from experienced researchers while contributing original work—matches where I am in developing as a safety researcher.

---

## What I Would Bring

1. **Empirical orientation**: I build tools and run experiments rather than theorizing. ARIA demonstrates my ability to systematically test hypotheses about LLM behavior.

2. **Attacker mindset**: From bug bounty experience to building jailbreak taxonomies, I understand how to think like an adversary—essential for security research.

3. **Engineering skills**: I can build production-quality tools (APIs, dashboards, databases) that make research scalable and reproducible.

4. **Novel discoveries**: Full campaign confirmed roleplay/novel strategies are 4-6x more effective than DAN-style attacks (23%/21% vs 6% ASR), and harm calibration works (0-38% ASR range). Preliminary multi-model testing suggests smaller models may be ~2x more vulnerable.

5. **Communication**: I document and share findings (Alignment Forum post, open-source code) to benefit the broader safety community.

---

## Potential Fellowship Research Directions

Based on my ARIA work, here are research directions I'd propose exploring:

1. **Roleplay/Professional Framing Hardening**: Develop adversarial training data targeting roleplay and professional framings—the attack families that actually work, rather than the DAN-style attacks that are already well-defended.

2. **Safety-Capability Scaling Laws**: Systematically characterize how adversarial robustness changes with model scale. Validate whether the preliminary ~2x gap holds across model families.

3. **Automated Red-Teaming at Scale**: Use LLMs to generate novel attack variants, creating a continuous adversarial testing pipeline.

4. **Constitutional Classifiers Evaluation**: Test how Constitutional Classifiers perform against the attack taxonomy I've developed.

5. **Real-time Jailbreak Detection**: Build monitoring systems that detect adversarial prompts in production, enabling dynamic defense.

---

## Links

- ARIA Code: https://github.com/rtj1/aria
- Blog Post: [Link to Alignment Forum post when published]
- Other Projects: https://github.com/rtj1

---

*Last updated: January 2026*
