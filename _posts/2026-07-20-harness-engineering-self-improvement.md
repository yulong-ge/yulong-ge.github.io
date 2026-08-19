---
layout: post
title: "从 Context Engineering 到 Self-Improving Harness：读 Lilian Weng 的 Harness 博客"
date: 2026-07-20 10:00:00 +0800
description: "Lilian Weng《Harness Engineering for Self-Improvement》的结构化解读：从 ACE、MCE、Meta-Harness 到 Self-Harness 的放权层级，workflow 自动设计、harness 与权重联合优化，以及通往 Full RSI 的七个开放挑战。"
tags: [Agent, Harness, 读书笔记]
categories: [research-notes]
lang: zh-CN
giscus_comments: true
---

近日研读了 Lilian Weng 的博客文章《Harness Engineering for Self-Improvement》[1]。这篇博客系统梳理了 Agent 脚手架（Harness）的设计模式与优化方法，并提出了通往完全递归式自我改进（Full RSI）道路上的若干开放性挑战。作为一名正在探索 Agent 方向的研究者，本文尝试对该博客的核心内容做一个结构化的梳理，并穿插一些个人的思考与评论，供同行参考与讨论。

需要先说明的是：博客原文将被优化对象的演进概括为"instruction prompts → structured context → workflow → harness code → optimizer code"这一连续谱系[1]。本文第一部分将其重组为"四个层级"的叙述框架，是我个人基于博客内容所做的归纳，而非原文的显式分类，特此注明。

## 一、Harness 优化的四个层级：一部"放权"的历史

若以"优化对象"与"优化主导权"为坐标，博客中讨论的工作可以组织为四个递进的层级。若加以提炼，这条演进线索的本质是**逐步放权**——将越来越多原本由人类固化的设计决策，开放给 Agent 自身去修改。

**1. Agentic Context Engineering（ACE）。** 这一层级的代表工作是 ACE（Zhang et al., ICLR 2026）[2]：它将上下文视为一本持续演进的 playbook，由 Generator、Reflector、Curator 三个组件维护结构化的条目式上下文。值得注意的是，尽管 ACE 已经能从 rollout 中提炼经验，但其更新规则与整体工作流仍是人工设计的——人类预先规划好改进的流程，模型在这一既定流程内改进自身的上下文。

**2. Meta Context Engineering（MCE）。** MCE（Ye et al., 2026）[3] 将"如何管理上下文"的机制本身从上下文内容中剥离出来，构成一个双层优化：外层通过 agentic crossover 在历史技能库上进化"上下文工程技能"（skill），内层由 base-level agent 执行技能并从训练 rollout 中学习具体的上下文函数。人类不再显式指定更新上下文的规则，改进的方法论本身成为可进化的对象。

**3. Meta-Harness。** Meta-Harness（Lee et al., 2026）[4] 将优化对象从上下文扩展到**代码**——即决定"哪些信息应被存储、检索并呈现给模型"的 harness 代码本身。其外置优化循环中的 proposer 本身就是一个 coding agent，通过文件系统访问全部历史候选的源码、得分与执行轨迹，最终输出 Pareto 前沿上的 harness 候选集合。"Meta-"的含义即：这是一个用于优化 harness 的 harness。

**4. Self-Improving Harness。** 这是放权逻辑的终点：Agent 不再借助外部循环，而是直接参与改进自身的 harness。这一方向可以追溯到 STOP（Zelikman et al., COLM 2024）[5]——递归式自我改进脚手架的早期工作；近期的代表是 Self-Harness（Zhang et al., 2026）[6]，通过"weakness mining → harness proposal → proposal validation"的闭环，让模型基于自身执行轨迹中的失败模式提出有界的 harness 修改，并在 held-in/held-out 回归测试通过后才合入。另一个相关工作是 Darwin Gödel Machine（DGM; Zhang et al., 2025）[7]，允许 coding agent 修改自身的 harness 代码库，在 SWE-bench 上从 20.0% 提升至 50.0%、在 Polyglot 上从 14.2% 提升至 30.7%。

