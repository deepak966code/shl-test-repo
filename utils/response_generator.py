import requests

def generate_response(user_query, results):
    MISTRAL_API_KEY = "KjZX2f53cZ9uoVtzchhO3mK2ofSkD7XC"

    if not results:
        return "<p>❌ No relevant assessments found.</p>"

    def limit_context_by_word_count(context, word_limit=1200):
        words = context.split()
        if len(words) <= word_limit:
            return context
        return " ".join(words[:word_limit])

    # Construct rich context
    def safe_get(r, idx):
        return r[idx] if len(r) > idx and r[idx] else "nil"

    context = "\n\n".join([
        f"""Assessment Name: {safe_get(r, 0)}
    Link: {safe_get(r, 1)}
    Remote Testing: {safe_get(r, 2)}
    Adaptive/IRT: {safe_get(r, 3)}
    Test Type: {safe_get(r, 4)}
    Duration: {safe_get(r, 5)}
    Description: {safe_get(r, 6)}"""
        for r in results
    ])

    
    context = limit_context_by_word_count(context)
    prompt = f"""
You are a career assistant. Based on the query: "{user_query}" and the context, return the top 5–10 recommended SHL assessments.
There must be atleast 5 recommendation if there are more than 5 given to you.

⚠️ Return only a valid HTML <table> element. No JSON, Markdown, or extra text.

The table must contain the following columns:
- Assessment Name
- Link (clickable anchor tag)
- Remote Testing (Yes/No)
- Adaptive/IRT (Yes/No)
- Duration (in minutes)
- Test Type (e.g., A, B, etc.)

⚠️ Ensure every row has exactly 6 columns — one for each field — and no rows should be missing any of the columns.
 Use plain <table>, <tr>, <td>, and <a href> tags only.

Context:
{context}
"""
    print("======== LLM CONTEXT START ========")
    print(context)
    print("======== LLM CONTEXT END ==========")
    
    print("======== LLM PROMPT START ========")
    print(prompt)
    print("======== LLM PROMPT END ==========")



    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
        json={
            "model": "open-mistral-7b",
            "messages": [
                {"role": "system", "content": "You are an assistant that recommends assessments based on context."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1024,
            "temperature": 0.3,
        },
    )

    if response.status_code == 200:
        llm_content = response.json()["choices"][0]["message"]["content"]
        print("🔍 Raw LLM response:\n", llm_content)  # 👈 This will print it in terminal
        return llm_content

    else:
        return f"<p>❌ LLM error: {response.status_code} - {response.text}</p>"
