import os
import openai

openai.api_key = os.getenv('OPENAI_API_KEY')

ADS = [
    {'id':'AD-001','file':'logitech_gpro_mouse.jpg','keywords':['gaming','tech','performance','pc']},
    {'id':'AD-002','file':'redbull_can.png',       'keywords':['gaming','energy','drink']},
]

def rank_ad(persona: dict, opportunity: dict) -> dict:
    prompt = f"Persona interests: {persona.get('interests')}\\nTags: {opportunity.get('tags')}\\nAds:\\n"
    for ad in ADS:
        prompt += f"- {ad['id']}: {ad['keywords']}\\n"
    prompt += "\nReturn only the best ad ID."

    try:
        res = openai.Completion.create(
            model='gpt-4o-mini',
            prompt=prompt,
            max_tokens=5,
            temperature=0.2
        )
        choice = res.choices[0].text.strip().split()[0]
        return next(a for a in ADS if a['id'] == choice)
    except Exception:
        # Fallback: keyword overlap
        ctx, best, score = set(persona.get('interests',[])) | set(opportunity.get('tags',[])), None, -1
        for ad in ADS:
            s = len(ctx & set(ad['keywords']))
            if s > score:
                best, score = ad, s
        return best