回顾这一脉络，可以看到一条清晰的"能力边界外扩"轨迹：从仅可修改上下文，到可修改工作流，再到可修改 harness 代码乃至优化器代码。在这一视角下，Mario Zechner（badlogic）设计的 Pi coding agent [8][9] 可以被视为一个"充分放权"的产品设计范例：它奉行极简的 harness 设计哲学，将定制能力完全交给用户——通过 TypeScript extensions、skills、prompt templates 等机制深度改造 Agent 行为[9]，其扩展机制的设计目标就是让用户"Adapt Pi to your workflows, not the other way around"[8]。这与 Claude Code 等以 hooks 为主的受控扩展方式形成了设计哲学上的对比（此为笔者基于公开文档的个人观察）。Pi 的代码库我已列入后续的阅读计划。

## 二、Workflow Design：从人工规划到自动化的 Agentic 系统设计

与 Harness 优化并行的另一条线索是工作流设计（Workflow Design），即如何设计 Agent 的工作流程。这一线索同样遵循"从受限到放权"的演进规律：

1. **人类预先规划 Workflow。** 典型代表是 AI Scientist（Lu et al., Nature 2026）[10]，由专家手工设计从 idea 生成、实验执行、论文写作到自动评审的完整管线；Karpathy 的 autoresearch 仓库[11]则是一个极简的范例：Agent 在固定的单文件训练代码上自主迭代实验，人类通过 `program.md` 以"编程程序"的方式设定研究组织的规则。面向数据合成的 Autodata（Kulikov et al., 2026）[12] 也属于人工设计工作流的范畴。
2. **Workflow 允许一定程度的自定义。**
3. **Agent 自主设计自身的 Workflow。** 即 Hu, Lu 与 Clune 提出的 **Automated Design of Agentic Systems（ADAS）** 研究域[13]（ICLR 2025），其 Meta Agent Search 算法由 meta-agent 以代码形式编程出新的 agentic workflow；后续工作 AFlow（Zhang et al., ICLR 2025）[14] 进一步将工作流表示为图，用蒙特卡洛树搜索（MCTS）进行优化，在多个基准上超过了手工设计的工作流与 ADAS。

## 三、Harness 与模型权重的联合优化

博客中另一个颇具新意的视角是 Harness 与模型权重的联合优化（Joint Optimization）。当前主流 Coding Agent 的部署形态是：模型在相对固定的 Harness 环境下工作（OpenAI 工程博客对 Codex harness 的 agent loop 有详细拆解[15]），训练与优化主要作用于模型权重，Harness 保持冻结。而下一步的自然延伸，便是让 Harness 与模型权重协同更新。

这一方向已有初步探索：SIA（Hebbar et al., 2026）[16] 尝试在同一优化循环中结合 harness 更新与权重更新，由 Feedback-Agent 根据近期轨迹决定下一轮更新 harness 还是模型权重。需要指出的是，Weng 在博客中对 SIA 的实验设计提出了保留意见——其 task-specific agent 远弱于 Meta-Agent 与 Feedback-Agent 所用的模型，且 baseline 设置偏弱，使得结果难以与相关方法干净地对标；她认为方向有趣，但证据尚属初步[1]。就个人判断而言，这是一个相当前沿但也颇具门槛的方向——它涉及模型权重更新，对算力和训练工程能力均有较高要求。即便具备一定算力条件，小规模模型上的联合优化能否取得理想效果，仍有待验证。尽管如此，该方向值得持续跟踪。

## 四、Future Challenges：七个开放性瓶颈

博客最有价值的部分，是作者基于前期调研提出的七个开放性挑战[1]。这些挑战与我日常使用 Coding Agent 产品时体会到的痛点高度吻合。以下按博客原有顺序重新组织，并附上个人评论。

