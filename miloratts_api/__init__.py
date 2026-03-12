import aiohttp

try:
    from astrbot.api import logger  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    import logging

    logger = logging.getLogger(__name__)


async def milora_tts_request(text: str, speaker: str) -> dict:
    url = "https://api.milorapart.top/apis/AIvoice/"
    params = {
        "text": text,
        "speaker": speaker
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                result = await response.json()
                logger.info(f"Milora TTS API 返回: {result}")
                return result
    except Exception as e:
        logger.error(f"Milora TTS 请求失败: {e}")
        return {"code": 500, "msg": str(e)}
