"""rbt214_compare —— RB/T 214-2017（已废止）↔ CNAS-CL01:2018 换版对照查询。

支持三种输入：
- RB/T 214 章节号（如 "4.1"、"4.5"、"4.5.20"）
- CNAS-CL01 条款号（如 "7.8"、"6.4"）→ 返回映射到它的 RB/T 主题
- 关键词（如 "换版"、"设备"）

返回恒含废止状态块（RB/T 214-2017 已于 2024-11-27 废止），
防止旧体系换版用户把本对照误当现行评审依据。
"""

from tools._loader import load_rbt214_map

# 命中权重：主题 > 关键词 > 差异要点
_WEIGHTS = (("rbt_theme", 5), ("keywords", 3), ("diff_points", 1))
MAX_RESULTS = 5


def _brief(mapping: dict) -> dict:
    """映射条目的对外精简结构。"""
    return {
        "rbt_id": mapping["rbt_id"],
        "rbt_theme": mapping["rbt_theme"],
        "cnas_refs": mapping["cnas_refs"],
        "relationship": mapping["relationship"],
        "diff_points": mapping["diff_points"],
    }


def _search_by_keyword(query: str, mappings: list[dict]) -> list[dict]:
    """按关键词加权检索映射条目。"""
    scored = []
    for m in mappings:
        score = 0
        for field, weight in _WEIGHTS:
            values = m.get(field) or []
            if isinstance(values, str):
                values = [values]
            if any(query in value for value in values):
                score += weight
        if score > 0:
            scored.append((score, m))
    scored.sort(key=lambda item: (-item[0], item[1]["rbt_theme"]))
    return [m for _, m in scored[:MAX_RESULTS]]


def rbt214_compare(query: str) -> dict:
    """查询 RB/T 214（已废止）与 CNAS-CL01:2018 的换版条款对照。

    Args:
        query: RB/T 214 章节号（如 "4.5"）、CNAS-CL01 条款号（如 "7.8"）或关键词（如 "换版"）。

    Returns:
        dict: standard_status（废止警示，恒返回）、matched_by（rbt_id/cnas_ref/keyword）、
              results（RB 主题/CL01 对应条款/关系/差异要点/换版做法）、disclaimer。
              无命中时附 rbt_ids_available 供选择。
    """
    query = (query or "").strip()
    kb = load_rbt214_map()
    mappings = kb["mappings"]

    results: list[dict] = []
    matched_by = "keyword"

    if query:
        exact = [m for m in mappings if m["rbt_id"] == query]
        if exact:
            results, matched_by = exact, "rbt_id"
        else:
            by_cnas = [m for m in mappings if query in m["cnas_refs"]]
            if by_cnas:
                results, matched_by = by_cnas, "cnas_ref"
    if not results:
        results = _search_by_keyword(query, mappings)

    output = {
        "tool": "rbt214_compare",
        "query": query,
        "standard_status": kb["status"],
        "matched_by": matched_by if results else "none",
        "results": [_brief(m) for m in results],
        "disclaimer": kb["disclaimer"],
    }
    if not results:
        output["rbt_ids_available"] = sorted(
            {m["rbt_id"] for m in mappings if m["rbt_id"] != "—"}
        )
        output["hint"] = (
            "未命中。可输入 RB/T 214 章节号（如 4.5）、"
            "CNAS-CL01 条款号（如 7.8）或关键词（如 换版、设备）。"
        )
    return output
