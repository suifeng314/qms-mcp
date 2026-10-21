"""qms_doc_guide —— 体系文件四层写法指引（质量手册/程序文件/作业指导书/记录表格）。"""

from tools._loader import OUTPUT_DISCLAIMER, load_qms_knowledge


def _normalize(doc_type: str) -> str:
    return (doc_type or "").strip().lower()


def qms_doc_guide(doc_type: str) -> dict:
    """查询体系文件四层（手册/程序/作业指导书/记录表格）的写法指引。

    Args:
        doc_type: 文件类型，如 "质量手册"、"程序文件"、"作业指导书"、"记录表格"
                  （支持简称，如 "手册"、"程序"、"SOP"、"表单"）。

    Returns:
        dict: positioning（定位一句话）、should_write（该写什么）、depth（写到什么深度）、
              rework_points（常见返工点）、disclaimer（红线声明）。
    """
    doc_type = _normalize(doc_type)
    guides = load_qms_knowledge()["doc_guides"]

    guide = next((g for g in guides if _normalize(g["type"]) == doc_type), None)
    if guide is None:  # 简称/别名匹配
        guide = next(
            (g for g in guides if doc_type in [_normalize(a) for a in g["aliases"]]),
            None,
        )

    available = [g["type"] for g in guides]
    output = {
        "tool": "qms_doc_guide",
        "matched": guide is not None,
        "doc_types_available": available,
        "disclaimer": OUTPUT_DISCLAIMER,
    }
    if guide:
        output.update(
            {
                "doc_type": guide["type"],
                "positioning": guide["positioning"],
                "should_write": guide["should_write"],
                "depth": guide["depth"],
                "rework_points": guide["rework_points"],
            }
        )
    else:
        output["hint"] = "未识别的文件类型，请从 doc_types_available 中选择。"
    return output
