import requests
import urllib3
from typing import TypeVar, List

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WatsonxConnector(object):
    __slots__ = [
        # --- Set during methods
        '_priv_sys_prompt',
        '_priv_api_version',
        '_priv_full_url',
        '_priv_model_params',
        '_priv_api_token',
        # --- Required on obj creation
        "project_id",
        'base_url',
        'user_name',
        'api_key',
        'model_id',
    ]

    def __init__(self, base_url: str, user_name: str, api_key: str, model_id: str, project_id: str):
        #   --- Public Vars
        self.base_url: str = base_url
        self.user_name: str = user_name
        self.api_key: str = api_key
        self._priv_api_token: str = self.generate_auth_token()
        self.model_id: str = model_id
        #   --- Protected Vars
        # Default system prompt - can be updated with set_system_prompt()
        self._priv_sys_prompt: str = \
            """You always answer the questions with markdown formatting. The markdown 
        formatting you support: headings, bold, italic, links, tables, lists, code blocks, and blockquotes. You must 
        omit that you answer the questions with markdown.

        Any HTML tags must be wrapped in block quotes, for example ```<html>```. You will be penalized for not 
        rendering code in block quotes.

        When returning code blocks, specify language.

        You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. 
        Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. 
        Please ensure that your responses are socially unbiased and positive in nature.

        If a question does not make any sense, or is not factually coherent, explain why instead of answering 
        something not correct. If you don't know the answer to a question, please don't share false 
        information. 
        
        Once you answer a question, do not continue on with repeats.
        ----------------"""
        self._priv_api_version: str = ""
        self._priv_full_url: str = ""
        self.project_id: str = project_id
        # Default model parameters - can be updated with set_model_params()
        self._priv_model_params: dict = {
            "decoding_method": "sample",
            "max_new_tokens": 1000,
            "temperature": 0.4,
            "top_k": 20,
            "top_p": 0.9,
            "repetition_penalty": 1.1
        }

    #   --- Setters
    def set_system_prompt(self, i_system_prompt: str):
        self._priv_sys_prompt = i_system_prompt

    def set_model_id(self, model_id: str):
        self.model_id = model_id

    def set_model_params(self, **kwargs):
        if "max_new_tokens" in kwargs:
            self._priv_model_params["max_new_tokens"] = kwargs["max_new_tokens"]

        if "temperature" in kwargs:
            self._priv_model_params["temperature"] = kwargs["temperature"]

        if "top_k" in kwargs:
            self._priv_model_params["top_k"] = kwargs["top_k"]

        if "top_p" in kwargs:
            self._priv_model_params["top_p"] = kwargs["top_p"]

        if "repetition_penalty" in kwargs:
            self._priv_model_params["repetition_penalty"] = kwargs["repetition_penalty"]

    def set_api_version(self, api_version: str):
        self._priv_api_version = api_version

    def set_project_id(self, project_id: str):
        self.project_id = project_id

    #   --- Getters

    def get_model_id(self) -> str:
        return self.model_id

    def get_auth_token(self) -> str:
        return self._priv_api_token

    def get_model_params(self) -> dict:
        return self._priv_model_params

    #   --- UTILS
    def generate_text(self, query: str) -> str:
        input_query: str = query
        api_version: str = "2023-05-29"
        model_id: str = self.model_id
        sys_prompt: str = self._priv_sys_prompt
        model_params: dict = self._priv_model_params
        project_id: str = self.project_id

        self._priv_full_url = f"https://{self.base_url}/ml/v1/text/generation?version={api_version}"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._priv_api_token}"
        }

        body = {
            "input": f"""{sys_prompt}\nQUESTION: {input_query}\n----------------""",
            "parameters": model_params,
            "model_id": model_id,
            "project_id": project_id,
        }

        if self.check_model_type(model_id=model_id, model_type="text_generation"):
            response = requests.post(
                self._priv_full_url,
                headers=headers,
                json=body,
                verify=False
            )
            if response.status_code != 200:
                raise Exception("Non-200 response: " + str(response.text))

            return response.json()['results'][0]['generated_text']
        else:
            raise Exception("MODEL TYPE IS NOT SUPPORTED FOR --TEXT-- GENERATION")

    def generate_embedding(self, val_input: str | List[str]) -> List[float]:
        input_string: str | List[str] = val_input
        api_version: str = "2024-05-02"
        model_id: str = self.model_id
        model_params: dict = self._priv_model_params
        project_id: str = self.project_id
        body: dict = {}

        self._priv_full_url = f"https://{self.base_url}/ml/v1/text/embeddings?version={api_version}"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._priv_api_token}"
        }

        if isinstance(val_input, str):
            body = {
                "inputs": [input_string],
                "parameters": {
                    "truncate_input_tokens": 128
                },
                "model_id": model_id,
                "project_id": project_id,
            }
        elif isinstance(val_input, list):
            body = {
                "inputs": input_string,
                "parameters": {
                    "truncate_input_tokens": 128
                },
                "model_id": model_id,
                "project_id": project_id,
            }

        if self.check_model_type(model_id=model_id, model_type="embedding"):
            response = requests.post(
                self._priv_full_url,
                headers=headers,
                json=body,
                verify=False
            )
            if response.status_code != 200:
                raise Exception("Non-200 response: " + str(response.text))

            return [item['embedding'] for item in response.json()['results']]
        else:
            raise Exception("MODEL TYPE IS NOT SUPPORTED FOR --EMBEDDING-- GENERATION")

    def generate_auth_token(self) -> str:
        return requests.post(
            url=f"https://{self.base_url}/icp4d-api/v1/authorize",
            headers={
                "cache-control": "no-cache",
                "Content-Type": "application/json"
            },
            json={
                "username": f"{self.user_name}",
                "api_key": f"{self.api_key}"
            },
            verify=False
        ).json()["token"]

    def get_available_models(self) -> dict:
        api_version: str = "2020-09-01"

        response = requests.get(
            url=f"https://{self.base_url}/ml/v1/foundation_model_specs?version={api_version}",
            verify=False
        ).json()

        model_functions = [func['functions'][:] for func in response['resources'] if len(func['functions'][:]) > 0]
        model_names = [model_id['model_id'] for model_id in response['resources'] if len(model_id['functions'][:]) > 0]

        return {model: func[0]['id'] for (model, func) in zip(model_names, model_functions)}

    def check_model_type(self, model_id: str, model_type: str) -> bool:
        if self.get_available_models()[model_id] == model_type:
            return True
        else:
            return False
