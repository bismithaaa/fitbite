import os
import google.generativeai as genai
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_ai_goal(prompt, selected_goal):
    if not prompt:
        return selected_goal

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a diet assistant. Decide the user's real fitness goal."
                },
                {
                    "role": "user",
                    "content": f"""
Dropdown goal: {selected_goal}
User message: "{prompt}"

Reply with ONLY ONE WORD:
weight_loss OR muscle_gain OR maintenance
"""
                }
            ],
            max_tokens=10
        )

        result = response.choices[0].message.content.strip().lower()

        if result in ["weight_loss", "muscle_gain", "maintenance"]:
            return result

    except Exception as e:
        print("OpenAI error:", e)

    return selected_goal
