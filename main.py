import random

from pydantic import Field
from pydantic.dataclasses import dataclass

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.agent.tool import FunctionTool
from astrbot.core.astr_agent_context import AstrAgentContext
from astrbot.core.config import AstrBotConfig
from astrbot.core.provider.entities import LLMResponse

from .miloratts_api import milora_tts_request
from .utils import normalize_tts_text


@register(
    "astrbot_plugin_miloratts",
    "helloworld",
    "基于 Milora API 的文本转语音插件",
    "1.0.0",
)
class MiloraTTSPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.enable_tts = bool(config.get("enable_tts", True))
        self.strip_timestamps = bool(config.get("strip_timestamps", True))

        try:
            self.tts_probability = max(
                0, min(100, float(config.get("tts_probability", 50)))
            )
        except (TypeError, ValueError):
            logger.warning("tts_probability 配置值无效，已使用默认值 50")
            self.tts_probability = 50

        try:
            self.max_length = max(1, int(config.get("max_length", 100)))
        except (TypeError, ValueError):
            logger.warning("max_length 配置值无效，已使用默认值 100")
            self.max_length = 100

        try:
            self.min_length = max(1, int(config.get("min_length", 5)))
        except (TypeError, ValueError):
            logger.warning("min_length 配置值无效，已使用默认值 5")
            self.min_length = 5

        self.too_long_strategy = str(config.get("too_long_strategy", "truncate")).lower()
        if self.too_long_strategy not in ("skip", "truncate"):
            logger.warning(
                f"too_long_strategy 配置值无效({self.too_long_strategy})，已使用默认值 truncate",
            )
            self.too_long_strategy = "truncate"

        self.speaker = str(config.get("speaker", "派星星"))
        logger.info(
            "Milora TTS 插件已加载，音色: %s, 概率: %s%%, max_length: %s, too_long_strategy: %s",
            self.speaker,
            self.tts_probability,
            self.max_length,
            self.too_long_strategy,
        )

    async def initialize(self):
        logger.info("Milora TTS plugin 已经启用")

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        try:
            if not self.enable_tts:
                return

            if not self.probability(self.tts_probability):
                logger.debug("本次消息未命中 TTS 概率，跳过语音合成")
                return

            result = event.get_result()
            if not result or not result.chain:
                logger.debug("本次消息没有结果，跳过 TTS")
                return

            text_parts = []
            for component in result.chain:
                if hasattr(component, "text"):
                    text_parts.append(component.text)

            if not text_parts:
                logger.debug("本次消息没有文本，跳过 TTS")
                return

            original_text = "".join(text_parts).strip()
            llm_text = normalize_tts_text(
                original_text,
                strip_timestamps=self.strip_timestamps,
            )

            if len(llm_text) < self.min_length:
                logger.debug(
                    f"LLM 文本长度 {len(llm_text)} 小于下限 {self.min_length}，跳过语音合成"
                )
                return

            if len(llm_text) > self.max_length:
                if self.too_long_strategy == "skip":
                    if self.tts_probability >= 100:
                        logger.info(
                            "TTS 概率为 100%% 但文本过长(len=%s > max_length=%s)，策略=skip，跳过语音合成",
                            len(llm_text),
                            self.max_length,
                        )
                    else:
                        logger.debug(
                            "LLM 文本长度 %s 超过上限 %s，策略=skip，跳过语音合成",
                            len(llm_text),
                            self.max_length,
                        )
                    return

                llm_text = llm_text[: self.max_length].rstrip()
                if self.tts_probability >= 100:
                    logger.info(
                        "TTS 概率为 100%%，文本过长(len=%s)，已按 max_length=%s 截断后合成语音",
                        len(original_text),
                        self.max_length,
                    )
                else:
                    logger.debug(
                        "LLM 文本长度 %s 超过上限 %s，已截断后合成语音",
                        len(original_text),
                        self.max_length,
                    )

                if len(llm_text) < self.min_length:
                    logger.debug(
                        "截断后的文本长度 %s 小于下限 %s，跳过语音合成",
                        len(llm_text),
                        self.min_length,
                    )
                    return

            logger.info(f"正在合成 Milora 语音: {llm_text[:50]}...")
            tts_result = await milora_tts_request(llm_text, self.speaker)

            if not tts_result:
                logger.warning("语音合成返回空数据，跳过本次语音回复")
                return

            if tts_result.get("code") != 200:
                logger.warning(f"语音合成失败: {tts_result.get('msg')}")
                return

            audio_url = tts_result.get("url")
            if not audio_url:
                logger.warning("语音合成返回为空 URL，跳过")
                return

            result = event.get_result()
            if result is None:
                logger.warning("合成完成但 event result 已失效，跳过")
                return
            result.chain = [Comp.Record(file=audio_url)]
            logger.info(f"语音合成完成: {audio_url}")

        except Exception as e:
            logger.error(f"Error in on_decorating_result: {e}")

    def probability(self, percent: int) -> bool:
        try:
            p = float(percent)
        except (TypeError, ValueError):
            return False
        p = max(0.0, min(100.0, p))
        return random.random() < (p / 100)

    async def terminate(self):
        logger.info("Milora TTS plugin 已经停用/卸载")


@dataclass
class MiloraTTSFunctionTool(FunctionTool[AstrAgentContext]):
    name: str = "milora_tts"
    description: str = "将文本转为语音发送的工具"
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "需要转换为语音的文本",
                },
            },
            "required": ["text"],
        }
    )
