# cBubble 🫧

Custom AI-powered news feed — a self-hosted news aggregator with Instagram-style UI
that uses LLMs to generate verified story abstracts.

## Quick Start

```bash
git clone https://github.com/agathebower/cbubble.git
cd cbubble
./scripts/setup.sh
vim .env   # add CEREBRAS_API_KEY and/or GROQ_API_KEY
./scripts/run.sh
```

Open http://localhost:8800

## Features

- Custom RSS sources via JSON config
- AI abstracts with fact-check verification (Cerebras / Groq)
- Automatic provider fallback
- Instagram-style dark theme with infinite scroll
- PWA — installable on Android/iOS
- Category filtering
