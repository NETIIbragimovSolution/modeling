import math


def _normal_pdf(x, mean_a, sigma):
    if sigma <= 0.0:
        return 0.0
    z = (x - mean_a) / sigma
    c = 1.0 / (sigma * math.sqrt(2.0 * math.pi))
    return c * math.exp(-0.5 * z * z)


def _min_max(data):
    if len(data) == 0:
        return 0.0, 1.0
    lo = data[0]
    hi = data[0]
    i = 1
    while i < len(data):
        if data[i] < lo:
            lo = data[i]
        if data[i] > hi:
            hi = data[i]
        i += 1
    return lo, hi


def _theory_curve_x_y(sample1, sample2, mean_a, sigma, n_points):
    lo1, hi1 = _min_max(sample1)
    lo2, hi2 = _min_max(sample2)
    lo = lo1
    if lo2 < lo:
        lo = lo2
    hi = hi1
    if hi2 > hi:
        hi = hi2
    tail_lo = mean_a - 4.0 * sigma
    tail_hi = mean_a + 4.0 * sigma
    if tail_lo < lo:
        lo = tail_lo
    if tail_hi > hi:
        hi = tail_hi
    if hi <= lo:
        lo = mean_a - 4.0 * sigma
        hi = mean_a + 4.0 * sigma
    step = (hi - lo) / float(n_points - 1)
    xs = []
    ys = []
    i = 0
    while i < n_points:
        x = lo + i * step
        xs.append(x)
        ys.append(_normal_pdf(x, mean_a, sigma))
        i += 1
    return xs, ys


def plot_two_histograms(sample1, sample2, bins, title1, title2, mean_a=None, sigma=None):
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("\nMatplotlib не установлен. Графики не построены.")
        print("Установите: pip install matplotlib")
        return False

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # density=True: высота столбцов так, что площадь под гистограммой = 1
    # (как у теоретической плотности f(x); удобно сравнивать форму с нормальным законом)
    axes[0].hist(
        sample1,
        bins=bins,
        density=True,
        edgecolor="black",
        color="#4C78A8",
        alpha=0.8,
    )
    axes[0].set_title(title1)
    axes[0].set_xlabel("Значение")
    axes[0].set_ylabel("Плотность")
    axes[0].grid(True, alpha=0.3)

    axes[1].hist(
        sample2,
        bins=bins,
        density=True,
        edgecolor="black",
        color="#F58518",
        alpha=0.8,
    )
    axes[1].set_title(title2)
    axes[1].set_xlabel("Значение")
    axes[1].set_ylabel("Плотность")
    axes[1].grid(True, alpha=0.3)

    if mean_a is not None and sigma is not None and sigma > 0.0:
        xs, ys = _theory_curve_x_y(sample1, sample2, mean_a, sigma, 250)
        label = "Теория: N({0}, {1}^2)".format(mean_a, sigma)
        axes[0].plot(xs, ys, color="darkred", linewidth=2.0, label=label)
        axes[0].legend(loc="upper right", fontsize=8)
        axes[1].plot(xs, ys, color="darkred", linewidth=2.0, label=label)
        axes[1].legend(loc="upper right", fontsize=8)
        fig.suptitle(
            "Плотность выборки и теоретическая плотность N(a, σ^2) (п. 2.4.2)",
            fontsize=10,
            y=1.02,
        )

    fig.tight_layout()
    plt.show()
    return True