### 4.1 弱而模糊的评估器（Weak and Fuzzy Evaluators）

这是博客提出的第一个挑战，也是我认为最根本的一个。对于代码任务，我们拥有相对明确的评估器——编写测试用例并运行，即可较为准确地衡量 Agent 的工作成效。但对于 Auto Research 这类任务，情况截然不同：一个研究 idea 可行与否如何建模？"Research taste"——即问题定义、实验设计、以及对"哪些反常结果值得深究、哪些失败值得重试"的判断力——如何度量？当前的自我改进循环仅在评估指标客观可测的任务上表现良好，这与 RL 的适用条件如出一辙[1]。

### 4.2 上下文与记忆的生命周期（Context and Memory Lifecycle）

在长周期的科研任务或代码库的长期维护中，Context 与 Memory 的生命周期应如何设计？何时将记忆移交（Hand Off）至外部文档？记忆应以何种形式组织？这实际上指向一个独立的研究领域——Agent Memory。Weng 提出了一个值得品味的类比：既然人类能够终身维持记忆，那么 Context Engineering 理应成为智能的核心组成部分，而非停留在软件系统层面[1]。

### 4.3 负结果的缺失（Negative Results）

这是直觉上我认为最合理、也最容易被忽视的一点。大模型的训练语料绝大多数由人类创造，而人类的知识产出系统性地偏向成功——以 Auto Research 为例，模型接触到的论文几乎全是已经成功发表的结果，它无从知晓什么样的结果应当被拒绝、什么样的结果属于失败，更缺乏判断"何时放弃一个假设"的能力。由此引出的问题是：**一个面向科研的 Harness，应如何让失败的尝试更容易被保留下来？** 从失败中学习无疑是削减搜索空间的高效途径，但这种经验如何内化到系统中，仍是一个环环相扣的难题[1]。

### 4.4 多样性崩塌（Diversity Collapse）

现有大模型普遍经过基于 RL 的 Post-Training（如 DeepSeek-R1 所代表的 RLVR 范式[17]），训练驱动模型向高奖励区域集中采样，导致生成分布的多样性逐渐趋同。对于 Auto Research 这类开放式任务，多样性的崩塌是致命的——因为在当前的评估器下，最优路径在初期可能看起来反而更差。这一问题本质上对应强化学习中的探索机制（Exploration）设计[18]。

### 4.5 奖励欺骗（Reward Hacking）

这是经典的 Goodhart 定律问题："当一项指标成为目标，它便不再是一个好的指标"（Goodhart, 1975；通行表述归于 Strathern）[19]。一旦某个信号成为自我改进循环的优化目标，模型便会设法"欺骗"它——若奖励来自单元测试，Agent 会过拟合测试；若来自裁判模型，它会习得针对该裁判的欺骗技巧；若来自 Benchmark 分数，它会利用数据集的伪迹[20]。Weng 给出的方向是：评估器与权限控制应当置于 Harness 进化循环**之外**，辅以留出测试（held-out tests）、轨迹审计（trace audits）与关键决策点的人工审查。监督能在多大程度上被规模化与自动化，仍是开放问题[1]。

### 4.6 长期成功（Long-term Success）

外在的优化循环作用于单个 Rollout 之外的奖励信号，而许多优化目标过于短视。以 Coding Agent 为例：它往往能完成手头任务，但如何维护一个由成百上千名工程师协作的代码仓库的长期健康——可维护性、所有权边界、迁移成本、向后兼容、未来的调试负担——标准的沙盒 RLVR 式训练几乎无法覆盖这些维度[1]。

### 4.7 人类的角色（The Role of Humans）

