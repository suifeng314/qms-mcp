"""qms-mcp —— 质量体系知识库 MCP 服务器（检测实验室垂直工具集，v0.2）。

定位：CNAS/CMA 体系文件知识 + CNAS-CL01:2018 条款受控查询 + 记录表格栏目推导 + 内审检查要点
+ RB/T 214（已废止）换版对照。
知识库内容全部为自写摘要（见 README 红线声明），不收录标准原文。

运行（stdio 传输，供 Claude Code / Claude Desktop 挂载）:
    python server.py
"""

from mcp.server.fastmcp import FastMCP

from tools import audit_checklist, derive_record_fields, qms_doc_guide, query_clause, rbt214_compare

mcp = FastMCP(
    "qms-mcp",
    instructions=(
        "检测实验室（CNAS/CMA 体系）质量体系知识库。五个工具：\n"
        "1. query_clause —— CNAS-CL01:2018 条款查询（条款号或关键词，含 x.y.z 子条款）；\n"
        "2. qms_doc_guide —— 体系文件四层写法指引（手册/程序/作业指导书/记录表格）；\n"
        "3. derive_record_fields —— 按条款推导记录表格应含栏目与保存期限建议；\n"
        "4. audit_checklist —— 按领域生成内审检查要点；\n"
        "5. rbt214_compare —— RB/T 214-2017（已废止）↔ CL01:2018 换版对照（恒带废止状态警示）。\n"
        "注意：所有返回为自写摘要与经验性指引，不收录标准原文，不构成评审依据。"
    ),
)

_TOOLS = (query_clause, qms_doc_guide, derive_record_fields, audit_checklist, rbt214_compare)
for _fn in _TOOLS:
    mcp.tool()(_fn)


if __name__ == "__main__":
    mcp.run(transport="stdio")
