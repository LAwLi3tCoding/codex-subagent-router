[English](README.md) | [简体中文](README.zh-CN.md)

# Codex Subagent Router

一套全局委派策略，提供四个 Sol 工作角色和一个独立的 Astra 审查角色。主会话负责需求与整体设计，保留用户手选的模型与推理强度；短任务、紧密关联的工作和未分类任务由主会话直接处理。

## 何时委派

子任务的目标、范围、依赖和验收标准明确，并且并行执行、上下文隔离或独立判断能带来具体收益时，才进行委派。其他任务直接执行。专题设计可以在完整方案形成前委派，只要问题边界明确；`sol-high` 可以负责探索尚未解决的设计问题。

| 角色 | 模型 | 推理强度 | 常见任务 |
| --- | --- | --- | --- |
| `sol-low` | `gpt-6.1-sol` | `low` | 决策少、范围明确且检查标准清楚的工作。 |
| `sol-medium` | `gpt-6.1-sol` | `medium` | 需要局部判断的常规实现与调查。 |
| `sol-high` | `gpt-6.1-sol` | `high` | 复杂排查、综合分析，或边界明确的开放设计专题。 |
| `sol-xhigh` | `gpt-6.1-sol` | `xhigh` | 约束相互影响、需要较多推理的复杂任务。 |
| `astra-reviewer` | `gpt-6-astra` | `xhigh` | 对重要决策与变更进行独立只读审查。 |

按任务的推理需求选择强度。四个 Sol 角色不覆盖 sandbox 或权限设置；每次委派应明确只读要求，或限定可写范围及负责人。并行写入必须拥有互斥的文件范围或隔离工作树。委派不能扩大用户授权范围。

安装器不设置全局子 Agent 模型与强度默认值，不安装自定义 `default`、`explorer`、`owner`、`mechanical` 或 `high-risk-owner`，并清理旧 Luna、Terra 角色。`max` 仅用于显式例外，不作为常驻角色。

## 独立审查与完成判断

核心共享设计、安全、一致性或恢复机制的实质变更、重大业务判断，以及用户明确要求的审查，必须交给独立的 `astra-reviewer` 子 Agent，以 `xhigh` 强度审查。推理强度、Ultra 或领域关键词本身不触发审查。证据不足属于审查缺口，不能成为免审理由。

主 Agent 根据证据裁决发现并修改。实质修正后，由同一审查者复查新版本；没有发现或仅修正措辞时，无需反复审查。子 Agent 应交付证据、验证结果和覆盖缺口。子任务运行结束不能证明业务已完成；主 Agent 负责集成、验证和最终完成声明。

只使用当前启动工具实际支持的字段。若工具禁止在完整历史分叉时覆盖模型或推理强度，显式覆盖时应使用 `fork_turns="none"` 或有限轮次。角色配置可能覆盖启动参数；有运行记录时，以记录确认实际模型与强度。

## 安装

需要 Python 3.11 或更新版本。

```bash
./install.sh
```

安装到其他 Codex 目录：

```bash
./install.sh --codex-home /path/to/.codex
```

安装器写入五个角色文件与全局 `AGENTS.md` 中的受管策略块，启用 subagents，并移除全局 `default_subagent_model` 和 `default_subagent_reasoning_effort` 设置。主会话模型与强度、权限、MCP 配置、用户并发限制、无关指引以及已有 hooks 和 features 设置均保留。替换或清理文件前，先备份到 `subagent-router-backups/`。受管输入不合法、受管文件存在不安全符号链接，或使用内联 `agents` 表时，在写入配置目录前拒绝安装；请使用 `[agents]` 表或点分键。安装写入失败时，逐一尝试恢复已改文件并保留备份；恢复不完整时，报告备份位置。

策略全局生效，仍需遵守工作区指引及角色覆盖设置。安装器不安装或启用 hook。重启 Codex 以重新加载配置。安装器不会修改 shell 启动文件或安装依赖。

## 验证

```bash
python3 scripts/verify.py --codex-home ~/.codex
```

运行仓库测试：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

## 仓库结构

```text
agents/                 四个 Sol 角色与只读 Astra 审查者
policy/                 委派、审查与职责策略
scripts/install.py      支持输入校验和备份的安装器
scripts/verify.py       安装状态与源文件隐私检查
tests/                  安装器与契约测试
```

## 发布安全

提交和 GitHub 元数据中不得包含个人信息、公司内部信息、凭据、主机信息或本地绝对路径。
