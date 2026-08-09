# Codex 子 Agent 路由器

[English](README.md) | [简体中文](README.zh-CN.md)

这是一套无第三方依赖、用户级生效的 Codex 子 Agent 路由策略。普通的
`default` Agent 始终继承当前会话手动选择的模型和推理强度；只有任务确实
需要指定能力层级时，才会路由到 Luna、Terra 或 Sol 专用角色。

## 路由模型

路由使用两个正交维度：模型家族由工作模式和权限边界决定，effort 由剩余工作
复杂度决定。

- Luna：处理范围闭合、成本敏感且有机械校验基准的任务。
- Terra：处理只读探索、资料研究和证据综合。
- Sol：处理实现、判断、验证、架构以及高风险最终综合。
- `default`：仍继承当前会话模型和 effort，但必须由路由凭证证明存在明确的
  同能力层级需求。

Canonical 角色统一使用 `{family}-{effort}` 命名。本版本支持：

| 家族 | Canonical effort |
| --- | --- |
| Luna | `low`、`medium`、`high`、`xhigh`、`max` |
| Terra | `low`、`medium`、`high`、`xhigh`、`max`、`ultra` |
| Sol | `low`、`medium`、`high`、`xhigh`、`max`、`ultra` |

当前 Codex 运行时元数据把 `ultra` 描述为自动任务委派。它是 Sol/Terra 在异常
困难且可独立拆分任务中的编排模式，不是高于 `max` 的推理深度；Luna 没有
Ultra 路由。

Luna 和 Terra 可以收集、转换或整理证据，但不能独立负责架构、安全、发布、
迁移或其他高风险决策。此类最终结论必须由 Sol 专用角色综合判断。

这套映射遵循 OpenAI 的 GPT-5.6 官方说明：Luna 面向成本敏感、高吞吐工作；
Terra 平衡能力与成本；Sol 是旗舰能力层级；`max` 是文档公开支持的最高推理
强度。参见 [OpenAI 官方模型指南](https://developers.openai.com/api/docs/guides/latest-model)。

全局策略只在有实际收益时才委派任务，并要求单向升级和单写入者边界。子
Agent 数量、并行或分批方式、最终集成和验证均由父 Agent 根据当前任务和
运行时实际容量动态决定，不设置共享的固定并发数量。

## 路由凭证与冲突优先级

每个子 Agent 的 prompt 都必须包含紧凑路由凭证：剩余工作、委派收益、阶段、
工作模式、闭合状态、风险、复杂度信号、独立工作流数量、选中的模型与 effort、
拒绝相邻层级的原因以及失败后的 fallback。这样每次降档、继承和升级都有可检查
依据。

冲突处理采用 fail-closed 顺序：混合的证据/写入/决策/验证任务先拆成顺序阶段；
先选模型家族再选 effort；降档要求所有条件成立；任一高风险信号都能阻止便宜
路由；未知状态不能作为降档证据。`default` 最后考虑，并且必须证明同层级能力
确实必要。

## 按阶段与剩余任务重新评估

路由依据是子 Agent 当前剩余的工作，而不是原任务最困难阶段使用过的模型。
父 Agent 会在设计转实现、实现转验证、探索转决策以及每次任务拆分或交接时
重新评估路由。

设计完成并不自动意味着可以降低模型层级。只有当实现所需的关键决策、接口、
边界、验收证据和禁止选择都已经闭合时，才可以降低层级。满足这些条件后，
即使父 Agent 使用 XHigh 或 Max，边界明确的实现也可以按剩余复杂度使用
`sol-low`、`sol-medium` 或 `sol-high`；机械性修改可以使用对应 Luna effort，
而仍有跨模块不确定性或架构决策的工作继续使用 XHigh 或 Max。

新的、更窄且边界完整的任务可以选择更低层级，但同一个尚未解决任务的重试
仍然只能单向升级。如果子 Agent 执行时发现范围扩大或设计缺口重新出现，必须
把证据交回父 Agent 重新路由，不能静默扩大自己的职责。验证阶段也按完成声明
所需的风险和判断强度独立选型，最终完成声明仍由父 Agent 负责。

## 运行时兼容回退

本地 Codex 模型缓存只作为提示性证据。effort 条目缺失，或缓存损坏、过期、
不完整、尚未生成时，不会让安装器、验证器、委派或父任务失败；可观察到的异常
会被报告为 warning。路由器仍先尝试配置的角色，并以运行时对子 Agent 启动的
实际结果为准。

如果 `ultra` 子 Agent 被运行时拒绝，路由器可以在同一家族内尝试一次 `max`，
由父 Agent 接管编排。其他具名角色失败时，也只允许一次满足风险和验收条件的
同家族安全回退，不能静默跨模型家族，也不能用 `default` 掩盖不兼容。如果回退
仍失败或不存在安全候选，父 Agent 直接执行该任务，避免路由元数据阻塞用户任务。

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
gpt56_luna_max_analyze_rules
```

当前 App 会把这个标识符显示为列表行标题。开头字段表达的可读文案是
`GPT56 · luna · max`；由于 Codex 任务名只允许小写字母、数字和下划线，实际
参数必须使用下划线编码。这是文本前缀，并非 App 原生 badge。标签根据子
Agent 最终生效的模型和强度生成，不根据角色名生成。完整映射如下：

| 子 Agent 最终家族 | Effort | 任务名前缀格式 |
| --- | --- | --- |
| `gpt-5.6-luna` | `low` 到 `max` | `gpt56_luna_<effort>` |
| `gpt-5.6-terra` | `low` 到 `max`、`ultra` | `gpt56_terra_<effort>` |
| `gpt-5.6-sol` | `low` 到 `max`、`ultra` | `gpt56_sol_<effort>` |
| 启动前无法取得模型或强度 | — | `runtime_selected` |

`default` 只有在启动前能够明确取得父会话最终模型和强度时才生成具体标签，
否则使用 `runtime_selected`。
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
- 升级时先把已经退役的 pre-canonical 角色文件放入时间戳备份，再从配置目录
  删除。
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

验证覆盖角色/模型/effort 矩阵、`default` 继承、路由凭证与合成场景、全局受
管理规则、生命周期 Hook 注册、配置解析、安装幂等性和仓库隐私检查。存在
Codex 模型缓存时，不受支持的家族/effort 组合或不可读缓存会作为提示性 warning
输出，不会让验证失败；已安装角色、策略、Hook、配置或隐私检查存在缺陷时仍会
fail-closed。

## 文件结构

- `agents/`：Codex 自定义 Agent 定义。
- `hooks/`：显示子 Agent 启动信息的生命周期 Hook。
- `policy/subagent-routing.md`：全局加载的路由策略。
- `policy/routing-scenarios.json`：合成路由凭证契约场景。
- `scripts/install.py`：幂等的用户级安装器。
- `scripts/verify.py`：安装状态和可公开性检查。
- `tests/`：安装器与路由策略回归测试。

## 发布

仓库不应包含个人路径、账号标识、私有配置、凭证或组织内部信息。发布或推送
到代码托管平台前，请检查完整 Git 历史并运行验证命令。
