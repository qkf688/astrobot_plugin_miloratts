# astrbot-plugin-miloratts

## 插件功能

- 基于 Milora TTS 实现文本转语音

> [!NOTE]
> This repo is just a template of [AstrBot](https://github.com/AstrBotDevs/AstrBot) Plugin.
> [AstrBot](https://github.com/AstrBotDevs/AstrBot) is an agentic assistant for both personal and group conversations. It can be deployed across dozens of mainstream instant messaging platforms, including QQ, Telegram, Feishu, DingTalk, Slack, LINE, Discord, Matrix, etc. In addition, it provides a reliable and extensible conversational AI infrastructure for individuals, developers, and teams. Whether you need a personal AI companion, an intelligent customer support agent, an automation assistant, or an enterprise knowledge base, AstrBot enables you to quickly build AI applications directly within your existing messaging workflows.

# Supports

- [AstrBot Repo](https://github.com/AstrBotDevs/AstrBot)
- [AstrBot Plugin Development Docs (Chinese)](https://docs.astrbot.app/dev/star/plugin-new.html)
- [AstrBot Plugin Development Docs (English)](https://docs.astrbot.app/en/dev/star/plugin-new.html)

## Milora TTS 配置说明

本插件会在发送消息前（`on_decorating_result`）把文本结果替换为语音消息段。


关键配置（见 `_conf_schema.json`）：

- `tts_probability`：0-100，转语音概率
- `max_length`：超过该长度视为“过长”
- `too_long_strategy`：`truncate`（默认，截断后合成）/ `skip`（直接跳过）
- `strip_timestamps`：默认开启，移除单独一行的 ISO 时间戳（减少无意义播报）
