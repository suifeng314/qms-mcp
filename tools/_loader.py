"""知识库 JSON 数据加载（tools 共用，按 mtime 热更新缓存）。"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CLAUSES_FILE = "clauses.json"
QMS_KNOWLEDGE_FILE = "qms_knowledge.json"
RBT214_MAP_FILE = "rbt214_map.json"

OUTPUT_DISCLAIMER = "本结果为自写摘要/经验性指引，不收录标准原文；评审与符合性判定请以 CNAS-CL01:2018 正式发布文本为准。"

# 文件名 -> (指纹, 数据)；指纹 = (mtime_ns, size)，与上次不同即重载
_cache: dict[str, tuple[tuple[int, int], dict]] = {}


def _fingerprint(path: Path) -> tuple[int, int]:
    """文件变化指纹：mtime 纳秒 + 字节数（防 mtime 粒度粗时漏检）。"""
    stat = path.stat()
    return (stat.st_mtime_ns, stat.st_size)


def load_json(filename: str) -> dict:
    """按 UTF-8 读取 data 目录下的知识库文件。

    带热更新缓存：每次调用检查文件 mtime，变化则重新加载，未变则直接复用缓存——
    编辑 data/*.json 后无需重启服务器，下次查询即生效。
    """
    path = DATA_DIR / filename
    fingerprint = _fingerprint(path)
    cached = _cache.get(filename)
    if cached is not None and cached[0] == fingerprint:
        return cached[1]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    _cache[filename] = (fingerprint, data)
    return data


def clear_knowledge_cache() -> None:
    """清空知识库缓存（下次查询强制重读文件）。"""
    _cache.clear()


def load_clauses() -> dict:
    """返回 CNAS-CL01:2018 条款知识库。"""
    return load_json(CLAUSES_FILE)


def load_qms_knowledge() -> dict:
    """返回体系文件指引与内审检查要点知识库。"""
    return load_json(QMS_KNOWLEDGE_FILE)


def load_rbt214_map() -> dict:
    """返回 RB/T 214-2017（已废止）↔ CNAS-CL01 换版对照知识库。"""
    return load_json(RBT214_MAP_FILE)
