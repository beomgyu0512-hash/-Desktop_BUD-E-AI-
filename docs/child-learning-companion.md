# 儿童学习伙伴集成说明

这份文档只说明这个 fork 额外加了什么，以及这些改动为什么不会把上游 BUD-E 主链路搞乱。

## 这次加了什么

核心新增分成四层：

1. 儿童模式提示词  
2. 儿童学习技能  
3. 浏览器和桌面聊天入口  
4. 长期记忆与动态记忆骨架

对应文件：

- [prompts/child_learning_companion_system_prompt.txt](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/prompts/child_learning_companion_system_prompt.txt)
- [skills/learning_companion.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/skills/learning_companion.py)
- [web_app.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/web_app.py)
- [desktop_app.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/desktop_app.py)
- [child_profile.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/child_profile.py)
- [dynamic_memory.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/dynamic_memory.py)

## 为什么这些改动相对安全

这次改动遵守了一个原则：尽量把新增能力放在外层，不直接把上游主入口改成难以维护的分支代码。

目前的安全点：

- 儿童提示词通过 `BUD_E_SYSTEM_PROMPT_FILE` 切换
- 儿童技能仍然遵循 BUD-E 的原始技能签名
- `buddy.py` 仍然保留为终端/语音主入口
- 浏览器版和桌面版走共享会话层，而不是把语音逻辑硬塞进网页
- 动态记忆默认 provider 是 `none`，不会在未确认前自动写入外部系统

## 中文默认策略

这个 fork 已经明确改成中文优先：

- 默认回答语言是简体中文
- 儿童技能默认返回中文
- 网页默认示例和家长设置为中文
- 语音识别默认是 `zh-CN`

目前的边界：

- 中文理解没有问题
- 中文文字回复没有问题
- 中文语音播报还没有切到正式可用的中文 TTS

## 当前可用入口

### 终端模式

适合开发时快速调试。

常用环境变量：

- `BUD_E_DISABLE_WAKE_WORD=1`
- `BUD_E_TEXT_MODE=1`
- `BUD_E_SYSTEM_PROMPT_FILE=prompts/child_learning_companion_system_prompt.txt`

### 浏览器模式

运行：

```sh
python3 web_app.py
```

适合：

- 给别人试用
- 展示聊天效果
- 编辑家长设置

### 桌面模式

运行：

```sh
python3 desktop_app.py
```

适合：

- 本地文字聊天
- 后续继续接语音按钮和系统能力

## 长期记忆设计

### 主档案

主档案存放在 `child_profile.json`。

这层负责稳定事实：

- 姓名
- 年龄
- 兴趣
- 学习目标
- 最近主题
- 家长偏好
- `child_id`

它是当前项目的记忆主线，也是家长设置面板真正修改的数据源。

### 动态记忆

动态记忆层用于保存“从互动中慢慢长出来”的信息。

更适合放这里的内容包括：

- 最近常卡住的知识点
- 更适合的解释方式
- 近期反复出现的话题
- 学习进步趋势摘要

当前状态：

- 规则层已接好
- 适配层已接好
- 默认仍然关闭

所以现在项目依然是“主档案已经工作，动态记忆尚未正式启用”的状态。

## 动态记忆规则

动态记忆目前不会盲目存所有聊天。

倾向于保留：

- 稳定偏好
- 反复出现的学习困难
- 学习结果摘要
- 教学风格偏好
- 有帮助的家长指导

会主动跳过：

- 敏感个人信息
- 一次性工具请求
- “现在几点”这种短期问题
- 逐题练习流水
- 没信息量的客套话

这层规则的目标很简单：

- 记趋势，不记流水
- 记规律，不记题号
- 记教学意义，不记聊天噪声

## mem0 的位置

项目现在已经给 `mem0` 留好了入口，但还没有默认启用。

推荐的角色分工是：

- `child_profile.json` 负责主档案
- `mem0` 负责补充型动态记忆

也就是说，后面真接 `mem0` 时，也不应该让它覆盖孩子年龄、家长偏好这类主档案信息。

## 本地数据采集

为了后续做产品评估和训练前分析，项目现在会把关键事件写入本地 JSONL 日志。

默认路径：

- `analytics/events.jsonl`

当前会记录：

- 会话开始
- 聊天请求
- 最终回答
- 家长设置更新
- 会话重置
- 动态记忆召回数量
- 动态记忆是否保存，以及为什么保存或跳过

这层日志的目标是先让系统具备可分析性，而不是把所有原始对话当作正式数据仓库长期堆积。

## 当前更适合继续做什么

如果继续往下开发，优先级建议是：

1. 切到正式可用的中文 TTS
2. 扩充儿童学习技能
3. 再启用 `mem0`
4. 最后再做更细的学习轨迹与家长报告
