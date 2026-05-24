"""Matplotlib visualisation for Lab 2."""

import math


def _try_import():
    try:
        import matplotlib.pyplot as plt
        return plt
    except Exception:
        print("\nMatplotlib не установлен. Графики не построены.")
        print("Установите: pip install matplotlib")
        return None


# ---------------------------------------------------------------------------
# Distribution check: histograms vs theoretical PDFs
# ---------------------------------------------------------------------------

def _pdf_exponential(x, mean):
    if x < 0:
        return 0.0
    lam = 1.0 / mean
    return lam * math.exp(-lam * x)


def _pdf_normal(x, mean, std):
    z = (x - mean) / std
    return math.exp(-0.5 * z * z) / (std * math.sqrt(2.0 * math.pi))


def _pdf_uniform(x, lo, hi):
    if lo <= x <= hi:
        return 1.0 / (hi - lo)
    return 0.0


def _linspace(lo, hi, n):
    step = (hi - lo) / (n - 1)
    result = []
    i = 0
    while i < n:
        result.append(lo + i * step)
        i += 1
    return result


def plot_distribution_checks(params, distribution_samples):
    """
    Для каждого стохастического параметра: гистограмма фактических значений
    из симуляции + теоретическая PDF.
    """
    plt = _try_import()
    if plt is None:
        return False

    ds = distribution_samples
    specs = [
        {
            "title": "Exp: межзаявочный интервал\n(mean={:.1f} ч)".format(
                params["mean_interarrival"]),
            "samples": ds["interarrival_times"],
            "pdf": lambda x, m=params["mean_interarrival"]: _pdf_exponential(x, m),
            "color": "#4C78A8",
        },
        {
            "title": "Exp: время проверки разрешения\n(mean={:.1f} ч)".format(
                params["mean_perm_check"]),
            "samples": ds["perm_check_times"],
            "pdf": lambda x, m=params["mean_perm_check"]: _pdf_exponential(x, m),
            "color": "#4C78A8",
        },
        {
            "title": "Exp: доставка местный\n(mean={:.1f} ч)".format(
                params["mean_delivery_local"]),
            "samples": ds["delivery_local_times"],
            "pdf": lambda x, m=params["mean_delivery_local"]: _pdf_exponential(x, m),
            "color": "#4C78A8",
        },
        {
            "title": "Exp: доставка иногородний\n(mean={:.1f} ч)".format(
                params["mean_delivery_nonlocal"]),
            "samples": ds["delivery_nonlocal_times"],
            "pdf": lambda x, m=params["mean_delivery_nonlocal"]: _pdf_exponential(x, m),
            "color": "#4C78A8",
        },
        {
            "title": "N: время подготовки склада\n(μ={:.1f}, σ={:.1f} ч)".format(
                params["mean_wh_prep"], params["std_wh_prep"]),
            "samples": ds["wh_prep_times"],
            "pdf": lambda x, mu=params["mean_wh_prep"], s=params["std_wh_prep"]:
                       _pdf_normal(x, mu, s),
            "color": "#54A24B",
        },
        {
            "title": "N: время размещения заказа\n(μ={:.1f}, σ={:.1f} ч)".format(
                params["mean_ext_order"], params["std_ext_order"]),
            "samples": ds["ext_order_times"],
            "pdf": lambda x, mu=params["mean_ext_order"], s=params["std_ext_order"]:
                       _pdf_normal(x, mu, s),
            "color": "#54A24B",
        },
        {
            "title": "U: период инвентаризации\n([{:.0f}, {:.0f}] ч)".format(
                params["inv_period_min"], params["inv_period_max"]),
            "samples": ds["inv_periods"],
            "pdf": lambda x, lo=params["inv_period_min"], hi=params["inv_period_max"]:
                       _pdf_uniform(x, lo, hi),
            "color": "#F58518",
        },
        {
            "title": "U: длительность инвентаризации\n([{:.0f}, {:.0f}] ч)".format(
                params["inv_duration_min"], params["inv_duration_max"]),
            "samples": ds["inv_durations"],
            "pdf": lambda x, lo=params["inv_duration_min"], hi=params["inv_duration_max"]:
                       _pdf_uniform(x, lo, hi),
            "color": "#F58518",
        },
    ]

    total_samples = sum(len(s["samples"]) for s in specs)
    fig, axes = plt.subplots(4, 2, figsize=(13, 16))
    fig.suptitle(
        "Проверка генераторов: гистограммы фактических значений из симуляции vs PDF\n"
        "(всего {:,} значений по всем законам)".format(total_samples),
        fontsize=13,
        fontweight="bold",
    )

    for idx, spec in enumerate(specs):
        ax = axes[idx // 2][idx % 2]
        samples = spec["samples"]

        s_min = min(samples)
        s_max = max(samples)

        # histogram normalized to density
        ax.hist(samples, bins=40, density=True,
                color=spec["color"], alpha=0.7, edgecolor="white",
                linewidth=0.4, label="выборка")

        # theoretical PDF
        margin = (s_max - s_min) * 0.05
        x_lo = max(s_min - margin, 0.0) if "Exp" in spec["title"] else s_min - margin
        x_hi = s_max + margin
        xs = _linspace(x_lo, x_hi, 300)
        ys = [spec["pdf"](x) for x in xs]
        ax.plot(xs, ys, color="#E45756", linewidth=2.0, label="теор. PDF")

        ax.set_title(spec["title"], fontsize=9)
        ax.set_xlabel("значение")
        ax.set_ylabel("плотность")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()
    return True


# ---------------------------------------------------------------------------
# Summary sensitivity: P_success and T_mean for all experiments (3-column grid)
# ---------------------------------------------------------------------------

def plot_sensitivity_summary(params, experiments, sensitivity_run_fn, n_runs):
    """
    Сводный рисунок: все эксперименты в одной сетке.
    Верхний ряд — P_success, нижний — T_mean.
    """
    plt = _try_import()
    if plt is None:
        return False

    n = len(experiments)
    ncols = 3
    nrows_p = (n + ncols - 1) // ncols  # rows for P
    fig_p, axes_p = plt.subplots(nrows_p, ncols, figsize=(15, 4 * nrows_p))
    fig_p.suptitle(
        "Сводный анализ чувствительности — вероятность выполнения P_success",
        fontsize=13, fontweight="bold",
    )

    fig_t, axes_t = plt.subplots(nrows_p, ncols, figsize=(15, 4 * nrows_p))
    fig_t.suptitle(
        "Сводный анализ чувствительности — среднее время выполнения T_mean, ч",
        fontsize=13, fontweight="bold",
    )

    axes_p_flat = [axes_p] if nrows_p == 1 and ncols == 1 else \
                  (list(axes_p) if nrows_p == 1 else
                   [ax for row in axes_p for ax in row])
    axes_t_flat = [axes_t] if nrows_p == 1 and ncols == 1 else \
                  (list(axes_t) if nrows_p == 1 else
                   [ax for row in axes_t for ax in row])

    colors_p = ["#4C78A8", "#54A24B", "#F58518", "#E45756", "#B279A2"]
    colors_t = ["#72B7B2", "#EECA3B", "#FF9DA6", "#9D755D", "#BAB0AC"]

    for idx, exp in enumerate(experiments):
        rows = sensitivity_run_fn(params, exp["param"], exp["values"], n_runs)
        x_vals = [r[0] for r in rows]
        p_vals = [r[1] for r in rows]
        t_vals = [r[2] for r in rows]

        ax_p = axes_p_flat[idx]
        ax_p.plot(x_vals, p_vals, marker="o", color=colors_p[idx % len(colors_p)],
                  linewidth=2.0, markersize=6)
        ax_p.set_title(exp["title"], fontsize=10)
        ax_p.set_xlabel(exp["xlabel"], fontsize=8)
        ax_p.set_ylabel("P_success", fontsize=8)
        ax_p.set_ylim(0.0, 1.05)
        ax_p.axhline(y=0.5, color="gray", linewidth=0.8, linestyle="--", alpha=0.6)
        ax_p.grid(True, alpha=0.3)

        ax_t = axes_t_flat[idx]
        ax_t.plot(x_vals, t_vals, marker="s", color=colors_t[idx % len(colors_t)],
                  linewidth=2.0, markersize=6)
        ax_t.set_title(exp["title"], fontsize=10)
        ax_t.set_xlabel(exp["xlabel"], fontsize=8)
        ax_t.set_ylabel("T_mean, ч", fontsize=8)
        ax_t.grid(True, alpha=0.3)

    # hide unused subplots
    for i in range(len(experiments), len(axes_p_flat)):
        axes_p_flat[i].set_visible(False)
        axes_t_flat[i].set_visible(False)

    fig_p.tight_layout(rect=[0, 0, 1, 0.95])
    fig_t.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()
    return True


# ---------------------------------------------------------------------------
# Chart 1 — rejection breakdown (stacked bar)
# ---------------------------------------------------------------------------

def plot_rejection_breakdown(results):
    plt = _try_import()
    if plt is None:
        return False

    labels = [
        "Нет\nразрешения",
        "Просрочено\nразрешение",
        "Нет\nсертификата",
        "Превышен\nлимит (5 дн)",
        "Успешно\nвыполнены",
    ]
    values = [
        results["agg_N_rej_noperm"],
        results["agg_N_rej_expired"],
        results["agg_N_rej_cert"],
        results["agg_N_rej_time"],
        results["agg_N_success"],
    ]
    colors = ["#E45756", "#F58518", "#EECA3B", "#72B7B2", "#54A24B"]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(labels, values, color=colors, edgecolor="black", linewidth=0.6)

    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + max(values) * 0.01,
                str(val),
                ha="center",
                va="bottom",
                fontsize=9,
            )

    ax.set_title("Распределение заявок по исходам (суммарно по всем реализациям)")
    ax.set_ylabel("Количество заявок")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    plt.show()
    return True


