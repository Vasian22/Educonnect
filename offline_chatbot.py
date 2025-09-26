def offline_chatbot(user_input: str) -> str:
    responses = {
        "ਸਤ ਸ੍ਰੀ ਅਕਾਲ": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡੀ ਮਦਦ ਲਈ ਤਿਆਰ ਹਾਂ।",
        "ਤੁਹਾਡਾ ਨਾਮ ਕੀ ਹੈ": "ਮੇਰਾ ਨਾਮ EduConnect ਬੋਟ ਹੈ।",
        "ਮੈਨੂੰ ਗਣਿਤ ਸਿਖਾਓ": "ਗਣਿਤ ਸਿਖਣ ਲਈ ਤੁਸੀਂ ਜੋੜ, ਘਟਾਓ, ਗੁਣਾ, ਭਾਗ ਨਾਲ ਸ਼ੁਰੂ ਕਰੋ।",
        "ਅਲਵਿਦਾ": "ਅਲਵਿਦਾ! ਫਿਰ ਮਿਲਾਂਗੇ।"
    }

    if not user_input:
        return "ਕਿਰਪਾ ਕਰਕੇ ਕੁਝ ਲਿਖੋ 🙂"

    for key in responses:
        if key in user_input:
            return responses[key]

    return "ਮੈਨੂੰ ਅਜੇ ਇਸਦਾ ਜਵਾਬ ਨਹੀਂ ਪਤਾ, ਪਰ ਮੈਂ ਤੁਹਾਨੂੰ ਸਿਖਣ ਵਿੱਚ ਮਦਦ ਕਰਾਂਗਾ!"
