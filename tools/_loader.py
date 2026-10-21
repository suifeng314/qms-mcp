"""知识库 JSON 数据加载（tools 共用）。"""

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CLAUSES_FILE = "clauses.json"
QMS_KNOWLEDGE_FILE = "qms_knowledge.json"
RBT214_MAP_FILE = "rbt214_map.json"

OUTPUT_DISCLAIMER = "本结果为自写摘要/经验性指引，不收录标准原文；评审与符合性判定请以 CNAS-CL01:2018 正式发布文本为准。"


@lru_cache(maxsize=None)
def load_json(filename: str) -> dict:
    """按 UTF-8 读取 data 目录下的知识库文件（结果缓存）。"""
    path = DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_clauses() -> dict:
    """返回 CNAS-CL01:2018 条款知识库。"""
    return load_json(CLAUSES_FILE)


def load_qms_knowledge() -> dict:
    """返回体系文件指引与内审检查要点知识库。"""
    return load_json(QMS_KNOWLEDGE_FILE)


def load_rbt214_map() -> dict:
    """返回 RB/T 214-2017（已废止）↔ CNAS-CL01 换版对照知识库。"""
    return load_json(RBT214_MAP_FILE)
