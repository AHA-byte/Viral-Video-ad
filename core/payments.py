from .config import STRIPE_BASIC_URL, STRIPE_PRO_URL

def get_basic_plan_url() -> str:
    return STRIPE_BASIC_URL or "#"

def get_pro_plan_url() -> str:
    return STRIPE_PRO_URL or "#"
