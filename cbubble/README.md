# cBubble 🫧

Custom AI-powered news feed — a self-hosted news aggregator with Instagram-style UI
that uses LLMs to generate verified story abstracts.

## Quick Start

```bash
git clone https://github.com/YOUR_USER/cbubble.git
cd cbubble
./scripts/setup.sh
vim .env   # add CEREBRAS_API_KEY_ABSTRACT and CEREBRAS_API_KEY_VALIDATE
./scripts/run.sh
```

Open http://localhost:8800

## Features

- Custom RSS sources via JSON config
- AI abstracts with fact-check verification (Cerebras — separate keys for generation & validation)
- Daily auto-discovery of available Cerebras models (prefers Qwen)
- Instagram-style dark theme with infinite scroll
- PWA — installable on Android/iOS
- Category filtering
