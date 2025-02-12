from litellm import Router
import os

# model_list = [{ # list of model deployments 
#     "model_name": "gpt-3.5-turbo", # model alias -> loadbalance between models with same `model_name`
#     "litellm_params": { # params for litellm completion/embedding call 
#         "model": "azure/chatgpt-v-2", # actual model name
#         "api_key": os.getenv("AZURE_API_KEY"),
#         "api_version": os.getenv("AZURE_API_VERSION"),
#         "api_base": os.getenv("AZURE_API_BASE")
#     }
# }, {
#     "model_name": "gpt-3.5-turbo", 
#     "litellm_params": { # params for litellm completion/embedding call 
#         "model": "azure/chatgpt-functioncalling", 
#         "api_key": os.getenv("AZURE_API_KEY"),
#         "api_version": os.getenv("AZURE_API_VERSION"),
#         "api_base": os.getenv("AZURE_API_BASE")
#     }
# }, {
#     "model_name": "gpt-3.5-turbo", 
#     "litellm_params": { # params for litellm completion/embedding call 
#         "model": "gpt-3.5-turbo", 
#         "api_key": os.getenv("OPENAI_API_KEY"),
#     }
# }, {
#     "model_name": "gpt-4", 
#     "litellm_params": { # params for litellm completion/embedding call 
#         "model": "azure/gpt-4", 
#         "api_key": os.getenv("AZURE_API_KEY"),
#         "api_base": os.getenv("AZURE_API_BASE"),
#         "api_version": os.getenv("AZURE_API_VERSION"),
#     }
# }, {
#     "model_name": "gpt-4", 
#     "litellm_params": { # params for litellm completion/embedding call 
#         "model": "gpt-4", 
#         "api_key": os.getenv("OPENAI_API_KEY"),
#     }
# },

# ]

# router = Router(model_list=model_list)

# # openai.ChatCompletion.create replacement
# # requests with model="gpt-3.5-turbo" will pick a deployment where model_name="gpt-3.5-turbo"
# response = await router.acompletion(model="gpt-3.5-turbo", 
#                 messages=[{"role": "user", "content": "Hey, how's it going?"}])

# print(response)

# # openai.ChatCompletion.create replacement
# # requests with model="gpt-4" will pick a deployment where model_name="gpt-4"
# response = await router.acompletion(model="gpt-4", 
#                 messages=[{"role": "user", "content": "Hey, how's it going?"}])

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
        model_list.append({
            "model_name": model,
            "litellm_params": params,
        })
    return Router(model_list=model_list)
