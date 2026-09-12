import base64
import os
import httpx
from src.config_store import load_config, update_usage_stats

def get_mime_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in (".png",):
        return "image/png"
    elif ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    elif ext in (".webp",):
        return "image/webp"
    elif ext in (".gif",):
        return "image/gif"
    elif ext in (".bmp",):
        return "image/bmp"
    return "image/jpeg"

def encode_image_base64(file_path: str) -> str:
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

async def extract_text_with_llm(file_path: str) -> str:
    """
    Sends the image to an OpenAI-compatible vision endpoint
    (supports OpenAI GPT-4o, OpenRouter, Groq, Ollama, Gemini API compatible, etc.)
    """
    config = load_config()
    api_key = config.get("api_key", "").strip()
    base_url = config.get("base_url", "https://api.openai.com/v1").rstrip("/")
    model_name = config.get("model_name", "gpt-4o-mini").strip()
    system_prompt = config.get("system_prompt", "Extract all visible text from this image accurately.")

    if not api_key and "localhost" not in base_url and "127.0.0.1" not in base_url:
        raise ValueError("API Key is missing. Please set your API Key in the top-left Settings.")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Image file not found: {file_path}")

    mime_type = get_mime_type(file_path)
    base64_data = encode_image_base64(file_path)
    data_url = f"data:{mime_type};base64,{base64_data}"

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please transcribe and extract all text and tabular data present in this image."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
    }

    url = f"{base_url}/chat/completions"

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            error_detail = response.text
            try:
                err_json = response.json()
                if "error" in err_json and "message" in err_json["error"]:
                    error_detail = err_json["error"]["message"]
            except Exception:
                pass
            update_usage_stats(characters=0, success=False)
            raise RuntimeError(f"LLM API Error ({response.status_code}): {error_detail}")

        result_json = response.json()
        choices = result_json.get("choices", [])
        if not choices:
            update_usage_stats(characters=0, success=False)
            raise RuntimeError("LLM API returned an empty choices list.")

        extracted = choices[0].get("message", {}).get("content", "")
        extracted_text = extracted.strip()
        update_usage_stats(characters=len(extracted_text), success=True)
        return extracted_text
