"""query_clause —— CNAS-CL01:2018 条款受控查询。

支持两种输入：
- 条款号（如 "7.4"、"4.1"），也支持章节号（如 "7"、"第7章"）返回该章条款目录
- 关键词（如 "样品"、"期间核查"），按标题/关键词/意图加权检索
"""

import re

from tools._loader import OUTPUT_DISCLAIMER, load_clauses

_CLAUSE_ID_RE = re.compile(r"^(\d+(?:\.\d+)*)$")
_CHAPTER_RE = re.compile(r"^第?(\d+)章?$")

# 命中权重：标题 > 关键词 > 意图 > 落地要点
_WEIGHTS = (("title", 5), ("keywords", 3), ("intent", 2), ("points", 1))
MAX_RESULTS = 5


def _clause_brief(clause: dict) -> dict:
    """条款条目的对外精简结构。"""
    return {
        "clause_id": clause["id"],
        "title": clause["title"],
        "intent": clause["intent"],
        "implementation_points": clause["points"],
        "keywords": clause["keywords"],
    }


def _search_by_keyword(query: str, clauses: list[dict]) -> list[dict]:
    """按关键词加权检索，返回按得分排序的条款列表。"""
    scored = []
    for clause in clauses:
        score = 0
        for field, weight in _WEIGHTS:
            values = clause.get(field) or []
            if isinstance(values, str):
                values = [values]
            if any(query in value for value in values):
                score += weight
        if score > 0:
            scored.append((score, clause))
    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [clause for _, clause in scored[:MAX_RESULTS]]


def query_clause(query: str) -> dict:
    """查询 CNAS-CL01:2018 条款：条款号或关键词均可。

    Args:
        query: 条款号（如 "7.4"、"6.4"）、章节号（如 "7"）或关键词（如 "样品"、"期间核查"）。

    Returns:
        dict: matched_by（clause_id/chapter/keyword）、results（条款号/标题/意图/落地要点）、
              disclaimer（红线声明）。无命中时附 all_clause_ids 供选择。
    """
    query = (query or "").strip()
    clauses = load_clauses()["clauses"]

    results: list[dict] = []
    matched_by = "keyword"

    if query:
        id_match = _CLAUSE_ID_RE.match(query) or _CHAPTER_RE.match(query)
        if id_match:
            number = id_match.group(1)
            exact = next((c for c in clauses if c["id"] == number), None)
            if exact:
                results = [exact]
                matched_by = "clause_id"
            elif "." not in number:  # 纯整数视为章节号；带点号但未收录的条款号不按章节处理，避免 int() 崩溃
                chapter_clauses = [c for c in clauses if c["chapter"] == int(number)]
                if chapter_clauses:
                    results = chapter_clauses
                    matched_by = "chapter"
        if not results:
            results = _search_by_keyword(query, clauses)

    output = {
        "tool": "query_clause",
        "query": query,
        "matched_by": matched_by if results else "none",
        "results": [_clause_brief(c) for c in results],
        "disclaimer": OUTPUT_DISCLAIMER,
    }
    if not results:
        output["all_clause_ids"] = [c["id"] for c in clauses]
        output["hint"] = "未命中。可输入条款号（如 7.4）、章节号（如 7）或改用其他关键词。"
    return output
