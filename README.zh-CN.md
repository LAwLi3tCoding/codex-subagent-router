# Codex Subagent Router

[English](README.md)

为会话已经决定执行的子代理任务选择模型和推理强度。Router 只负责这两个参数；是否启动子代理、选择哪个角色、是否独立审核、何时升级以及修复后是否复核，由当前会话、项目规则或显式工作流决定。

## 选择规则

保留人工选择的主模型和 effort，包括 Ultra。模型和 effort 分别判断：保留用户明确指定的参数及任务或角色已有的绑定，只为未指定的参数提供建议。

Router 使用六个自动路由组合：

| 模型 + effort | 选择边界 |
| --- | --- |
| **Sol/low**（`gpt-6.1-sol`） | 解法已知、范围封闭、输入和检查明确，主要是机械执行。 |
| **Sol/medium** | 需求和影响范围明确，需要局部判断。 |
| **Sol/high** | 关键问题未决，需要验证假设或比较方案。 |
| **Sol/xhigh** | 多个约束跨组件或状态相互影响，需要联合分析。 |
| **Sol/max** | 问题、证据和约束已明确，但需要深入推演多个路径和方案才能形成完整结论。 |
| **Astra/xhigh**（`gpt-6-astra`） | 问题框架可能不充分，证据已具备，需要重新组织整体解释或设计，且有具体理由预期 Sol 不足以完成。 |

**默认使用 Sol，Luna 不参与自动选择。** Astra/high、Astra/max 只接受显式选择。用户明确参数和角色固定绑定优先，并限制可选的自动组合。

Sol/max 负责把已明确的难题推演完整；Astra/xhigh 负责重新审视问题框架。边界不清时优先 Sol，选用 Astra 时简要说明具体需求。两者都不要求先跑一轮较低档位。这些边界是选择规则，尚未通过任务实测证明质量、成本或耗时优势。完整规则见[路由策略](policy/subagent-routing.md)。

Sol 按当前任务选择足够完成工作的最低 effort。高风险、领域名称、需要审核、任务长或主会话使用 Ultra，本身都不足以升档。证据缺失和工具失败应先恢复依赖。在已有阶段边界重新评估：设计确定后，常规实现通常回到 Sol/medium，机械收尾回到 Sol/low。不为换档新增、重启、拆分或重复任务。

规则是模型选择说明，不是运行时拦截器。仅通过运行时支持且兼容所选角色和上下文的参数应用建议。某档不可用时，只有其他合规且受支持的组合足以完成任务，才使用该组合；否则保留原调用并说明限制。不通过更换角色、上下文、配置或流程强行应用映射。安装成功不证明子代理实际使用了建议参数。

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
