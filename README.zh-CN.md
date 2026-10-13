# Codex Subagent Router

[English](README.md)

为会话已经决定执行的子代理任务选择模型和推理强度。Router 只负责这两个参数；是否启动子代理、选择哪个角色、是否独立审核、何时升级以及修复后是否复核，由当前会话、项目规则或显式工作流决定。

## 选择规则

保留人工选择的主模型和 effort，包括 Ultra。用户明确指定的设置，以及任务或角色已有的模型与 effort 绑定，优先于 router 建议。子代理参数尚未指定时，建议使用 `gpt-6.1-sol`，并选择足够完成任务的最低 effort：

| Effort | 任务的不确定性 |
| --- | --- |
| `low` | 输入和验收明确、可机械检查的工作。 |
| `medium` | 需要局部判断的常规实现、有限范围调查或测试修复。 |
| `high` | 根因未明、跨模块兼容、开放设计，或已经决定执行且需要独立判断的审阅。 |
| `xhigh` | 并发、迁移、恢复中多个不变量相互影响，或已经决定执行的重大风险评估。 |

用户明确恢复之前，自动选择不使用 Astra。任务长度、文件数量、领域名称和主会话的 effort 本身不决定子代理强度。`max` 需要针对当前任务明确选择。

[路由规则](policy/subagent-routing.md) 是指导模型选择的说明，不是运行时拦截器。只有当前运行时支持兼容所选角色和上下文的模型与 effort 参数时，才应用建议。角色固定了参数或运行时不支持覆盖时，保留原调用，不通过更换角色或上下文模式强行应用映射。安装成功不证明子代理实际使用了建议参数。

## 安装

需要 Python 3.11 或更新版本。在当前仓库中运行：

```sh
sh ./install.sh
```

安装到其他配置目录，或指定说明文件：

```sh
sh ./install.sh --codex-home /path/to/profile
sh ./install.sh --codex-home /path/to/profile --global-agents /path/to/AGENTS.md
```

安装器只更新全局 `AGENTS.md` 中 router 标记内的内容。存在非空 `AGENTS.override.md` 时，默认使用该文件。标记外的说明保持不变；说明文件为符号链接时，更新其目标。修改前将说明备份到 `subagent-router-backups/`，通过原子写入更新；写入失败时尝试恢复，恢复不完整时报告备份位置。重复、不完整、顺序错误的标记或空策略会在写入前被拒绝。

安装器不创建或修改 `config.toml`，不启用 agents，不设置全局模型默认值，不安装、覆盖或删除角色文件，不改变权限、hooks 或审核流程。使用新会话加载更新后的说明。

## 从旧版升级

重新安装会替换旧 router 块，移除其中的委派和审核流程要求。新版不再提供角色模板。现有配置和角色文件保持不变，包括旧版安装的角色；这些角色仍可能包含旧流程说明和固定的模型与 effort 绑定。

完整迁移时，先检查并备份旧 router 的六个角色，再明确删除：`worker-low`、`worker-medium`、`worker-high`、`worker-xhigh`、`reviewer`、`risk-reviewer`。删除前检查项目中的引用；仍按名称调用这些自定义角色的工作流，需要自行维护角色定义。保留其他工具或项目的角色。

安装器不会自动清理角色，不会关闭子代理，也不会恢复旧版删除的配置。清理后重新安装说明并新建会话；现有会话仍可能保留已加载的旧指令和角色。

## 验证

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/verify.py --codex-home /path/to/profile
```

验证器检查 router 说明和源码隐私，不要求启用 agents 或安装特定角色。测试覆盖现有配置、角色、hooks、其他说明的保留，以及备份和失败恢复。实际模型与 effort 的验证方法见[任务级验证](docs/performance-validation.md)。

## 项目结构

```text
policy/                 仅包含模型和 effort 选择说明
scripts/install.py      仅更新说明，提供备份和失败恢复
scripts/verify.py       说明内容及源码隐私检查
tests/                  安装边界和失败恢复测试
```

提交和 GitHub 元数据中不得包含个人信息、内部信息、凭据、主机信息或本地绝对路径。
