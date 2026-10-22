"""知识库热更新（mtime 缓存）测试。

运行: pytest tests/test_hot_reload.py -v
全部在 tmp_path 中操作真实知识库的副本，monkeypatch 自动还原 DATA_DIR，
测试后清空缓存恢复现场，不触碰 data/ 下任何真实文件。
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools import _loader as loader  # noqa: E402
from tools._loader import (  # noqa: E402
    CLAUSES_FILE,
    QMS_KNOWLEDGE_FILE,
    clear_knowledge_cache,
    load_json,
)
from tools.query_clause import query_clause  # noqa: E402


def _bump_mtime(path: Path) -> None:
    """显式前移 mtime 1 秒，避免文件系统 mtime 粒度粗导致指纹未变。"""
    ns = path.stat().st_mtime_ns + 1_000_000_000
    os.utime(path, ns=(ns, ns))


def _copy_kb_to_tmp(tmp_path: Path, filename: str) -> Path:
    """把真实知识库文件复制到 tmp 目录，返回副本路径。"""
    dst = tmp_path / filename
    dst.write_text(
        (PROJECT_ROOT / "data" / filename).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return dst


def _use_tmp_data_dir(monkeypatch, tmp_path: Path) -> None:
    """把 loader 指向 tmp 目录并清空缓存（隔离真实数据）。"""
    monkeypatch.setattr(loader, "DATA_DIR", tmp_path)
    clear_knowledge_cache()


# ---------- 场景①: 文件变化后重载 ----------

def test_load_json_reloads_on_mtime_change(tmp_path, monkeypatch):
    _copy_kb_to_tmp(tmp_path, CLAUSES_FILE)
    _use_tmp_data_dir(monkeypatch, tmp_path)
    try:
        first = load_json(CLAUSES_FILE)
        assert first["standard"].startswith("CNAS-CL01:2018")

        raw = json.loads((tmp_path / CLAUSES_FILE).read_text(encoding="utf-8"))
        raw["clauses"][0]["title"] = "热更新测试标题XYZ"
        (tmp_path / CLAUSES_FILE).write_text(
            json.dumps(raw, ensure_ascii=False), encoding="utf-8"
        )
        _bump_mtime(tmp_path / CLAUSES_FILE)

        second = load_json(CLAUSES_FILE)
        assert second is not first, "文件变化后必须重载，不得返回旧缓存对象"
        assert second["clauses"][0]["title"] == "热更新测试标题XYZ"
    finally:
        clear_knowledge_cache()


def test_query_clause_reflects_modified_knowledge(tmp_path, monkeypatch):
    """端到端：改知识库文件后，工具查询结果反映新内容。"""
    _copy_kb_to_tmp(tmp_path, CLAUSES_FILE)
    _use_tmp_data_dir(monkeypatch, tmp_path)
    try:
        raw = json.loads((tmp_path / CLAUSES_FILE).read_text(encoding="utf-8"))
        target = next(c for c in raw["clauses"] if c["id"] == "7.4")
        target["title"] = "样品处置（热更新版）"
        (tmp_path / CLAUSES_FILE).write_text(
            json.dumps(raw, ensure_ascii=False), encoding="utf-8"
        )
        _bump_mtime(tmp_path / CLAUSES_FILE)

        out = query_clause("7.4")
        assert out["matched_by"] == "clause_id"
        assert out["results"][0]["title"] == "样品处置（热更新版）"
    finally:
        clear_knowledge_cache()


def test_reload_when_only_mtime_changes(tmp_path, monkeypatch):
    """内容相同但 mtime 变化也触发重载——证明每次查询都在检查指纹，而非只在首查。"""
    dst = _copy_kb_to_tmp(tmp_path, QMS_KNOWLEDGE_FILE)
    _use_tmp_data_dir(monkeypatch, tmp_path)
    try:
        first = load_json(QMS_KNOWLEDGE_FILE)
        _bump_mtime(dst)
        second = load_json(QMS_KNOWLEDGE_FILE)
        assert second is not first, "仅 mtime 变化也应重载"
        assert second == first, "内容未变时重载结果应等值"
    finally:
        clear_knowledge_cache()


# ---------- 场景②: 文件未变时不重载 ----------

def test_no_reload_when_file_unchanged(tmp_path, monkeypatch):
    _copy_kb_to_tmp(tmp_path, QMS_KNOWLEDGE_FILE)
    _use_tmp_data_dir(monkeypatch, tmp_path)

    calls = {"json_load": 0}
    real_json_load = json.load

    def counting_load(fp, *args, **kwargs):
        calls["json_load"] += 1
        return real_json_load(fp, *args, **kwargs)

    monkeypatch.setattr(loader.json, "load", counting_load)
    try:
        first = load_json(QMS_KNOWLEDGE_FILE)
        assert calls["json_load"] == 1, "首次调用应真实读文件一次"

        for _ in range(3):
            assert load_json(QMS_KNOWLEDGE_FILE) is first, "未变化时应复用同一缓存对象"
        assert calls["json_load"] == 1, "文件未变时不得触发重载"
    finally:
        clear_knowledge_cache()
