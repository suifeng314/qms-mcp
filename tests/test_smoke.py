"""qms-mcp 冒烟测试：直接 import 工具函数，断言返回结构与知识库完整性。

运行: pytest tests/test_smoke.py -v
不启动真实 stdio 会话；MCP 协议层验证见 tests/client_check.py。
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools import audit_checklist, derive_record_fields, qms_doc_guide, query_clause, rbt214_compare  # noqa: E402
from tools._loader import load_clauses, load_qms_knowledge, load_rbt214_map  # noqa: E402

NO_GARBLED = "�"  # 乱码替代符，出现即说明编码链路断裂


def assert_clean_chinese(value):
    """递归断言字符串无乱码替代符且含中文内容不报错。"""
    if isinstance(value, str):
        assert NO_GARBLED not in value, f"发现乱码替代符: {value!r}"
    elif isinstance(value, dict):
        for v in value.values():
            assert_clean_chinese(v)
    elif isinstance(value, list):
        for v in value:
            assert_clean_chinese(v)


# ---------- 知识库文件完整性 ----------

def test_clauses_knowledge_base_valid():
    kb = load_clauses()
    assert kb["standard"].startswith("CNAS-CL01:2018")
    clauses = kb["clauses"]
    assert len(clauses) >= 25, "条款覆盖应不少于 25 条（8 章主要条款）"

    ids = [c["id"] for c in clauses]
    assert len(ids) == len(set(ids)), "条款号不得重复"

    chapters = {c["chapter"] for c in clauses}
    assert chapters == {4, 5, 6, 7, 8}, "须覆盖第 4-8 章（通用/结构/资源/过程/管理体系）"

    for c in clauses:
        assert c["title"] and c["intent"], f"{c['id']} 缺标题或意图"
        assert 2 <= len(c["points"]) <= 4, f"{c['id']} 落地要点应为 2-4 条"
        assert c["keywords"], f"{c['id']} 缺关键词"
        assert len(c["record_fields"]) >= 4, f"{c['id']} 记录栏目应不少于 4 个"
        assert "当地监管" in c["retention"], f"{c['id']} 保存期限须注明以当地监管为准"
        assert_clean_chinese(c)


def test_qms_knowledge_valid():
    kb = load_qms_knowledge()
    guides = kb["doc_guides"]
    assert {g["type"] for g in guides} == {"质量手册", "程序文件", "作业指导书", "记录表格"}
    for g in guides:
        assert g["positioning"] and g["aliases"]
        assert len(g["should_write"]) >= 4 and len(g["rework_points"]) >= 4
        assert_clean_chinese(g)

    areas = kb["audit_areas"]
    assert len(areas) >= 10, "内审领域应不少于 10 个"
    for a in areas:
        assert 5 <= len(a["items"]) <= 10, f"{a['area']} 检查要点应为 5-10 条"
        assert_clean_chinese(a)


# ---------- 工具 1: query_clause ----------

def test_query_clause_by_id():
    out = query_clause("7.4")
    assert out["matched_by"] == "clause_id"
    assert out["results"][0]["clause_id"] == "7.4"
    assert out["results"][0]["title"] == "样品处置"
    assert out["results"][0]["implementation_points"]
    assert "不收录标准原文" in out["disclaimer"]
    assert_clean_chinese(out)


def test_query_clause_by_chapter():
    out = query_clause("7")
    assert out["matched_by"] == "chapter"
    assert len(out["results"]) >= 8  # 第 7 章过程要求应覆盖 7.1-7.11 中的主要条款


def test_query_clause_by_keyword():
    out = query_clause("期间核查")
    assert out["matched_by"] == "keyword"
    assert out["results"], "关键词\"期间核查\"应命中（至少 6.4 设备）"
    assert any(r["clause_id"] == "6.4" for r in out["results"])
    assert len(out["results"]) <= 5


def test_query_clause_no_match():
    out = query_clause("绝对不存在的术语xyzzy")
    assert out["matched_by"] == "none"
    assert out["all_clause_ids"], "无命中时须给出全部可选条款号"


# ---------- 工具 2: qms_doc_guide ----------

def test_doc_guide_full_name_and_alias():
    full = qms_doc_guide("程序文件")
    alias = qms_doc_guide("程序")
    assert full["matched"] and alias["matched"]
    assert full["doc_type"] == alias["doc_type"] == "程序文件"
    assert full["positioning"] and full["depth"] and full["rework_points"]
    assert_clean_chinese(full)


def test_doc_guide_unknown():
    out = qms_doc_guide("不存在的类型")
    assert out["matched"] is False
    assert len(out["doc_types_available"]) == 4


# ---------- 工具 3: derive_record_fields ----------

def test_derive_record_fields():
    out = derive_record_fields("7.4")
    assert out["matched"] and out["title"] == "样品处置"
    fields = out["fields"]
    assert len(fields) >= 4
    assert all(f["name"] and f["reason"] for f in fields), "每栏须附一句话理由"
    assert "当地监管" in out["retention"]
    assert_clean_chinese(out)


def test_derive_record_fields_unknown_clause():
    out = derive_record_fields("9.9")
    assert out["matched"] is False
    assert out["all_clause_ids"]


# ---------- 工具 4: audit_checklist ----------

def test_audit_checklist_by_alias():
    out = audit_checklist("设备")
    assert out["matched"] and out["area"] == "设备管理"
    assert 5 <= len(out["items"]) <= 10
    assert_clean_chinese(out)


def test_audit_checklist_unknown():
    out = audit_checklist("不存在领域")
    assert out["matched"] is False
    assert len(out["areas_available"]) >= 10


# ---------- 知识库扩展：x.y.z 子条款 ----------

def test_subclauses_present():
    kb = load_clauses()
    ids = {c["id"] for c in kb["clauses"]}
    expected = {
        "6.2.2", "6.2.5", "6.2.6",           # 人员族
        "7.2.1", "7.2.2",                     # 方法族
        "7.7.1",                              # 质控
        "7.8.1", "7.8.2", "7.8.3", "7.8.4", "7.8.5", "7.8.6", "7.8.7", "7.8.8",  # 报告族
        "8.9.1", "8.9.2", "8.9.3",            # 管理评审（总则/输入/输出）
    }
    assert expected <= ids, f"缺失子条款: {expected - ids}"
    # 父条款精确匹配不被子条款干扰
    out = query_clause("7.8")
    assert out["matched_by"] == "clause_id"
    assert out["results"][0]["clause_id"] == "7.8"
    # 子条款可精确查询
    out = query_clause("7.8.6")
    assert out["matched_by"] == "clause_id"
    assert "符合性" in out["results"][0]["title"]


def test_query_clause_numeric_unknown_no_crash():
    """带点号但未收录的条款号不得崩溃（曾因 int() 抛 ValueError）。"""
    for q in ("8.1", "9.9", "7.4.1", "4.3"):  # 8.1/4.3 为真实条款但库未收录
        out = query_clause(q)
        assert out["matched_by"] == "none", f"{q} 应走未命中分支"
        assert out["all_clause_ids"], f"{q} 未命中时应给出可选条款号"


def test_empty_query_no_fake_keyword_hit():
    """空输入不得命中全部条目（"" in value 恒真陷阱）。"""
    assert query_clause("")["matched_by"] == "none"
    assert rbt214_compare("")["matched_by"] == "none"


def test_query_clause_chapter_variants():
    out = query_clause("第7章")
    assert out["matched_by"] == "chapter"
    assert len(out["results"]) >= 8


# ---------- 知识库扩展：RB/T 214 换版对照 ----------

def test_rbt214_map_valid():
    kb = load_rbt214_map()
    status = kb["status"]
    assert status["abolished"] is True, "RB/T 214-2017 已废止，状态块必须如实标注"
    assert status["abolished_effective"] == "2024-11-27"
    assert "GB/T 27025" in status["successor"]

    mappings = kb["mappings"]
    assert len(mappings) >= 15, "换版映射应不少于 15 条"
    for m in mappings:
        assert m["rbt_theme"] and m["relationship"], "缺主题或对应关系"
        assert 2 <= len(m["diff_points"]) <= 4, f"{m['rbt_theme']} 差异要点应为 2-4 条"
        assert m["keywords"], f"{m['rbt_theme']} 缺关键词"
        assert_clean_chinese(m)


# ---------- 工具 5: rbt214_compare ----------

def test_rbt214_compare_by_rbt_id():
    out = rbt214_compare("4.5")
    assert out["matched_by"] == "rbt_id"
    assert out["results"], "4.5 有多条主题级映射"
    assert out["standard_status"]["abolished"] is True, "结果须恒带废止警示"


def test_rbt214_compare_by_cnas_ref():
    out = rbt214_compare("7.8")
    assert out["matched_by"] == "cnas_ref"
    assert any("结果报告" in r["rbt_theme"] for r in out["results"])


def test_rbt214_compare_by_keyword():
    out = rbt214_compare("换版")
    assert out["matched_by"] == "keyword"
    assert out["results"], "关键词\"换版\"应命中"
    assert len(out["results"]) <= 5


def test_rbt214_compare_no_match():
    out = rbt214_compare("绝对不存在的术语xyzzy")
    assert out["matched_by"] == "none"
    assert out["rbt_ids_available"]
    assert out["standard_status"]["abolished"] is True


# ---------- 数据文件可被标准 JSON 解析（UTF-8 无 BOM） ----------

def test_json_files_strict_utf8():
    for name in ("clauses.json", "qms_knowledge.json", "rbt214_map.json"):
        raw = (PROJECT_ROOT / "data" / name).read_bytes()
        text = raw.decode("utf-8")  # 带 BOM 会抛异常
        data = json.loads(text)
        assert isinstance(data, dict)
