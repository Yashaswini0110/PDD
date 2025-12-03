from __future__ import annotations
from pathlib import Path
import json
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

EMB_ROOT = Path("embeddings")
EMB_ROOT.mkdir(parents=True, exist_ok=True)

def _paths(job_id: str):
    base = EMB_ROOT / f"{job_id}"
    vec_path = base.with_suffix(".tfidf.pkl")
    mat_path = base.with_suffix(".matrix.pkl")
    meta_path = base.with_suffix(".meta.json")
    return vec_path, mat_path, meta_path

def build_index(job_id: str, clauses: list[dict]) -> dict:
    texts = [c["text"] for c in clauses]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1,2),      # unigrams + bigrams for better recall
        max_features=20000,     # small, deploy-friendly
    )
    X = vectorizer.fit_transform(texts)      # sparse (N x V)

    vec_path, mat_path, meta_path = _paths(job_id)
    joblib.dump(vectorizer, vec_path)
    joblib.dump(X, mat_path)
    meta = [{"id": c["id"], "page": c["page"]} for c in clauses]
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    return {"rows": X.shape[0], "cols": X.shape[1]}

def search(job_id: str, query: str, clauses: list[dict], top_k: int = 5) -> list[dict]:
    vec_path, mat_path, meta_path = _paths(job_id)
    if not (vec_path.exists() and mat_path.exists() and meta_path.exists()):
        raise FileNotFoundError("index not built")

    vectorizer = joblib.load(vec_path)
    X = joblib.load(mat_path)  # sparse matrix
    meta = json.loads(Path(meta_path).read_text())

    qv = vectorizer.transform([query])  # (1 x V)
    scores = cosine_similarity(qv, X).ravel()  # (N,)

    top_k = max(1, int(top_k))
    idxs = scores.argsort()[::-1][:top_k]

    # Build a lookup dict by clause ID for safe matching
    clauses_by_id = {c.get("id"): c for c in clauses}

    out = []
    for i in idxs:
        # Use meta to get the ID, then look up in clauses dict
        if i < len(meta):
            meta_item = meta[i]
            clause_id = meta_item.get("id")
            c = clauses_by_id.get(clause_id)
            if c:
                out.append({
                    "id": c.get("id", "N/A"),
                    "page": c.get("page", meta_item.get("page", "N/A")),
                    "text": c.get("text", ""),
                    "score": float(scores[i]),
                })
    return out