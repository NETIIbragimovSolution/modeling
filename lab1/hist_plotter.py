def plot_two_histograms(sample1, sample2, bins, title1, title2):
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

    fig.tight_layout()
    plt.show()
    return True
