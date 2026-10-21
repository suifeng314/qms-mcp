"""derive_record_fields —— 从条款要求推导记录表格应含栏目。"""

from tools._loader import OUTPUT_DISCLAIMER, load_clauses


def derive_record_fields(clause: str) -> dict:
    """输入 CNAS-CL01:2018 条款号，推导该条款下记录表格应含的栏目。

    Args:
        clause: 条款号，如 "7.4"（样品处置）、"6.4"（设备）、"8.8"（内部审核）。

    Returns:
        dict: clause_id/title/intent、fields（栏目名 + 每栏一句话理由）、
              retention（建议保存期限，注明以当地监管为准）、disclaimer（红线声明）。
    """
    clause = (clause or "").strip()
    clauses = load_clauses()["clauses"]
    entry = next((c for c in clauses if c["id"] == clause), None)

    output = {
        "tool": "derive_record_fields",
        "clause": clause,
        "matched": entry is not None,
        "disclaimer": OUTPUT_DISCLAIMER,
    }
    if entry is None:
        output["all_clause_ids"] = [c["id"] for c in clauses]
        output["hint"] = "未找到该条款，请从 all_clause_ids 中选择条款号（如 7.4）。"
        return output

    output.update(
        {
            "title": entry["title"],
            "intent": entry["intent"],
            "record_table_name_hint": f"{entry['title']}记录表（建议命名参考）",
            "fields": [
                {"name": f["name"], "reason": f["reason"]} for f in entry["record_fields"]
            ],
            "retention": entry["retention"],
        }
    )
    return output
