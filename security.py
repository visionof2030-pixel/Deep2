# security.py
from fastapi import Header, HTTPException
from key_logic import verify_code

def activation_required(
    x_activation_code: str | None = Header(default=None),
    x_activation_code_alt: str | None = Header(default=None, alias="X-Activation-Code")
):
    code = x_activation_code_alt or x_activation_code

    if not code:
        raise HTTPException(status_code=401, detail="Activation code missing")

    verify_code(code.strip())