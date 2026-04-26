# TO DELETE

def interpret_results(baseline, current, relative, risk):

    direction = "stable"

    if relative > 2:
        direction = "increase in activity"
    elif relative < -2:
        direction = "decrease in activity"

    return {
        "summary": "Environmental signal analysis completed",
        "change_direction": direction,
        "signal_strength": abs(relative)
    }