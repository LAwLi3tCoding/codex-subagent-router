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

安装器会：

1. 将角色配置安装到用户的 Codex 配置目录。
2. 在全局 Codex `AGENTS.md` 中写入一个受管理的路由规则区块。
3. 启用多 Agent 能力，但不设置共享并发上限。
4. 移除全局子 Agent 默认模型配置，使 `default` 继承当前会话。
5. 替换受管理目标前创建带时间戳的本地备份。

安装器还会清理旧版全局规则中固定子 Agent 数量的语句，同时保留所有无关
配置和说明。更新仓库后可再次运行安装器；安装过程是幂等的。

路由策略会写入全局 Codex `AGENTS.md`，因此每个新会话都会自动加载，不需要
shell 启动 hook 或常驻进程。

## 验证

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify.py
```

验证覆盖角色与模型矩阵、`default` 继承、全局受管理规则、配置解析、安装
幂等性和仓库隐私检查。

## 文件结构

- `agents/`：Codex 自定义 Agent 定义。
- `policy/subagent-routing.md`：全局加载的路由策略。
- `scripts/install.py`：幂等的用户级安装器。
- `scripts/verify.py`：安装状态和可公开性检查。
- `tests/`：安装器回归测试。

## 发布

仓库不应包含个人路径、账号标识、私有配置、凭证或组织内部信息。发布或推送
到代码托管平台前，请检查完整 Git 历史并运行验证命令。
