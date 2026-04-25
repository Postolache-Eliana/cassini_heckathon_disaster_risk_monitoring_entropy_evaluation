def compute_risk(entropy_value):
    if entropy_value < 4:
        return "HIGH"
    elif entropy_value < 5:
        return "MEDIUM"
    else:
        return "LOW"