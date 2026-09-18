def ensure_runtime_mode(environment):
    if environment.lower()=="production":
        raise RuntimeError("LOCAL PROTOTYPE ONLY: production hardening is incomplete")

def verification_enabled(value):
    return value == "1"
