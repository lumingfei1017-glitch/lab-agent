from chromadb.api.models.Collection import Collection

import chromadb
from jwt import encode

from app.config import BASE_DIR

KB_DIR = BASE_DIR / "data" / "kb"
CHROMA_DIR = BASE_DIR / "data" / "chroma"

_collection = None


def get_collection() -> Collection:
    """向量库初始化"""
    global _collection
    if _collection is not None:
        return _collection

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection(name="lab_kb")
    if col.count() == 0:
        ids = []
        docs = []
        metas = []
        for path in sorted(KB_DIR.glob("*.md")):
            text = path.read_text(encoding="UTF-8").strip()

            if not text:
                continue

            docs.append(text)
            ids.append(path.stem)
            metas.append({"source": path.name})
        if docs:
            col.add(ids=ids, documents=docs, metadatas=metas)

    _collection = col
    return col


def search(query: str):
    """关键字检索"""
    col = get_collection()
    if col.count() == 0:
        return ""
    limit = min(5, col.count())
    res = col.query(query_texts=[query], n_results=limit)
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    distances = (res.get("distances") or [[]])[0]

    """
    以下是检索出来的资料：
    [预约规则.md]
    # 实验室预约规则...
    
    [安全规范.md]
    安全规范....
    """
    score_parts = []
    for doc, meta, dist in zip(docs, metas, distances):
        """0-1,越大越相关"""
        score = 1 / (1 + dist)
        if score < 0.2:
            continue
        name = meta.get("source") or ""
        score_parts.append({"score": score, "content": f"[{name}]\n{doc}"})
    score_parts.sort(key=lambda x: x["score"], reverse=True)
    print(score_parts)
    final_parts = [item["content"] for item in score_parts[:2]]
    return "\n\n".join(final_parts)
