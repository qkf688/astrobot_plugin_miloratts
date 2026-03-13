# 设计：@ 与 Emoji 分离发送，避免被 TTS 读出（MiloraTTS 插件）

日期：2026-03-13

## 背景

`astrobot_plugin_miloratts` 在 `on_decorating_result` 阶段将消息结果替换为语音段（`Record`），从而实现“文本转语音”。

当回复中包含：

- 群聊 `@`（`At` 组件，@别人/@所有人等）
- 平台表情组件（如 QQ `Face`、微信 `WechatEmoji`）
- 纯文本里的 Unicode emoji（例如 🙂🎉）

现有实现会将它们与文本一起丢进 TTS 或者在替换 `chain` 后直接丢失，导致：

- `@`/emoji 被读出来（不符合预期）
- `@`/emoji 组件被丢失（替换为 `Record` 后不再发送）

## 目标

- 当本次确实要走 TTS 并成功获得语音 URL 时，将 `@` 与 emoji 从 TTS 文本中剥离，**分别单独发送**：
  1) 先发送 `@`（仅包含 At 相关内容）
  2) 再发送 emoji（表情组件 + 抽取出的 Unicode emoji 文本）
  3) 最后发送语音（`Record`）
- 所有行为提供开关，可按需关闭。
- 若未触发 TTS（未命中概率/长度不符合/指令回复跳过/合成失败等），保持旧行为，不做分离发送。

## 非目标

- 不对纯文本中的 `@xxx` 做“看起来像 @”的解析（只处理真正的 `At` 组件），避免误伤邮箱/普通文本。
- 不尝试保留或重排除 `At/Face/WechatEmoji/Plain` 之外的其他富媒体组件（当前插件本就会在 TTS 时整体替换为 `Record`）。

## 方案（已确认 / 推荐）

采用“组件级分离 + Unicode emoji 抽取”的混合方案：

- 组件级：识别 `At` / `Face` / `WechatEmoji`，从结果链中提取出来
- 文本级：对 `Plain` 文本执行 Unicode emoji 的“尽力而为”抽取（不新增第三方依赖）

### 配置项（新增）

均为 `bool`，默认 `true`：

- `split_at_before_tts`：当回复链中包含 `At` 组件时，先单独发送 `@` 消息
- `split_emoji_before_tts`：当回复链中包含 `Face/WechatEmoji` 组件时，单独发送 emoji 消息
- `split_unicode_emoji_before_tts`：当纯文本中包含 Unicode emoji（🙂🎉 等）时，将其抽出并单独发送

### 处理流程（插件侧）

触发时机：仅在本次真的要发语音（命中概率 + 文本长度检查通过 + TTS 请求成功返回 URL）时进行。

1. 读取当前 `result.chain`
2. 从 `result.chain` 里提取：
   - `At` 组件列表（按原顺序）
   - emoji 组件列表（`Face` / `WechatEmoji`，按原顺序）
   - 从 `Plain` 文本中抽取 Unicode emoji，得到：
     - `unicode_emoji_text`（按原出现顺序拼接）
     - `remaining_text`（移除 emoji 后的文本）
3. 将 `remaining_text` 送入 `normalize_tts_text(...)`（保留既有时间戳过滤/空行折叠逻辑）
4. 若 `remaining_text` 长度不足或超长策略要求跳过：不做分离发送，保持原链走默认发送
5. 调用 Milora API 合成语音，获得 `audio_url`
6. 发送顺序（用户确认的顺序）：
   - 若 `split_at_before_tts` 且存在 `At`：`await event.send(MessageChain(at_chain))`
   - 若 `split_emoji_before_tts`/`split_unicode_emoji_before_tts` 且存在任何 emoji：
     - 先把表情组件加入 `emoji_chain`
     - 若 `unicode_emoji_text` 非空，再追加 `Plain(unicode_emoji_text)`
     - `await event.send(MessageChain(emoji_chain))`
   - `await event.send(MessageChain([Record(file=audio_url)]))`
7. 清空原结果链 `result.chain.clear()`，避免框架后续阶段再次发送原内容（并确保实际发送顺序由插件掌控）。

### Unicode emoji 抽取策略（尽力而为）

不引入第三方库（例如 `regex`），使用 Python 标准库实现“覆盖主流 emoji 的范围 + 处理常见连接符”：

- 覆盖常见 emoji 区段（如 U+1F300~U+1FAFF、U+2600~U+27BF 等）
- 支持变体选择符 `FE0F`、肤色修饰符（U+1F3FB~U+1F3FF）、ZWJ（U+200D）序列的拼接

该策略目标是“少读、尽量不漏”，允许极少数边界字符误判/漏判。

## 测试计划

保持单测不依赖 `astrbot` 包：

- 在 `utils.py` 增加纯函数（示例）：
  - `extract_unicode_emojis(text: str) -> tuple[str, str]`（返回 `emoji_text`, `remaining_text`）
- 在 `tests/test_utils.py` 覆盖：
  - 纯 Unicode emoji：`"🙂🎉"` ⇒ emoji 全提取，剩余为空
  - 文本混合：`"hi🙂there"` ⇒ emoji 提取为 `🙂`，剩余为 `"hithere"`（或按实现约定保留空格）
  - ZWJ/变体选择符/肤色修饰符的典型组合（至少 1-2 例）
  - 空输入/None 输入与现有 `normalize_tts_text` 一致的容错策略

## 风险与降级

- 若平台不允许发送“仅包含 At”的消息链：可在实现阶段增加最小不可见占位（例如零宽字符）作为降级；默认先不做，按实际平台适配器表现再决定。
- 若 TTS 合成失败：不发送任何拆分消息，保持原结果链走默认发送，避免“只发了 @/emoji 但没有语音”的半截体验。

