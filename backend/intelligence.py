import os, openai
openai.api_key = os.getenv('OPENAI_API_KEY')

ADS = [
    {'id':'AD-001','file':'logitech_gpro_mouse.png','keywords':['gaming','tech','performance','pc']},
    {'id':'AD-002','file':'redbull_can.png','keywords':['gaming','energy','drink']},
]

def rank_ad(persona: dict, opportunity: dict) -> dict:
    prompt = (
        f"Persona: {persona.get('interests')}\n"
        f"Tags: {opportunity.get('tags')}\n"
        "Ads:\n"
    ) + ''.join([f"- {ad['id']}: {ad['keywords']}\n" for ad in ADS])
    prompt += "\nPick the single best ad ID."
    try:
        res = openai.Completion.create(
            model='gpt-4o-mini', prompt=prompt,
            max_tokens=5, temperature=0.2
        )
        choice = res.choices[0].text.strip().split()[0]
        return next(ad for ad in ADS if ad['id']==choice)
    except:
        # fallback heuristic
        context = set(persona.get('interests',[]))|set(opportunity.get('tags',[]))
        best,score=None,-1
        for ad in ADS:
            s = len(context & set(ad['keywords']))
            if s>score: best,score=ad,s
        return best