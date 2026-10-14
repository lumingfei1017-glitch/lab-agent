from app.common.exceptions import BuinessException
from app.schemas.ai import ChatMessage, ChatRequest
from app.config import settings
from openai import OpenAI
import logging

from app.services import kb_service

logger = logging.getLogger(__name__)
SYSTEM_PROMPT = """你是智能实验室预约系统的助手，回答要简洁。
如果下面提供了实验室资料，请依据资料回答，不要编造资料里没有的时间、规则、设备。
你目前查不到真实的实验室空闲、设备库存、预约记录。
如果用户问现在哪些实验室能约、某台设备此刻有没有空，请说明去「实验室列表」查看。
除了实验室相关的问题之外，不要回复无关的问题。
"""


def get_client() -> OpenAI:
    """创建OPENAI的客户端"""
    if not settings.LLM_API_KEY:
        raise BuinessException(message="为获取到大模型的api_key")

    return OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)


def chat(data: ChatRequest):
    """大模型对话"""
    if not data.messages:
        raise BuinessException(message="对话内容为空")
    history = []

    for message in data.messages:
        if message.role in ("user", "assistant") and message.content.strip():
            history.append(message.model_dump())
        if not history:
            raise BuinessException(message="请输入您要对话的内容")

    question = next(
        (item["content"] for item in reversed(history) if item["role"] == "user"), ""
    )
    knowledge = kb_service.search(query=question)

    # print(f"检索到的向量库的数据：{knowledge}")
    system_prompt = SYSTEM_PROMPT
    if knowledge:
        system_prompt += "\n\n以下是实验室检索到的资料:\n" + knowledge

    client = get_client()

    try:
        res = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                *history,
            ],
        )
        content = res.choices[0].message.content
        if not content.strip():
            raise BuinessException(message="大模型没有返回内容")
        return content

    except Exception:
        # logger.exception("调用大模型失败")
        raise BuinessException(message="大模型调用失败")


if __name__ == "__main__":
    from app.services import kb_service

    # 先看集合里有多少条数据
    col = kb_service.get_collection()
    print("集合文档数:", col.count())

    # 再测检索
    knowledge = kb_service.search(query="实验室开放时间")
    print("=" * 50)
    print("检索结果：")
    print(repr(knowledge))  # 用 repr 看有没有隐藏空格
    print("类型:", type(knowledge))
    print("长度:", len(knowledge) if knowledge else 0)
