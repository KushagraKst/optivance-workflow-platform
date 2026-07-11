def predict(values):
    """Simple linear regression prediction using pure Python (no numpy/sklearn needed)."""
    n = len(values)
    if n == 0:
        return 0
    if n == 1:
        return values[0]

    # X = [0, 1, 2, ..., n-1], y = values
    sum_x = sum(range(n))
    sum_y = sum(values)
    sum_xy = sum(i * v for i, v in enumerate(values))
    sum_x2 = sum(i * i for i in range(n))

    # slope (m) and intercept (b)
    denom = n * sum_x2 - sum_x * sum_x
    if denom == 0:
        return sum_y / n

    m = (n * sum_xy - sum_x * sum_y) / denom
    b = (sum_y - m * sum_x) / n

    # Predict next value at x = n
    return m * n + b