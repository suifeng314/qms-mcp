"""audit_checklist —— 内审检查要点生成（按领域）。"""

from tools._loader import OUTPUT_DISCLAIMER, load_qms_knowledge


def _normalize(area: str) -> str:
    return (area or "").strip().lower()


def audit_checklist(area: str) -> dict:
    """生成指定领域的内审检查要点清单。

    Args:
        area: 审核领域，如 "设备管理"、"样品管理"、"结果报告"、"记录与数据控制"。

    Returns:
        dict: area（领域名）、items（检查要点清单）、disclaimer（红线声明）。
              未识别领域时返回全部可选领域。
    """
    area = _normalize(area)
    areas = load_qms_knowledge()["audit_areas"]

    entry = next((a for a in areas if _normalize(a["area"]) == area), None)
    if entry is None:  # 简称/别名匹配
        entry = next(
            (a for a in areas if area in [_normalize(x) for x in a["aliases"]]), None
        )

    available = [a["area"] for a in areas]
    output = {
        "tool": "audit_checklist",
        "areas_available": available,
        "matched": entry is not None,
        "disclaimer": OUTPUT_DISCLAIMER,
    }
    if entry:
        output.update({"area": entry["area"], "items": entry["items"]})
    else:
        output["hint"] = "未识别的审核领域，请从 areas_available 中选择。"
    return output
