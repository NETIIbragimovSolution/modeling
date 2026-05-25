try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False

_C_BLUE   = "#4C78A8"
_C_ORANGE = "#F58518"
_C_GREEN  = "#54A24B"
_C_RED    = "#E45756"
_C_PURPLE = "#B279A2"


def _ax_style(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=12)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)


def plot_all(results, params):
    if not _HAS_MPL:
        print("  matplotlib не установлен — графики недоступны.")
        return

    ts   = results["t"]
    Zcs  = results["Zc"]
    Y0As = results["y0A"]
    Y0Bs = results["y0B"]
    Y11s = results["y11"]
    Y21s = results["y21"]
    Y12s = results["y12"]
    Y22s = results["y22"]
    YCAs = results["yCA"]
    YCBs = results["yCB"]

    y0A_init = results["y0A_init"]
    y0B_init = results["y0B_init"]
    crit_A   = 0.2 * y0A_init
    crit_B   = 0.2 * y0B_init

    # --- Figure 1: Finished product output ---
    fig1, ax1 = plt.subplots(figsize=(9, 4))
    ax1.plot(ts, Zcs, color=_C_BLUE, linewidth=1.5, label="Zc(t) — выпуск изделий")
    _ax_style(ax1, "Выпуск готовой продукции Zc(t)", "Время t", "Zc")
    fig1.tight_layout()

    # --- Figure 2: Warehouse levels ---
    fig2, ax2 = plt.subplots(figsize=(9, 4))
    ax2.plot(ts, Y0As, color=_C_BLUE,   linewidth=1.5, label="y0A — склад A")
    ax2.plot(ts, Y0Bs, color=_C_ORANGE, linewidth=1.5, label="y0B — склад B")
    ax2.axhline(crit_A, color=_C_BLUE,   linestyle="--", linewidth=0.9, alpha=0.7,
                label=f"Критич. уровень A ({crit_A:.0f})")
    ax2.axhline(crit_B, color=_C_ORANGE, linestyle="--", linewidth=0.9, alpha=0.7,
                label=f"Критич. уровень B ({crit_B:.0f})")

    events = results["replenish_events"]
    i = 0
    labeled_A = False
    labeled_B = False
    while i < len(events):
        ev = events[i]
        if ev[1] == "A":
            lbl = "Пополнение A" if not labeled_A else None
            ax2.axvline(ev[0], color=_C_BLUE, linestyle=":", linewidth=0.8, alpha=0.5, label=lbl)
            labeled_A = True
        else:
            lbl = "Пополнение B" if not labeled_B else None
            ax2.axvline(ev[0], color=_C_ORANGE, linestyle=":", linewidth=0.8, alpha=0.5, label=lbl)
            labeled_B = True
        i += 1

    _ax_style(ax2, "Уровни складов сырья y0A(t), y0B(t)", "Время t", "Уровень")
    fig2.tight_layout()

    # --- Figure 3: Processing levels ---
    fig3, ax3 = plt.subplots(figsize=(9, 4))
    ax3.plot(ts, Y11s, color=_C_BLUE,   linewidth=1.5, label="y11 — звено 11 (лин. A)")
    ax3.plot(ts, Y21s, color=_C_ORANGE, linewidth=1.5, label="y21 — звено 21 (лин. B, ст. 1)")
    ax3.plot(ts, Y12s, color=_C_GREEN,  linewidth=1.5, label="y12 — звено B2 (лин. B, ст. 2)")
    ax3.plot(ts, Y22s, color=_C_RED,    linewidth=1.5, label="y22 — звено B3 (лин. B, ст. 3)")
    _ax_style(ax3, "Уровни обрабатывающих звеньев yij(t)", "Время t", "Уровень")
    fig3.tight_layout()

    # --- Figure 4: Assembly stocks ---
    fig4, ax4 = plt.subplots(figsize=(9, 4))
    ax4.plot(ts, YCAs, color=_C_BLUE,   linewidth=1.5, label="yCА — детали A на сборке")
    ax4.plot(ts, YCBs, color=_C_ORANGE, linewidth=1.5, label="yCВ — детали B на сборке")
    _ax_style(ax4, "Запасы деталей на узле сборки yCА(t), yCВ(t)", "Время t", "Количество деталей")
    fig4.tight_layout()

    plt.show()
