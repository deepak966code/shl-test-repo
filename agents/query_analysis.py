import requests
import json
from agents import keywords_config as kc  # your predefined lists

def mistral_keywords(query):
    MISTRAL_API_KEY = "KjZX2f53cZ9uoVtzchhO3mK2ofSkD7XC"

    system_prompt = f"""
You are an assistant that only tags job-related attributes from a pre-cleaned list of words.

Return a valid JSON with:
- keywords: list of relevant terms from the query (lemmatized or clean) and Do not generate any extra word from yourself , use only those mentioned in query.
NEVER make up words. Just extract key terms from the user query.
"""

    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
        json={
            "model": "open-mistral-7b",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "max_tokens": 300,
            "temperature": 0.3,
        },
    )

    result = response.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(result).get("keywords", [])
    except Exception:
        return []

def find_matches(llm_keywords, vocab_list):
    return [
        option for option in vocab_list
        if any(k.lower() in option.lower() or option.lower() in k.lower() for k in llm_keywords)
    ]

def analyze_query_with_mistral(query):
    keywords = mistral_keywords(query)

    return {
        "keywords": keywords,
        "job_family": find_matches(keywords, kc.job_family),
        "job_level": find_matches(keywords, kc.job_level),
        "industry": find_matches(keywords, kc.industry),
        "language": find_matches(keywords, kc.languages),
        "job_category": find_matches(keywords, kc.job_category),
    }
