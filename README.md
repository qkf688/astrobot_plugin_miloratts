# astrbot-plugin-miloratts

> [!NOTE]
> 本插件是 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 的语音合成扩展插件
> [AstrBot](https://github.com/AstrBotDevs/AstrBot) 是一个支持个人和群组对话的智能助理，可部署在 QQ、Telegram、飞书、钉钉、Slack、LINE、Discord、Matrix 等数十个主流即时通讯平台

## 插件功能

- 基于 Milora API 实现文本转语音（TTS）
- 支持 **150+ 种音色** 选择（派星星、温柔女友、高冷男声、新闻主播等）
- 支持 **概率触发**，可自定义 TTS 回复概率（0-100%）
- 支持 **文本长度控制**，避免过长文本合成
- 支持 **智能时间戳过滤**，减少无意义播报
- 在消息发送前（`on_decorating_result`）自动将文本结果替换为语音消息段

## 快速开始

### 安装插件

在 AstrBot 中安装本插件：

```bash
# 通过 AstrBot 插件市场安装
# 或手动上传插件文件到 plugins 目录
```

## 配置说明

### 关键配置项

| 配置项 | 类型 | 默认值 | 说明 |
| ------ | ---- | ------ | ---- |
| `enable_tts` | bool | `true` | 是否启用 TTS 功能 |
| `speaker` | string | `派星星` | 音色选择（从 150+ 种音色中选择） |
| `tts_probability` | int | `50` | TTS 回复概率（0-100） |
| `max_length` | int | `100` | TTS 最大字数，超过后按策略处理 |
| `min_length` | int | `5` | TTS 最小字数，小于该字数不使用语音 |
| `too_long_strategy` | string | `truncate` | 超长文本策略：`truncate`=截断后合成，`skip`=直接跳过 |
| `strip_timestamps` | bool | `true` | 移除单独一行的 ISO-8601 时间戳 |
| `skip_command_reply_tts` | bool | `true` | 指令回复（例如 `/sid`、`/help`）不转语音 |

### 可用音色示例

部分热门音色：

- **角色类**：派星星、温柔女友、魅力女友、病娇少女、傲娇大小姐
- **广播类**：新闻男声、新闻女声、电台广播、赛事解说
- **地域特色**：粤语男声、港普男声、台湾女生、东北老铁、川妹子
- **解说类**：游戏解说、军事解说、娱乐播报、知识讲解
- **经典角色**：如来佛祖、孙悟空、猪八戒、武则天、容嬷嬷

> 完整音色列表见 [_conf_schema.json](_conf_schema.json)

### 配置示例

```json
{
  "speaker": "温柔女友",
  "tts_probability": 80,
  "max_length": 150,
  "min_length": 3,
  "too_long_strategy": "truncate",
  "strip_timestamps": true,
  "skip_command_reply_tts": true,
  "enable_tts": true
}
```

## 工作原理

1. 当 LLM 返回文本消息后，插件在 `on_decorating_result` 阶段拦截
2. 检查是否命中 TTS 概率（`tts_probability`）
3. 对文本进行预处理（移除时间戳等）
4. 检查文本长度是否符合要求
5. 调用 Milora API 合成语音
6. 将原始文本消息替换为语音消息段

## 使用场景

- **情感化回复**：使用特定音色增强对话情感表达
- **广播通知**：使用新闻主播音色播报重要信息
- **角色扮演**：配合不同角色使用对应音色
- **无障碍辅助**：为视障用户提供语音反馈

## 相关资源

- [AstrBot 主项目](https://github.com/AstrBotDevs/AstrBot)
- [AstrBot 插件开发文档（中文）](https://docs.astrbot.app/dev/star/plugin-new.html)
- [AstrBot 插件开发文档（英文）](https://docs.astrbot.app/en/dev/star/plugin-new.html)
- [Milora API 文档](https://docs.milora.cc/)

## 许可证

本项目采用 [MIT 许可证](LICENSE)
