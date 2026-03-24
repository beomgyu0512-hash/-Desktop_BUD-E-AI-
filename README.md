# Buddy 儿童 AI 学习伙伴

我们基于 [LAION 的 Desktop BUD-E](https://github.com/LAION-AI/Desktop_BUD-E) 做了儿童学习场景改造。当前目标不是做一个通用桌面助手，而是先做出“适合孩子和家长使用“的学习陪伴体验。

当前仓库包含：

- 儿童模式系统提示词
- 面向儿童的学习技能
- 浏览器文字聊天入口
- 本地桌面文字聊天入口
- 家长设置面板
- 结构化长期档案
- 预留好的动态记忆适配层

## 现在能做什么

目前项目已经可以用于以下场景：

- 浏览器中进行中文文字聊天
- 用家长设置面板保存孩子资料
- 根据孩子档案调整后续回答
- 通过本地技能回答时间、生成学习计划、做儿童化解释
- 在代码层为后续 `mem0` 动态记忆接入做好准备

当前项目更适合：

- 本地开发
- 产品原型验证
- 家长和朋友小范围体验

## 下一步目标

- 用大量数据和对话测试长期记忆功能
- 训练、微调模型
  - 在儿童使用时的适配性
  - 实现家长通过自然语言对话设置和核对需求
- 实现桌面客户端部署

## 当前入口

### 1. 终端文字模式

```sh
python3 buddy.py
```

如果你只想在终端里打字测试，使用：

```sh
export BUD_E_DISABLE_WAKE_WORD=1
export BUD_E_TEXT_MODE=1
export BUD_E_SYSTEM_PROMPT_FILE=prompts/child_learning_companion_system_prompt.txt
python3 buddy.py
```

### 2. 浏览器模式

```sh
python3 web_app.py
```

然后打开：

```text
http://127.0.0.1:8000
```

浏览器版本当前支持：

- 文字聊天
- 新对话
- 家长设置
- 长期档案保存

### 3. 桌面模式

```sh
python3 desktop_app.py
```

桌面版目前是最小可用文字聊天客户端，和网页版共用同一套会话、技能和记忆逻辑。

## 环境变量

至少需要：

- `MOONSHOT_API_KEY`
- `DEEPGRAM_API_KEY`

常用配置：

- `KIMI_BASE_URL` 默认 `https://api.moonshot.cn/v1`
- `KIMI_MODEL` 默认 `moonshot-v1-8k`
- `BUD_E_SYSTEM_PROMPT_FILE` 默认可指向 `prompts/child_learning_companion_system_prompt.txt`
- `BUD_E_DISABLE_WAKE_WORD=1` 开发阶段跳过唤醒词
- `BUD_E_TEXT_MODE=1` 终端打字模式
- `BUD_E_WEB_HOST` 默认 `127.0.0.1`
- `BUD_E_WEB_PORT` 默认 `8000`

如果要启用 `mem0`：

- `MEM0_API_KEY`
- `BUD_E_DYNAMIC_MEMORY_PROVIDER=mem0`
- `BUD_E_MEM0_MODE=platform`

示例模板见：
[.env.example](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/.env.example)

## 中文默认行为

这个 fork 已经改成“中文优先”：

- 儿童提示词默认用简体中文
- 网页默认文案和家长设置示例是中文
- 儿童技能默认输出中文
- Deepgram 语音识别默认是 `zh-CN`

当前语音边界：

- 中文识别已默认开启
- 中文文字回答已默认开启
- Deepgram Aura 目前不作为中文 TTS 使用，如果要真正的中文语音播报，后面需要切换 TTS 提供方

## 长期记忆设计

项目当前使用两层记忆。

### 1. 主档案：`child_profile.json`

用于保存稳定、家长可控的信息：

- 孩子姓名
- 年龄
- 兴趣
- 学习目标
- 最近学习主题
- 家长偏好
- 稳定的 `child_id`

这份档案是当前系统的 `source of truth`。

### 2. 动态记忆层

用于处理“从对话里长出来的记忆”，例如：

- 最近常卡住的知识点
- 更适合的讲解方式
- 近期反复出现的话题
- 学习进步趋势摘要

当前状态：

- 规则层已经接好
- 适配层已经预留 `mem0`
- 默认 provider 仍然是 `none`

目前长期记忆主力是 `child_profile.json`，未来可能更新为 `mem0`。

## 动态记忆规则

动态记忆先过滤，不保存所有对话。

当前倾向于保存：

- 稳定偏好
- 反复出现的困难点
- 进步趋势摘要
- 学习风格偏好
- 对教学有帮助的家长引导

当前会跳过：

- 敏感信息
- 一次性临时请求
- “现在几点”这类工具型问题
- 逐题流水账
- 低价值寒暄

规则实现见：
[dynamic_memory_rules.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/dynamic_memory_rules.py)

## 主要文件

- [buddy.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/buddy.py)
  终端和语音主入口
- [web_app.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/web_app.py)
  浏览器聊天入口
- [desktop_app.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/desktop_app.py)
  本地桌面聊天入口
- [buddy_session.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/buddy_session.py)
  共享会话与提示词编排层
- [skills/learning_companion.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/skills/learning_companion.py)
  儿童学习技能
- [child_profile.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/child_profile.py)
  长期主档案持久化
- [dynamic_memory.py](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/dynamic_memory.py)
  动态记忆适配层

## 已知限制

- 浏览器版目前只支持文字聊天
- `mem0` 代码入口已预留，但默认不启用
- 中文语音播报还没有切到正式可用的中文 TTS


## 部署

阿里云和其他服务器部署说明见：
[deployment.md](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/docs/deployment.md)

儿童模式集成说明见：
[child-learning-companion.md](/Users/clea/Documents/GitHub/基于BUD-E的儿童AI学习伴侣/-Desktop_BUD-E-AI-/docs/child-learning-companion.md)
