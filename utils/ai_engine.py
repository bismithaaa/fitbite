def detect_intent(prompt):
    """
    Detects user intent from natural language prompt.
    Returns: weight_loss | muscle_gain | None
    """

    if not prompt:
        return None

    prompt = prompt.lower()

    weight_loss_keywords = [
        'lose', 'weight loss', 'fat', 'slim', 'reduce', 'cut', 'burn'
    ]

    muscle_gain_keywords = [
        'gain', 'muscle', 'bulk', 'increase', 'strength'
    ]

    for word in weight_loss_keywords:
        if word in prompt:
            return 'weight_loss'

    for word in muscle_gain_keywords:
        if word in prompt:
            return 'muscle_gain'

    return None
