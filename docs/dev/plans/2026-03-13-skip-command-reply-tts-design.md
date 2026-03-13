# 设计：跳过“指令回复”的 TTS 转换（MiloraTTS 插件）

日期：2026-03-13

## 背景

`astrobot_plugin_miloratts` 通过 `on_decorating_result` 在消息发送前把结果文本替换为语音段，因此包括 `/sid`、`/help` 等真正匹配到的指令回复，也会被转成语音。

## 目标

- 当且仅当本次事件**确实匹配到指令处理器**时，跳过本插件的“文本转语音替换”逻辑。
- 不影响用户输入以 `/` 开头但**未匹配到任何指令**、最终走 LLM 的正常回复（仍可按概率转语音）。

## 非目标

- 不改 AstrBot 主项目的指令解析/管线逻辑。
- 不尝试识别“看起来像命令”的文本（仅依据实际匹配结果）。

## 方案（已确认）

使用 AstrBot 在 `WakingCheckStage` 中写入的 `event.extra["handlers_parsed_params"]` 作为“本次匹配到指令”的信号：

- `handlers_parsed_params` 为非空 `dict` ⇒ 至少有一个 `CommandFilter` 命中 ⇒ 本次为真实指令触发。
- 将判断封装为插件侧的纯函数，避免单测依赖 `astrbot` 包。

### 配置

新增配置项：

- `skip_command_reply_tts`：`bool`，默认 `true`
  - `true`：指令回复不转语音（本需求）
  - `false`：保持旧行为（指令回复也可能被转语音）

### 处理流程（插件侧）

在 `MiloraTTSPlugin.on_decorating_result` 的早期阶段增加：

- 若 `skip_command_reply_tts` 开启且检测到本次为指令触发：直接 `return`，不做任何替换/请求。

## 测试计划

在 `utils.py` 中新增纯函数（例如 `is_command_triggered(extras)`），并在 `tests/test_utils.py` 增加用例：

- `handlers_parsed_params` 缺失/不是 `dict`/为空 `dict` ⇒ 返回 `False`
- `handlers_parsed_params` 为非空 `dict`（值允许为空 dict）⇒ 返回 `True`

