"""MCP 协议层快速验证（可选）：用官方 client 走一次 stdio 会话。

运行: python tests/client_check.py
验证 server.py 可被标准 MCP 客户端挂载、工具列表完整、一次真实调用返回结构化结果。
"""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402


async def main() -> int:
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(PROJECT_ROOT / "server.py")],
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            expected = {
                "query_clause", "qms_doc_guide", "derive_record_fields",
                "audit_checklist", "rbt214_compare",
            }
            assert expected <= names, f"工具注册缺失: {expected - names}"
            print(f"[OK] tools registered: {sorted(names)}")

            result = await session.call_tool("query_clause", {"query": "7.4"})
            text = result.content[0].text
            assert "样品处置" in text and "不收录标准原文" in text
            print(f"[OK] call_tool(query_clause, 7.4) -> {text[:80]}...")

            result = await session.call_tool("audit_checklist", {"area": "报告签发"})
            assert "结果报告" in result.content[0].text
            print("[OK] call_tool(audit_checklist, 报告签发) alias resolved")

            result = await session.call_tool("rbt214_compare", {"query": "4.5.20"})
            text = result.content[0].text
            assert "结果报告" in text and '"abolished": true' in text
            print("[OK] call_tool(rbt214_compare, 4.5.20) abolished-status present")
    print("client check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
