import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
import os
import glob

model = SentenceTransformer("all-MiniLM-L6-v2")
#model = SentenceTransformer("./model")

faiss_index = faiss.IndexFlatL2(384)
stored_texts = []

def store_results_to_faiss():
    global stored_texts
    stored_texts.clear()
    faiss_index.reset()

    for file in glob.glob("data/*.csv"):
        df = pd.read_csv(file)
        for _, row in df.iterrows():
            text = (
                f"{row['Job Title']} | Remote: {row['Remote Testing']} | Adaptive: {row['Adaptive/IRT']} | "
                f"Duration: {row.get('Duration', '')} | Test Type: {row.get('Test Type', row.get('Keys', ''))} | "
                f"Description: {row.get('Description', '')}"
            )
            embedding = model.encode([text])
            faiss_index.add(embedding)
            stored_texts.append((text, row.get("Link", "#")))

def query_faiss(query, top_k=10):
    query_embedding = model.encode([query])
    D, I = faiss_index.search(query_embedding, top_k)
    results = []
    for idx in I[0]:
        if idx < len(stored_texts):
            text, link = stored_texts[idx]
            results.append((text, link))
    return results

def init_faiss():
    faiss_index.reset()
    stored_texts.clear()
