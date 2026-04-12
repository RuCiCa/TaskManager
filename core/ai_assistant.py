"""
AI 助手模組 — 使用 Anthropic Claude API
需要環境變數 ANTHROPIC_API_KEY 或在程式目錄放置 .env 檔案。
"""
import os
import json


def _get_client():
    import anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=api_key)


def decompose_task(goal: str) -> list[dict]:
    """
    將一個大目標分解為 3-5 個循序漸進的子任務。
    回傳 list of task_data dict，可直接傳入 manager.publish_new_task()。
    """
    client = _get_client()

    system_prompt = (
        "你是一個任務規劃 AI。使用者會給你一個目標，你要把它分解成 3 到 5 個具體、可執行的子任務。\n"
        "每個子任務必須包含：title（短標題）、content（一句話說明）、"
        "difficulty（EASY/MEDIUM/HARD 之一）、task_type（固定填 COUNTING）、"
        "target_count（建議完成次數，整數）、frequency（ONCE 或 PERIODIC）、publisher（固定 'AI'）。\n"
        "請僅回傳一個 JSON 陣列，不要有任何其他文字。"
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": f"目標：{goal}"}],
    )

    raw = message.content[0].text.strip()
    # 容錯：移除可能的 markdown code block
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    tasks = json.loads(raw)

    # 補齊必要欄位的預設值
    for t in tasks:
        t.setdefault('task_type', 'COUNTING')
        t.setdefault('frequency', 'ONCE')
        t.setdefault('difficulty', 'MEDIUM')
        t.setdefault('target_count', 1)
        t.setdefault('total_seconds', 0)
        t.setdefault('publisher', 'AI')

    return tasks


def chat(messages: list[dict]) -> str:
    """
    多輪對話：傳入完整的訊息歷史，回傳 AI 的最新回覆。
    """
    client = _get_client()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=(
            "你是遊戲化任務系統的 AI 助手，協助使用者規劃任務、分析進度、提供激勵與建議。"
            "語氣活潑、正向，請用繁體中文回覆，回覆盡量簡潔。"
        ),
        messages=messages,
    )
    return response.content[0].text.strip()


def generate_failure_message(task_title: str) -> str:
    """
    根據失敗的任務標題，生成一段帶有幽默感的毒舌鼓勵對話。
    """
    client = _get_client()

    system_prompt = (
        "你是一個毒舌但其實很關心使用者的任務督促 AI 教練。"
        "當使用者的任務失敗時，用幽默、帶刺但不傷人的語氣調侃他，"
        "同時給予一句真心的鼓勵，告訴他下次怎麼做才能成功。"
        "回覆限 100 字以內，繁體中文。"
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=system_prompt,
        messages=[{"role": "user", "content": f"我的任務失敗了：「{task_title}」"}],
    )

    return message.content[0].text.strip()