最后一点，也是我深有体会的一点：**人类应当沿抽象层级上移，而非被移出循环**。即使 Harness 进化至最优形态，关键环节仍离不开人类的参与——在恰当的时机、以恰当的抽象层级提供监督与纠偏。这也正是我在设计自己的科研工作流框架时所秉持的原则：不试图剔除人的作用，而是将系统设计为人类与 Agent 协同工作的文档化组织形式。如何在系统设计中设置这样的人机接触点（touch points），本身就是值得研究的问题[1]。

## 五、结语

这篇博客的阅读体验印证了一个方法论上的体会：优质博客往往已经完成了 Literature Tree 中的大量 Milestone 梳理，并给出了前沿的 Challenge 图谱，恰好对应科研方法论中的 Challenge 与 Insight Tree。对于研究者而言，剩下的工作便是基于 Note Tree，结合这些 Challenge 去审视已有方法，从中组合出新的解决方向。就个人而言，负结果保留、评估器建模与人机协同机制这三个挑战与我的研究兴趣最为贴近，值得作为后续深入调研的切入点。

---

## 参考文献

[1] Weng, Lilian. "Harness Engineering for Self-Improvement." *Lil'Log*, July 4, 2026. <https://lilianweng.github.io/posts/2026-07-04-harness/>

[2] Zhang, Qizheng, et al. "Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models." ICLR 2026. arXiv:2510.04618. <https://arxiv.org/abs/2510.04618>

[3] Ye, Haoran, et al. "Meta Context Engineering via Agentic Skill Evolution." arXiv:2601.21557, 2026. <https://arxiv.org/abs/2601.21557>

[4] Lee, Yoonho, et al. "Meta-Harness: End-to-End Optimization of Model Harnesses." arXiv:2603.28052, 2026. <https://arxiv.org/abs/2603.28052>

[5] Zelikman, Eric, et al. "Self-Taught Optimizer (STOP): Recursively Self-Improving Code Generation." COLM 2024. arXiv:2310.02304. <https://arxiv.org/abs/2310.02304>

[6] Zhang, Hangfan, et al. "Self-Harness: Harnesses That Improve Themselves." arXiv:2606.09498, 2026. <https://arxiv.org/abs/2606.09498>

[7] Zhang, Jenny, et al. "Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents." arXiv:2505.22954, 2025. <https://arxiv.org/abs/2505.22954>

[8] Pi Coding Agent 官网. <https://pi.dev/>

[9] Zechner, Mario. "What I learned building an opinionated and minimal coding agent." November 30, 2025. <https://mariozechner.at/posts/2025-11-30-pi-coding-agent/>

[10] Lu, Chris, et al. "Towards end-to-end automation of AI research." *Nature*, 651:914–919, 2026. <https://www.nature.com/articles/s41586-026-10265-5>

[11] Karpathy, Andrej. "autoresearch: AI agents running research on single-GPU nanochat training automatically." GitHub. <https://github.com/karpathy/autoresearch>

[12] Kulikov, Ilia, et al. "Autodata: An agentic data scientist to create high quality synthetic data." arXiv:2606.25996, 2026. <https://arxiv.org/abs/2606.25996>

[13] Hu, Shengran, Cong Lu, and Jeff Clune. "Automated Design of Agentic Systems." ICLR 2025. arXiv:2408.08435. <https://arxiv.org/abs/2408.08435>

[14] Zhang, Jiayi, et al. "AFlow: Automating Agentic Workflow Generation." ICLR 2025. arXiv:2410.10762. <https://arxiv.org/abs/2410.10762>

[15] Bolin, Michael. "Unrolling the Codex agent loop." OpenAI, January 23, 2026. <https://openai.com/index/unrolling-the-codex-agent-loop/>

[16] Hebbar, Prannay, et al. "SIA: Self Improving AI with Harness & Weight Updates." arXiv:2605.27276, 2026. <https://arxiv.org/abs/2605.27276>

[17] DeepSeek-AI. "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning." *Nature*, 645:633–638, 2025. arXiv:2501.12948. <https://arxiv.org/abs/2501.12948>

