from fastapi import Header
from key_logic import verify_code

def activation_required(x_activation_code: str = Header(...)):
    verify_code(x_activation_code)