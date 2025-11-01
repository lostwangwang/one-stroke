import os
import base64
from typing import Optional, Dict, Any

# 可替换为 Azure OpenAI，或其它具备视觉理解能力的模型客户端
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def explain_with_llm(
    image_b64: Optional[str], state: Dict[str, Any], suggested_move: Optional[list]
) -> Optional[str]:
    """
    使用视觉大模型生成自然语言讲解。
    若未配置 OPENAI_API_KEY 则返回 None。
    """
    if not OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)

        parts = []
        # 结构化状态优先，减少识别误差
        parts.append(
            {
                "type": "text",
                "text": (
                    "你是一名益智游戏讲解助手。游戏是“一笔画/欧拉路径”。"
                    "请基于提供的结构化状态，先判断下一步可行走的边，并给出简洁讲解。"
                    "如果附带了截图，仅用于辅助核对，不要仅凭截图推断错误信息。\n\n"
                    f"结构化状态(JSON):\n{state}\n\n"
                    f"算法建议的下一步(若有): {suggested_move}"
                ),
            }
        )
        if image_b64:
            parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                }
            )

        resp = client.chat.completions.create(
            model="gpt-4o-mini",  # 可换 gpt-4o / gpt-4.1 等具备视觉能力的模型
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "输出简洁的中文说明：\n"
                        "1) 当前端点与其可走的边有哪些；\n"
                        "2) 推荐下一步及理由（如保持未走边连通、防止卡死）；\n"
                        "3) 若已无路或已完成，说明原因。"
                    ),
                },
                {"role": "user", "content": parts},
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        # 失败则交给上层退回到本地讲解
        return None
