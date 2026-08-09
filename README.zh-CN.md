# Codex 子 Agent 路由器

[English](README.md) | [简体中文](README.zh-CN.md)

这是一套无第三方依赖、用户级生效的 Codex 子 Agent 路由策略。普通的
`default` Agent 始终继承当前会话手动选择的模型和推理强度；只有任务确实
需要指定能力层级时，才会路由到 Luna、Terra 或 Sol 专用角色。

## 路由模型

- `default`：继承当前会话的模型和推理强度。
- `luna-batch`：使用 Medium 推理处理规则清晰的高吞吐工作。
- `luna-reasoner`：使用 Luna Max，但只处理输入完整、边界严格且结果可由
  独立机制校验的推理任务。
- `terra-explorer` 和 `terra-researcher`：处理大范围、以读取为主的探索和
  资料收集工作。
- `sol-high`、`sol-xhigh` 和 `sol-max`：依次处理复杂度不断提高的任务。
- `sol-ultra`：以 Sol Max 作为编排 leader，处理能够拆成多个独立工作流的
  极高难度规划或设计任务。这里不会把 `ultra` 写成模型推理强度。

Luna 和 Terra 可以收集、转换或整理证据，但不能独立负责架构、安全、发布、
迁移或其他高风险决策。此类最终结论必须由 Sol 专用角色综合判断。

这套映射遵循 OpenAI 的 GPT-5.6 官方说明：Luna 面向成本敏感、高吞吐工作；
Terra 平衡能力与成本；Sol 是旗舰能力层级；`max` 是文档公开支持的最高推理
强度。参见 [OpenAI 官方模型指南](https://developers.openai.com/api/docs/guides/latest-model)。

全局策略只在有实际收益时才委派任务，并要求单向升级和单写入者边界。子
Agent 数量、并行或分批方式、最终集成和验证均由父 Agent 根据当前任务和
运行时实际容量动态决定，不设置共享的固定并发数量。

## 启动信息可见

每次子 Agent 启动时，Codex App 或 CLI 事件流都会显示一条消息：

```text
Subagent started | role: sol-xhigh | model: gpt-5.6-sol | reasoning: xhigh
```

模型值直接取自运行时的 `SubagentStart` 事件，因此反映该子 Agent 实际选择
的模型。具名路由角色的推理强度取自已安装的 TOML 配置。由于该运行时事件
目前不提供推理强度字段，`default` 会如实显示 `inherited from parent`；没有
配置强度的内置或未知角色会显示
`runtime-selected (not exposed by SubagentStart)`，不会猜测具体值。

路由器还会给每个子 Agent 的任务名增加前缀，让模型层级和推理强度直接显示
在 Codex App 的 **Subagents** 列表中。例如：

```text
5_6_luna_max_analyze_rules
```

当前 App 会把这个标识符显示为列表行标题。开头字段表达的可读文案是
`5.6 · luna · max`；由于 Codex 任务名只允许小写字母、数字和下划线，实际
参数必须使用下划线编码。这是文本前缀，并非 App 原生 badge。标签根据子
Agent 最终生效的模型和强度生成，不根据角色名生成。完整映射如下：

| 子 Agent 最终生效模型 | 强度 | 任务名前缀 |
| --- | --- | --- |
| `gpt-5.6-luna` | `medium` | `5_6_luna_medium` |
| `gpt-5.6-luna` | `max` | `5_6_luna_max` |
| `gpt-5.6-terra` | `medium` | `5_6_terra_medium` |
| `gpt-5.6-terra` | `high` | `5_6_terra_high` |
| `gpt-5.6-sol` | `high` | `5_6_sol_high` |
| `gpt-5.6-sol` | `xhigh` | `5_6_sol_xhigh` |
| `gpt-5.6-sol` | `max` | `5_6_sol_max` |
| 启动前无法取得模型或强度 | — | `runtime_selected` |

例如，`sol-max` 和 `sol-ultra` 当前最终都是 Sol Max，因此都使用
`5_6_sol_max`，不会把编排角色写进模型标签。`default` 只有在启动前能够明确
取得父会话最终模型和强度时才生成具体标签，否则使用 `runtime_selected`。
生命周期消息仍负责校验 Codex 实际使用的运行时模型。

## 安装

需要 Python 3.11 或更高版本，以及当前版本的 Codex。

从 GitHub 一键安装：

```bash
curl -fsSL https://raw.githubusercontent.com/LAwLi3tCoding/codex-subagent-router/main/install.sh | sh
```

也可以克隆仓库后执行：

```bash
./install.sh
```

出于安全考虑，Codex 会要求用户对新增或发生变化的命令 Hook 做一次信任
确认。安装后请启动 Codex CLI，执行 `/hooks`，信任路由器的
`SubagentStart` Hook，然后重启 App 或 CLI 会话。安装器不会绕过这项官方
安全机制。

### 安装后会发生什么

- 将 Luna、Terra 和 Sol 角色定义安装到用户的 Codex 配置目录。
- 在全局 Codex `AGENTS.md` 中写入一个受管理的路由规则区块，使每个新会话
  都能使用这套路由策略。
- 安装并启用用户级 `SubagentStart` 生命周期 Hook，在每个子 Agent 启动时
  显示角色、运行时实际模型，以及已配置或继承的推理强度。
- 启用多 Agent 能力，并由 Codex 运行时和父 Agent 动态决定并发数量与分批
  方式。
- 清理与会话继承和动态并发冲突的旧版子 Agent 模型覆盖及固定并发覆盖，使
  `default` 使用当前会话选择的模型和推理强度。
- 当旧版全局委派语句设置了固定子 Agent 数量时，将其规范化为动态决策。

### 安全与可恢复性

- 修改已有受管理目标前，创建带时间戳的本地备份。
- 只修改路由器管理的规则区块、已知 Agent 配置项、具名角色文件，以及精确
  匹配的受支持旧版固定数量委派语句；保留所有无关配置和说明。
- 安装过程是幂等的，更新仓库后可以安全地再次运行。
- 只安装 Codex 生命周期 Hook；不会修改 shell 启动文件，也不会运行常驻
  后台进程。

## 验证

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify.py
```

验证覆盖角色与模型矩阵、`default` 继承、全局受管理规则、生命周期 Hook
注册、配置解析、安装幂等性和仓库隐私检查。

## 文件结构

- `agents/`：Codex 自定义 Agent 定义。
- `hooks/`：显示子 Agent 启动信息的生命周期 Hook。
- `policy/subagent-routing.md`：全局加载的路由策略。
- `scripts/install.py`：幂等的用户级安装器。
- `scripts/verify.py`：安装状态和可公开性检查。
- `tests/`：安装器回归测试。

## 发布

仓库不应包含个人路径、账号标识、私有配置、凭证或组织内部信息。发布或推送
到代码托管平台前，请检查完整 Git 历史并运行验证命令。