# ---------------------------------------------------------------------------
# Chart 2 — completion time histogram
# ---------------------------------------------------------------------------

def plot_completion_time_hist(completion_times, n_bins=20):
    plt = _try_import()
    if plt is None:
        return False
    if len(completion_times) == 0:
        print("  Нет успешных заявок для построения гистограммы.")
        return False

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(
        completion_times,
        bins=n_bins,
        color="#4C78A8",
        edgecolor="black",
        alpha=0.85,
    )
    ax.set_title("Гистограмма времени выполнения успешных заявок")
    ax.set_xlabel("Время выполнения, ч")
    ax.set_ylabel("Число заявок")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    plt.show()
    return True


# ---------------------------------------------------------------------------
# Chart 3 — sensitivity: P_success vs parameter
# ---------------------------------------------------------------------------

def plot_sensitivity_p_success(x_vals, p_vals, x_label, title):
    plt = _try_import()
    if plt is None:
        return False

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x_vals, p_vals, marker="o", color="#4C78A8", linewidth=2.0,
            markersize=6)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel("P_success (вероятность выполнения)")
    ax.set_ylim(0.0, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    plt.show()
    return True


# ---------------------------------------------------------------------------
# Chart 4 — sensitivity: T_mean vs parameter
# ---------------------------------------------------------------------------

def plot_sensitivity_t_mean(x_vals, t_vals, x_label, title):
    plt = _try_import()
    if plt is None:
        return False

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x_vals, t_vals, marker="s", color="#F58518", linewidth=2.0,
            markersize=6)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel("T_mean, ч (среднее время выполнения)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    plt.show()
    return True


# ---------------------------------------------------------------------------
# Chart 5 — normality check: histograms of p_list and t_list with normal PDF
# ---------------------------------------------------------------------------

def plot_normality_histograms(p_list, t_list):
    """
    Two-panel figure: histograms of per-realization P_success and T_mean
    with a fitted normal PDF overlay — visually confirms CLT convergence.
    """
    plt = _try_import()
    if plt is None:
        return False

    def _normal_pdf(x, mu, sigma):
        return (1.0 / (sigma * math.sqrt(2.0 * math.pi))) * math.exp(
            -0.5 * ((x - mu) / sigma) ** 2
        )

    def _stats(data):
        n = len(data)
        if n < 2:
            return 0.0, 1.0
        mu = sum(data) / n
        var = sum((v - mu) ** 2 for v in data) / (n - 1)
        return mu, math.sqrt(var) if var > 0 else 1e-9

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(
        "Проверка нормальности показателей эффективности\n"
        "(гистограммы по реализациям + теоретическая кривая нормального закона)",
        fontsize=12,
    )

    for ax, data, title, xlabel, color in [
        (ax1, p_list, "P_success по реализациям", "P_success", "#4C78A8"),
        (ax2, t_list, "T_mean по реализациям, ч",  "T_mean, ч",  "#F58518"),
    ]:
        n_bins = max(8, len(data) // 5)
        ax.hist(
            data, bins=n_bins, color=color, edgecolor="black",
            alpha=0.7, density=True, label="Эмпирическая\nгистограмма",
        )

        mu, sigma = _stats(data)

        lo = min(data) - 3 * sigma
        hi = max(data) + 3 * sigma
        n_pts = 300
        step = (hi - lo) / n_pts
        xs = [lo + i * step for i in range(n_pts + 1)]
        ys = [_normal_pdf(x, mu, sigma) for x in xs]

        ax.plot(xs, ys, color="crimson", linewidth=2.0,
                label="N(μ={:.4f},\nσ={:.4f})".format(mu, sigma))
        ax.axvline(mu, color="crimson", linestyle="--", linewidth=1.2, alpha=0.7)

        ax.set_title(title, fontsize=11)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Плотность")
        ax.legend(fontsize=9)
        ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    plt.show()
    return True


# ---------------------------------------------------------------------------
# Chart 6 — combined sensitivity on one figure (two y-axes)
# ---------------------------------------------------------------------------

def plot_sensitivity_combined(x_vals, p_vals, t_vals, x_label, title):
    plt = _try_import()
    if plt is None:
        return False

    fig, ax1 = plt.subplots(figsize=(9, 5))

    color1 = "#4C78A8"
    color2 = "#F58518"

    ax1.plot(x_vals, p_vals, marker="o", color=color1, linewidth=2.0,
             markersize=6, label="P_success")
    ax1.set_xlabel(x_label)
    ax1.set_ylabel("P_success", color=color1)
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.set_ylim(0.0, 1.05)

    ax2 = ax1.twinx()
    ax2.plot(x_vals, t_vals, marker="s", color=color2, linewidth=2.0,
             markersize=6, linestyle="--", label="T_mean")
    ax2.set_ylabel("T_mean, ч", color=color2)
    ax2.tick_params(axis="y", labelcolor=color2)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    ax1.set_title(title)
    ax1.grid(True, alpha=0.3)
    fig.tight_layout()
    plt.show()
    return True


# ---------------------------------------------------------------------------
# Chart 7 — temporal diagram (methodology style)
# ---------------------------------------------------------------------------

def plot_temporal_diagram():
    """
    Temporal diagram matching the methodology example:
    - Top: time axis with state boxes (I=X C=X) at each event
    - Bottom: coloured channel bars (K1, K2, K3) with labelled segments
    """
    plt = _try_import()
    if plt is None:
        return False
    import matplotlib.patches as mpatches

    T_END = 36.0
    TOP_Y = 6.0
    BOX_W, BOX_H = 2.8, 1.2

    ROWS = {
        "K1": (3.2, 0.7),
        "K2": (1.8, 0.7),
        "K3": (0.4, 0.7),
    }

    COLORS = {
        "idle":     "#d0d0e8",
        "k1_check": "#6baed6",
        "k2_serve": "#74c476",
        "k3_place": "#fd8d3c",
        "k3_deliv": "#fdae6b",
    }

    events = [
        (0,  0, 0),
        (10, 1, 1),
        (15, 2, 2),
        (18, 1, 1),
        (25, 0, 0),
        (30, 1, 1),
    ]

    k1_segs = [
        (0,   2,    "idle"),
        (2,   17,   "k1_check"),
        (17,  22,   "idle"),
        (22,  30,   "k1_check"),
        (30,  T_END,"idle"),
    ]
    k2_segs = [
        (0,   10,   "idle"),
        (10,  18,   "k2_serve"),
        (18,  25,   "k2_serve"),
        (25,  30,   "idle"),
        (30,  35,   "k2_serve"),
        (35,  T_END,"idle"),
    ]
    k3_segs = [
        (0,   17,   "idle"),
        (17,  19,   "k3_place"),
        (19,  27,   "k3_deliv"),
        (27,  T_END,"idle"),
    ]

    k2_labels = [
        (5,    "Простой\nΔt_пр",     0.0),
        (14,   "Обсл. З1\nΔt_обсл", -1.6),
        (21.5, "Обсл. З2\nΔt_обсл",  0.0),
        (27.5, "Простой\nΔt_пр",    -1.6),
        (32.5, "Обсл. З3\nΔt_обсл",  0.0),
    ]

    fig, ax = plt.subplots(figsize=(17, 9))
    ax.set_xlim(-4, T_END + 2)
    ax.set_ylim(-5.5, 7.5)
    ax.axis("off")
    fig.suptitle("Временная диаграмма имитационной модели склада химикатов",
                 fontsize=12, fontweight="bold")

    ax.annotate("", xy=(T_END + 1.5, TOP_Y), xytext=(-3.5, TOP_Y),
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
    ax.text(T_END + 1.7, TOP_Y, "t", ha="left", va="center", fontsize=11)
    ax.text(-4, TOP_Y + 1.8, "Начало\nработы, t=0",
            ha="center", va="bottom", fontsize=8)
    ax.plot([0, 0], [TOP_Y + 1.4, TOP_Y], "k-", lw=1)

    row_labels = {
        "K1": "Ось времени\nканала К1",
        "K2": "Ось времени\nканала К2",
        "K3": "Ось времени\nканала К3",
    }
    for name, (ch_y, ch_h) in ROWS.items():
        ax.text(-0.3, ch_y + ch_h / 2, row_labels[name],
                ha="right", va="center", fontsize=8.5,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black"))

    ax.text(-0.3, TOP_Y, "Ось времени\nвходного потока",
            ha="right", va="center", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black"))

    ch3_y, ch3_h = ROWS["K3"]
    for t, I, C in events:
        ax.plot([t, t], [TOP_Y - BOX_H / 2, ch3_y + ch3_h], "k--", lw=0.8)
        ax.annotate("", xy=(t, TOP_Y + 0.4), xytext=(t, TOP_Y + 1.0),
                    arrowprops=dict(arrowstyle="->", color="black", lw=1))
        rect = mpatches.Rectangle(
            (t - BOX_W / 2, TOP_Y - BOX_H / 2), BOX_W, BOX_H,
            linewidth=1.2, edgecolor="black", facecolor="white", zorder=3)
        ax.add_patch(rect)
        ax.text(t, TOP_Y, "I={}\nC={}".format(I, C),
                ha="center", va="center", fontsize=9,
                fontfamily="monospace", zorder=4)

    def _draw_bar(segs, row_key):
        ch_y, ch_h = ROWS[row_key]
        for ts, te, ckey in segs:
            rect = mpatches.Rectangle(
                (ts, ch_y), te - ts, ch_h,
                facecolor=COLORS[ckey], edgecolor="black", linewidth=0.9)
            ax.add_patch(rect)

    _draw_bar(k1_segs, "K1")
    _draw_bar(k2_segs, "K2")
    _draw_bar(k3_segs, "K3")

    ch2_y, _ = ROWS["K2"]
    for tc, lbl, extra_y in k2_labels:
        ax.annotate(
            lbl,
            xy=(tc, ch2_y),
            xytext=(tc, -0.4 + extra_y),
            ha="center", va="top", fontsize=8,
            arrowprops=dict(arrowstyle="->", color="black", lw=0.9),
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black"),
            zorder=5)

    ch2_y, ch2_h = ROWS["K2"]
    ax.annotate(
        "З2 ждёт\nв очереди",
        xy=(16.5, ch2_y + ch2_h + 0.05),
        xytext=(16.5, ch2_y + ch2_h + 1.1),
        ha="center", va="bottom", fontsize=7.5, color="#636363",
        arrowprops=dict(arrowstyle="->", color="#636363", lw=0.8),
        bbox=dict(boxstyle="round,pad=0.2", fc="#fff8e1", ec="#636363"),
        zorder=5)
    ax.annotate("", xy=(18, ch2_y + ch2_h + 0.65),
                xytext=(15, ch2_y + ch2_h + 0.65),
                arrowprops=dict(arrowstyle="<->", color="#636363", lw=1.0))

    legend_patches = [
        mpatches.Patch(facecolor=COLORS["idle"],     edgecolor="black", label="Простой"),
        mpatches.Patch(facecolor=COLORS["k1_check"], edgecolor="black", label="К1: проверка разрешения"),
        mpatches.Patch(facecolor=COLORS["k2_serve"], edgecolor="black", label="К2: подготовка склада"),
        mpatches.Patch(facecolor=COLORS["k3_place"], edgecolor="black", label="К3: размещение заказа"),
        mpatches.Patch(facecolor=COLORS["k3_deliv"], edgecolor="black", label="К3: ожидание доставки"),
    ]
    ax.legend(handles=legend_patches, loc="lower right",
              fontsize=8, framealpha=0.95, edgecolor="black")

    fig.tight_layout()
    plt.show()
    return True
