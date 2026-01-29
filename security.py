# security.py
from fastapi import Header, HTTPException
from key_logic import verify_code

def activation_required(
    x_activation_code: str = Header(..., alias="X-Activation-Code")
):
    if not x_activation_code:
        raise HTTPException(status_code=401, detail="Activation code missing")

    verify_code(x_activation_code)