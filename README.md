# envault

> Lightweight utility to encrypt and manage `.env` files with team-sharing support.

---

## Installation

```bash
pip install envault
```

---

## Usage

**Encrypt a `.env` file:**

```bash
envault encrypt .env --output .env.vault
```

**Decrypt and load into your environment:**

```bash
envault decrypt .env.vault --output .env
```

**Share with your team by committing `.env.vault` and distributing the key securely:**

```python
from envault import load_vault

load_vault(".env.vault", key="your-secret-key")

import os
print(os.getenv("DATABASE_URL"))
```

**Generate a new encryption key:**

```bash
envault keygen
```

---

## Workflow

1. Add `.env` to `.gitignore`
2. Encrypt with `envault encrypt .env`
3. Commit `.env.vault` to version control
4. Share the key with teammates via a secrets manager
5. Teammates decrypt locally with `envault decrypt .env.vault`

---

## License

MIT © [envault contributors](https://github.com/yourorg/envault)