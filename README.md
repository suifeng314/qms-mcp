# qms-mcp · 质量体系知识库 MCP

检测实验室（CNAS/CMA 体系）垂直 MCP 服务器：**体系文件知识 + CNAS-CL01:2018 条款受控查询 + 记录表格栏目推导 + 内审检查要点**。不做通用工具，只做质量体系的垂直合规位，供 Claude Code / Claude Desktop 直接挂载。

## 红线声明（重要）

1. **不收录标准原文**：本知识库全部内容为自写摘要与经验性落地要点，**不包含 CNAS-CL01:2018（ISO/IEC 17025:2017）标准原文**；条款号与条款标题属框架性引用。
2. **不构成评审依据**：所有返回内容供学习与工作参考，符合性判定与认可评审请以 CNAS 正式发布文本及认可机构要求为准。
3. **不承诺结果**：本工具不承诺"包过评审"或任何认可/考核结果。
4. **建议保存期限为通用参考**（如 6 年），以当地法规、监管机构与客户合同要求为准。

## 五个工具

| 工具 | 输入 | 返回 |
|---|---|---|
| `query_clause` | 条款号（`7.4`/`7.8.6`）、章节号（`7`）或关键词（`期间核查`） | 条款号/标题/意图一句话/体系文件落地要点（2-4 条）；支持关键词加权检索 |
| `qms_doc_guide` | 文件类型（`质量手册`/`程序文件`/`作业指导书`/`记录表格`，支持简称） | 定位一句话、该写什么、写到什么深度、常见返工点 |
| `derive_record_fields` | 条款号（`7.4`） | 记录表格应含栏目清单 + 每栏一句话理由 + 建议保存期限（注明以当地监管为准） |
| `audit_checklist` | 审核领域（`设备管理`/`样品管理`/`结果报告` 等 13 个，支持简称） | 该领域内审检查要点清单（每领域 5-10 条） |
| `rbt214_compare` | RB/T 214 章节号（`4.5`）、CNAS 条款号（`7.8`）或关键词（`换版`） | **废止状态警示（恒返回）** + 条款映射 + 差异要点 + 换版做法 |

知识库覆盖 CNAS-CL01:2018 第 4-8 章 29 个主要条款 + 17 个关键子条款（6.2 人员族、7.2 方法族、7.7 质控、7.8 报告族八条、8.9 管理评审三条），以及 RB/T 214-2017（已废止）换版映射 17 条。

## 安装

要求 Python 3.10+，官方 MCP SDK：

```bash
pip install mcp
```

无需其他依赖，无需构建步骤。

## 挂载

### Claude Code

```bash
claude mcp add qms-mcp -- python /path/to/qms-mcp/server.py
```

（`/path/to/qms-mcp` 替换为你的本地克隆路径；Windows 路径建议用正斜杠；也可用 `--scope user` 装为用户级。）

### Claude Desktop

编辑 `claude_desktop_config.json`（路径同样替换为你的本地克隆路径）：

```json
{
  "mcpServers": {
    "qms-mcp": {
      "command": "python",
      "args": ["/path/to/qms-mcp/server.py"]
    }
  }
}
```

### 手动验证

```bash
python server.py                 # stdio 模式启动（挂 CTL-C 退出）
pytest tests/test_smoke.py -v    # 冒烟测试（不依赖 MCP 会话）
python tests/client_check.py     # 可选：标准 MCP client 协议层验证
mcp dev server.py                # 可选：MCP Inspector 调试界面
```

## 目录结构

```
qms-mcp/
├── server.py              # MCP 入口（FastMCP，stdio）
├── data/
│   ├── clauses.json       # CNAS-CL01:2018 条款知识库（自写摘要，含 x.y.z 子条款）
│   ├── qms_knowledge.json # 四层文件指引 + 内审领域检查要点（自写）
│   └── rbt214_map.json    # RB/T 214-2017（已废止）↔ CL01 换版映射（自写）
├── tools/
│   ├── _loader.py         # 知识库加载（UTF-8 + 缓存）
│   ├── query_clause.py
│   ├── qms_doc_guide.py
│   ├── derive_record_fields.py
│   ├── audit_checklist.py
│   └── rbt214_compare.py
├── tests/
│   ├── test_smoke.py      # 冒烟测试
│   └── client_check.py    # 可选协议层验证
├── .github/workflows/ci.yml  # push 即跑冒烟测试
├── .gitignore
├── LICENSE
└── README.md
```

## 自定义知识库

直接编辑 `data/*.json` 即可，无需改代码（注意：编辑后需重启 MCP 服务器/会话才生效——知识库按文件名缓存于进程内）：

- `clauses.json` 每条含 `id / chapter / title / intent / points(2-4条) / keywords / record_fields / retention`（子条款紧随父条款存放）
- `qms_knowledge.json` 含 `doc_guides`（四层文件指引）与 `audit_areas`（内审领域，每领域 5-10 条）
- `rbt214_map.json` 含 `status`（废止状态，勿删）与 `mappings`（rbt_id / rbt_theme / cnas_refs / relationship / diff_points / keywords）
- 扩展字段全部为自写摘要。请继续遵守红线：不收录标准原文。

## 关于 RB/T 214-2017 的重要状态

**RB/T 214-2017 已被国家认监委 2024 年第 22 号公告废止（2024-11-27 起生效）**，资质认定（CMA）体系转向以 GB/T 27025-2019（等同 ISO/IEC 17025:2017）为基础框架。`rbt214_compare` 工具因此定位为**旧体系文件换版迁移对照**，每次返回都带废止状态警示，不可作为现行评审依据。换版依据请以认监委/市场监管总局现行有效文件为准。

## 已知局限（v0.3 候选）

- ~~条款粒度到 x.y 级~~ ✅ v0.2 已补关键子条款 17 条（6.2/7.2/7.7/7.8/8.9 族；v0.2.1 复核修正 8.9 族编号错位并补 8.9.1 总则）；其余子条款按需增补
- ~~未覆盖 RB/T 214 差异对照~~ ✅ v0.2 已建换版映射（17 条，带废止警示）；RB/T 214 的 4.5 内部子条款编号未逐条核验，按主题级映射，仅 4.5.20（结果报告）编号经外部核验
- 关键词检索为简单加权匹配，无同义词/拼音/语义扩展
- 记录保存期限只有通用建议，未按行业/地区细分（危化、医疗、司法等有专门规定）
- 中文纯人工维护，条款号对应关系需随标准改版手动更新

## License

代码 MIT。知识库内容（`data/*.json`）为原创摘要，使用时请保留红线声明。