[18] Weng, Lilian. "Exploration Strategies in Deep Reinforcement Learning." *Lil'Log*, June 7, 2020. <https://lilianweng.github.io/posts/2020-06-07-exploration-drl/>

[19] Goodhart, Charles A. E. "Problems of Monetary Management: The U.K. Experience." In *Papers in Monetary Economics*, Reserve Bank of Australia, 1975；通行表述 "When a measure becomes a target, it ceases to be a good measure" 归于 Strathern, Marilyn. "'Improving ratings': audit in the British University system." *European Review*, 5(3):305–321, 1997. 参见 <https://en.wikipedia.org/wiki/Goodhart%27s_law>

[20] Weng, Lilian. "Reward Hacking in Reinforcement Learning." *Lil'Log*, November 28, 2024. <https://lilianweng.github.io/posts/2024-11-28-reward-hacking/>

---

## 附录：原文 Challenges

> Toward full RSI, researchers have made real progress, but several bottlenecks remain.
>
> **1. Weak and fuzzy evaluators.** Many research claims do not have a fast and precise verifier, and the same is true for many real-world tasks. Current self-improvement loops work best for tasks when evaluation metrics are measurable and objective, similar as [how RL works](https://lilianweng.github.io/posts/2018-02-19-rl-overview/).
>
> Research taste, novelty, and long-term scientific value are much harder to measure. For example, research taste often mixes problem framing, experimental design, and judgment about which surprising results are worth pursuing and which failure cases are worth retries.
>
> **2. Context and memory lifecycle.** Memory grows as AI agents become more autonomous and independent. A useful harness needs to manage context and memory to complement existing limitation in long-context generation while still maximizing the success of long-horizon tasks. Since humans are able to maintain memory through our life time, I see an anoloy here that [context engineering](https://lilianweng.github.io/posts/2026-07-04-harness/#context-engineering) will and should become a core part of intelligence, rather than staying in the software system layer.
>
> **3. Negative results.** Researchers are incentivized to publish successful results and thus literature is biased toward successes. LLMs trained on a vast amount of data (mostly human created, at least for now, lol) may be bad at deciding when to abandon a hypothesis, report a negative result, or even acknowledge a failure due to the imablance of success vs failure cases in data. A research harness should make failed attempts easy to preserve, as learning from failure is the best way to trim down the task search space.
>
> **4. Diversity collapse.** Evolutionary and RL loops tend to exploit known high-reward patterns. We need [mechanisms](https://lilianweng.github.io/posts/2020-06-07-exploration-drl/) to prevent the population from collapsing into variants of the same solution. This is especially critical for open-ended research, where the best path may initially look worse under the current evaluator.
>
> **5. [Reward hacking](https://lilianweng.github.io/posts/2024-11-28-reward-hacking/).** A self-improvement loop optimizes whatever signal it is given. If the reward comes from unit tests, the agent may overfit to tests; if it comes from a judge model, it may learn reward hacking tricks specific to this judge; if it comes from benchmark scores, it may exploit benchmark artifacts.
>
> The evaluator and permission control should likely sit outside the loop that evolves harness, with held-out tests, trace audits, and human review at decision points that matter—how much oversight can be scaled up and automated remains an open research area.
>
> **6. Long-term success.** An extrinsic loop of optimization works on rewards outside of individual rollouts that we can simulate in training sandbox.
>
> Take coding agent as an example. Coding agents have already increased daily productivity in software engineering, but many optimization goals are still too short-term. It can often complete the task at hand, but less obvious how it should protect the long-term health of a repo collectively maintained by hundreds or thousands of engineers. Standard sandbox-based RLVR-style training rarely captures maintainability, ownership boundaries, migration cost, backwards compatibility, or future debugging burden.
>
> **7. The role of humans.** Humans should move up the stack, not be removed from the loop, meaning that human should provide oversight at the right time, at the right abstraction level and our system design should consider when and how to set up such touch points.
