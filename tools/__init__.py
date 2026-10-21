"""qms-mcp 工具集：检测实验室（CNAS/CMA）质量体系垂直工具。

每个模块一个工具函数（纯函数、返回 dict），由 server.py 统一注册到 FastMCP。
"""

from tools.audit_checklist import audit_checklist
from tools.derive_record_fields import derive_record_fields
from tools.qms_doc_guide import qms_doc_guide
from tools.query_clause import query_clause
from tools.rbt214_compare import rbt214_compare

__all__ = ["query_clause", "qms_doc_guide", "derive_record_fields", "audit_checklist", "rbt214_compare"]
