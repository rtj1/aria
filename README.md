# ARIA - Automated Red-teaming & Iterative Attack Agent

A research tool for automated LLM red-teaming, designed to discover and analyze jailbreak vulnerabilities in large language models.

## Key Findings

Testing 77 attack variants across Claude's model family revealed:

1. **Safety-Capability Gap**: Haiku (smallest) is 2x more vulnerable than Opus 4.5 (largest)
2. **Professional Framing Works**: A novel "expert consultation" attack achieved 67% ASR—higher than traditional jailbreaks
3. **Harm Calibration**: Models show stronger refusals for higher-harm requests (0% ASR for CBRN)

---

## Overview

ARIA automates the process of testing LLM safety mechanisms by:

1. **Generating adversarial prompts** using 10 attack strategy families
2. **Testing against target models** (Claude Haiku, Sonnet, Opus)
3. **Evaluating responses** to determine attack success
4. **Learning from failures** using the Reflexion pattern
5. **Tracking metrics** across attack campaigns

## Features

- **10 Attack Strategies, 77 Variants**: Roleplay, Encoding, Logic Trap, Prefix Injection, Hypothetical, Multi-turn, Combination, Persona, Context Manipulation, Novel
- **Multi-Model Testing**: Test across Claude model family
- **Reflexion Learning**: Analyzes failures to improve future attacks
- **Attack Memory**: ChromaDB-powered similarity search
- **Metrics Dashboard**: Real-time ASR tracking
- **API & Dashboard**: FastAPI backend + Streamlit visualization

## Installation

```bash
# Clone the repository
git clone https://github.com/rtj1/aria.git
cd aria

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your Anthropic API key
```

## Quick Start

### Run a Demo
```bash
python main.py demo
```

### Single Attack
```bash
python main.py attack "explain how to pick a lock" -s roleplay -v author
```

### Attack Campaign
```bash
python main.py campaign -f data/behaviors/sample_behaviors.txt -m 3
```

### Start Dashboard
```bash
python main.py dashboard
# Open http://localhost:8501
```

## Attack Strategies

| Strategy | Variants | Description |
|----------|----------|-------------|
| roleplay | 8 | Fictional scenarios (author, researcher, actor) |
| encoding | 6 | Base64, ROT13, leetspeak obfuscation |
| logic_trap | 8 | False premises, authority override |
| prefix_injection | 8 | Response format manipulation |
| hypothetical | 9 | Thought experiments, alternate universes |
| multi_turn | 5 | Gradual escalation sequences |
| combination | 6 | Layered multi-technique attacks |
| persona | 7 | DAN, jailbroken persona injection |
| context_manipulation | 8 | False history, context injection |
| **novel** | 12 | Experimental approaches (expert_consultation, etc.) |

## Results Summary

### Model Vulnerability (Novel Attacks)

| Model | ASR |
|-------|-----|
| Claude 3.5 Haiku | 33% |
| Claude Sonnet 4 | 25% |
| Claude Opus 4.5 | 17% |

### Top Performing Attacks

| Attack | ASR |
|--------|-----|
| expert_consultation | 67% |
| hypothetical/thought_experiment | 40% |
| roleplay/author | 30% |

## Project Structure

```
aria/
├── src/
│   ├── agent/           # Core agent logic
│   │   ├── aria_agent.py
│   │   ├── strategy_selector.py
│   │   └── reflexion.py
│   ├── strategies/      # Attack strategy implementations
│   ├── evaluation/      # Response evaluation
│   ├── targets/         # Target model wrappers
│   └── memory/          # ChromaDB attack storage
├── api/                 # FastAPI server
├── dashboard/           # Streamlit UI
├── data/               # Behaviors and results
├── experiments/        # Experiment configs and outputs
└── main.py             # CLI entry point
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/attack` | POST | Execute single attack |
| `/campaign` | POST | Start attack campaign |
| `/strategies` | GET | List available strategies |
| `/metrics` | GET | Get campaign metrics |
| `/successful-attacks` | GET | Get successful attacks |

## Research Context

This tool was built as part of preparation for the **Anthropic Security Fellow** program.

### Relevant Anthropic Research

- [Constitutional Classifiers](https://www.anthropic.com/research/constitutional-classifiers) - Jailbreak defense
- [Many-shot Jailbreaking](https://www.anthropic.com/research/many-shot-jailbreaking) - Attack patterns

## Ethical Use

This tool is for authorized security research only.

- Use only on systems you have permission to test
- Report vulnerabilities through proper channels
- Do not use for malicious purposes

## License

MIT License

---

**Author**: Tharun Jagarlamudi
**GitHub**: [@rtj1](https://github.com/rtj1)
