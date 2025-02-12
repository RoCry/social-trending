from litellm import Router
import os
from utils import logger


def make_router():
    model = os.getenv("LITELLM_MODEL")
    api_keys = os.getenv("LITELLM_API_KEY").split(",")
    base_url = os.getenv("LITELLM_BASE_URL") or None
    model_list = []
    for api_key in api_keys:
        params = {
            "model": model,
            "api_key": api_key,
        }
        if base_url:
            params["base_url"] = base_url
        model_list.append(
            {
                "model_name": model,
                "litellm_params": params,
            }
        )
    logger.info(
        f"Model: {model}, API Keys: {len(api_keys)}, {[k[:4]+"***" for k in api_keys]}, Base URL: {base_url}"
    )
    return Router(model_list=model_list)
