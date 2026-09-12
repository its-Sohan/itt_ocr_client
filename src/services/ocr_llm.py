import base64
import os
import httpx
from src.config_store import load_config, update_usage_stats
from src.styles import safe_bengali_normalize

# Developer-configured internal OCR System Prompt
# Stays strictly within code; cannot be viewed or altered by end-users in UI settings.
OCR_BASE_PROMPT = (
    "You are an expert high-precision OCR and document transcription engine. "
    "Transcribe all visible text, handwritten notes, numbers, tables, and punctuation from this image accurately. "
    "Support multilingual scripts including English, Bengali (বাংলা), Assamese, Hindi, and others accurately with correct conjuncts and diacritics. "
    "Output clean text or Markdown only without introductory pleasantries or commentary."
)

OUTPUT_MODES = {
    "document": {
        "label": "Document",
        "description": "Standard prose, headings & paragraphs",
        "system_instruction": (
            "Preserve structural elements such as headings, lists, tables, and paragraphs where applicable. "
            "Maintain natural reading order and document hierarchy."
        ),
        "user_prompt": "Please transcribe and extract all text and layout elements present in this image preserving original structure.",
    },
    "spreadsheet": {
        "label": "Spreadsheet",
        "description": "Itemized tables, invoices & receipts (Excel ready)",
        "system_instruction": (
            "You are a specialized financial and tabular document extractor. "
            "Identify all tables, itemized billing rows, quantities, rates, unit prices, descriptions, and numerical totals. "
            "Format all tabular sections strictly as clean Markdown tables with header rows (`| Col 1 | Col 2 |`) so they can be exported to CSV or pasted into Excel. "
            "For non-table document metadata (such as invoice number, date, vendor name, buyer name, total amount), format them as a concise 2-column key-value table (`| Field | Value |`). "
            "Do NOT merge separate columns into combined text paragraphs."
        ),
        "user_prompt": "Extract all tabular data, line items, and document metadata from this image strictly into formatted tables suitable for spreadsheets.",
    },
    "key_value": {
        "label": "Key-Value Form",
        "description": "Structured label-value pairs (IDs, forms, certificates)",
        "system_instruction": (
            "You are a structured data and form extractor. "
            "Extract every form field, label, identifier, and value present in the image. "
            "Format strictly as clean key-value pairs (`Field Name: Value`). "
            "Group related fields under concise markdown headings. "
            "Do not output conversational commentary."
        ),
        "user_prompt": "Extract all form fields, labels, and corresponding values from this image as structured key-value pairs.",
    },
    "raw_text": {
        "label": "Raw Text",
        "description": "Clean continuous unformatted text",
        "system_instruction": (
            "You are a pure OCR transcription engine. "
            "Transcribe all text in natural reading order. "
            "Output pure plain text only with zero markdown formatting, zero table pipes, zero bold asterisks, and zero commentary."
        ),
        "user_prompt": "Transcribe all text from this image as raw unformatted plain text.",
    },
}

OCR_SYSTEM_PROMPT = OCR_BASE_PROMPT

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

async def extract_text_with_llm(file_path: str, mode: str = "document") -> str:
    """
    Sends the image to an OpenAI-compatible vision endpoint with mode-specific instructions
    (supports OpenAI GPT-4o, OpenRouter, Groq, Ollama, Gemini API compatible, etc.)
    """
    config = load_config()
    api_key = config.get("api_key", "").strip()
    raw_base = config.get("base_url", "https://api.openai.com/v1").strip()
    clean_base = raw_base.rstrip("/")
    if clean_base.endswith("/chat/completions"):
        url = clean_base
    else:
        url = f"{clean_base}/chat/completions"

    model_name = config.get("model_name", "gpt-4o-mini").strip()

    if not api_key and "localhost" not in clean_base and "127.0.0.1" not in clean_base:
        raise ValueError("API Key is missing. Please configure your API Key in Settings.")

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
    if "openrouter" in clean_base.lower():
        headers["HTTP-Referer"] = "https://github.com/its-Sohan/itt_ocr_client"
        headers["X-Title"] = "ITT OCR Client"

    mode_info = OUTPUT_MODES.get(mode, OUTPUT_MODES["document"])
    effective_system_prompt = f"{OCR_BASE_PROMPT}\n\n[OUTPUT FORMAT DIRECTIVE: {mode_info['label'].upper()}]\n{mode_info['system_instruction']}"
    user_instruction = mode_info["user_prompt"]

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": effective_system_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_instruction,
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

    try:
        async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.ConnectError as exc:
        update_usage_stats(characters=0, success=False)
        err_msg = str(exc)
        if "ssl" in err_msg.lower() or "tlsv1" in err_msg.lower() or "certificate" in err_msg.lower():
            raise RuntimeError(
                f"SSL/TLS Connection Error on {clean_base}: The endpoint server rejected the secure handshake ({err_msg}). "
                "Please verify your Endpoint URL in Settings or confirm the server has a valid SSL certificate."
            ) from exc
        raise RuntimeError(
            f"Cannot connect to {clean_base}: Connection refused or host unreachable ({err_msg}). "
            "Please check the Endpoint URL in Settings."
        ) from exc
    except httpx.TimeoutException as exc:
        update_usage_stats(characters=0, success=False)
        raise RuntimeError(
            f"Request timed out after 90s contacting {clean_base}. Please check your connection or model provider."
        ) from exc
    except httpx.RequestError as exc:
        update_usage_stats(characters=0, success=False)
        raise RuntimeError(f"Network error while calling {url}: {exc}") from exc

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
    extracted_text = safe_bengali_normalize(extracted.strip())
    update_usage_stats(characters=len(extracted_text), success=True)
    return extracted_text
