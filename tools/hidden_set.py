"""Encrypt / decrypt the hidden held-out set with age (x25519), via pyrage.

    python tools/hidden_set.py keygen    # once: writes secrets/age-key.txt (git-ignored) and config/age-recipient.txt
    python tools/hidden_set.py encrypt   # cases/hidden.jsonl -> cases/hidden.jsonl.age (safe to commit)
    python tools/hidden_set.py decrypt   # cases/hidden.jsonl.age -> cases/hidden.jsonl (needs the key)

The private key never goes in the repo. Put its contents in the GitHub secret AGE_KEY so the
monthly workflow can decrypt (it uses the standard `age` CLI, which reads the same format).
"""
from __future__ import annotations

import sys
from pathlib import Path

from pyrage import decrypt, encrypt, x25519

ROOT = Path(__file__).resolve().parents[1]
KEY = ROOT / "secrets" / "age-key.txt"
RECIPIENT = ROOT / "config" / "age-recipient.txt"
PLAIN = ROOT / "cases" / "hidden.jsonl"
SEALED = ROOT / "cases" / "hidden.jsonl.age"


def keygen() -> None:
    if KEY.exists():
        print(f"{KEY.relative_to(ROOT)} already exists; not overwriting.")
        return
    identity = x25519.Identity.generate()
    KEY.parent.mkdir(exist_ok=True)
    KEY.write_text(f"# public key: {identity.to_public()}\n{identity}\n", encoding="utf-8")
    RECIPIENT.write_text(f"{identity.to_public()}\n", encoding="utf-8")
    print(f"wrote {KEY.relative_to(ROOT)} (secret, git-ignored) and {RECIPIENT.relative_to(ROOT)} (public)")


def do_encrypt() -> None:
    recipient = x25519.Recipient.from_str(RECIPIENT.read_text(encoding="utf-8").strip())
    SEALED.write_bytes(encrypt(PLAIN.read_bytes(), [recipient]))
    print(f"encrypted {sum(1 for l in PLAIN.read_text(encoding='utf-8').splitlines() if l.strip())} cases -> {SEALED.relative_to(ROOT)}")


def do_decrypt() -> None:
    line = next(l for l in KEY.read_text(encoding="utf-8").splitlines() if l.startswith("AGE-SECRET-KEY-"))
    PLAIN.write_bytes(decrypt(SEALED.read_bytes(), [x25519.Identity.from_str(line)]))
    print(f"decrypted -> {PLAIN.relative_to(ROOT)}")


if __name__ == "__main__":
    {"keygen": keygen, "encrypt": do_encrypt, "decrypt": do_decrypt}[sys.argv[1]]()
