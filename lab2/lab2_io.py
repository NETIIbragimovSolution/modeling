# Terminal input/output for Lab 2.
# All user-facing text is in Russian to match lab1 style.

# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def _read_float_gt0(prompt, default):
    while True:
        text = input(prompt).strip().replace(",", ".")
        if text == "":
            return default
        try:
            v = float(text)
            if v <= 0.0:
                print("  Ошибка: значение должно быть больше 0.")
                continue
            return v
        except ValueError:
            print("  Ошибка: введите число.")


def _read_prob(prompt, default):
    while True:
        text = input(prompt).strip().replace(",", ".")
        if text == "":
            return default
        try:
            v = float(text)
            if v < 0.0 or v > 1.0:
                print("  Ошибка: вероятность должна быть в [0, 1].")
                continue
            return v
        except ValueError:
            print("  Ошибка: введите число.")


def _read_int_gt0(prompt, default):
    while True:
        text = input(prompt).strip()
        if text == "":
            return default
        try:
            v = int(text)
            if v < 1:
                print("  Ошибка: значение должно быть >= 1.")
                continue
            return v
        except ValueError:
            print("  Ошибка: введите целое число.")


# ---------------------------------------------------------------------------
# Introduction
# ---------------------------------------------------------------------------

def print_intro():
    print()
    print("=" * 65)
    print("  Лабораторная работа №2")
    print("  Имитационная модель склада химикатов")
    print("  (принцип «особых состояний», Q-схема)")
    print("=" * 65)
    print()
    print("Объект моделирования: система обработки заявок на химикаты.")
    print("Показатели эффективности:")
    print("  P_success  — вероятность выполнения заявки")
    print("  T_mean     — среднее время выполнения заявки (ч)")
    print("  T_wait     — среднее время ожидания в очереди (ч)")
    print("  Разбивка отказов по причинам")
    print()


# ---------------------------------------------------------------------------
# Parameter input
# ---------------------------------------------------------------------------

def read_params():
    """Prompt user for all model parameters; empty input keeps the default."""
    print("-" * 65)
    print("  Параметры модели (Enter = значение по умолчанию)")
    print("-" * 65)

    print("\n[Время моделирования]")
    T_mod = _read_float_gt0(
        "  Горизонт моделирования, ч [2160 = 1 квартал]: ", 2160.0
    )

    print("\n[Входной поток заявок]")
    mean_interarrival = _read_float_gt0(
        "  Среднее время между заявками, ч [1.5]: ", 1.5
    )
    p_priority = _read_prob(
        "  Доля приоритетных заявок [0.01]: ", 0.01
    )

    print("\n[Проверка разрешения — K1]")
    p_new_user = _read_prob(
        "  Доля новых пользователей (требуют полной проверки) [1.0]: ", 1.0
    )
    mean_perm_check = _read_float_gt0(
        "  Среднее время проверки, ч [48 = 2 дня]: ", 48.0
    )
    p_no_permission = _read_prob(
        "  Вероятность отсутствия разрешения [0.2]: ", 0.2
    )
    p_expired = _read_prob(
        "  Вероятность просроченного разрешения [0.3]: ", 0.3
    )
    while p_no_permission + p_expired > 1.0:
        print("  Ошибка: сумма вероятностей отказов > 1. Введите заново.")
        p_no_permission = _read_prob(
            "  Вероятность отсутствия разрешения [0.2]: ", 0.2
        )
        p_expired = _read_prob(
            "  Вероятность просроченного разрешения [0.3]: ", 0.3
        )

    print("\n[Путь выполнения заказа]")
    p_warehouse = _read_prob(
        "  Вероятность выполнения через склад (иначе — внешний поставщик) [0.5]: ",
        0.5,
    )

    print("\n[Канал склада — K2a]")
    mean_wh_prep = _read_float_gt0(
        "  Среднее время подготовки контейнера, ч [4.0]: ", 4.0
    )
    std_wh_prep = _read_float_gt0(
        "  СКО времени подготовки, ч [2.0]: ", 2.0
    )
    p_dangerous = _read_prob(
        "  Доля опасных химикатов [0.5]: ", 0.5
    )
    p_certificate = _read_prob(
        "  Вероятность наличия сертификата у пользователя [0.7]: ", 0.7
    )

    print("\n[Канал внешнего поставщика — K2b]")
    mean_ext_order = _read_float_gt0(
        "  Среднее время размещения заказа, ч [1.5]: ", 1.5
    )
    std_ext_order = _read_float_gt0(
        "  СКО времени размещения, ч [0.2]: ", 0.2
    )
    p_local = _read_prob(
        "  Доля местных поставщиков [0.5]: ", 0.5
    )
    mean_delivery_local = _read_float_gt0(
        "  Среднее время доставки (местный), ч [72 = 3 дня]: ", 72.0
    )
    mean_delivery_nonlocal = _read_float_gt0(
        "  Среднее время доставки (иногородний), ч [144 = 6 дней]: ", 144.0
    )

    print("\n[Инвентаризация — L]")
    inv_period_min = _read_float_gt0(
        "  Мин. период между инвентаризациями, ч [120 = 5 дн]: ", 120.0
    )
    inv_period_max = _read_float_gt0(
        "  Макс. период между инвентаризациями, ч [216 = 9 дн]: ", 216.0
    )
    inv_duration_min = _read_float_gt0(
        "  Мин. длительность инвентаризации, ч [3]: ", 3.0
    )
    inv_duration_max = _read_float_gt0(
        "  Макс. длительность инвентаризации, ч [7]: ", 7.0
    )

    print("\n[Ограничение по времени]")
    time_limit = _read_float_gt0(
        "  Максимальное допустимое время выполнения заявки, ч [120 = 5 дн]: ",
        120.0,
    )

    print("\n[Параметры расчёта]")
    N_init = _read_int_gt0(
        "  Начальное число реализаций [50]: ", 50
    )
    epsilon = _read_prob(
        "  Точность расчёта ε [0.1]: ", 0.1
    )

    print()

    return {
        "T_mod": T_mod,
        "mean_interarrival": mean_interarrival,
        "p_priority": p_priority,
        "p_new_user": p_new_user,
        "mean_perm_check": mean_perm_check,
        "p_no_permission": p_no_permission,
        "p_expired": p_expired,
        "p_warehouse": p_warehouse,
        "mean_wh_prep": mean_wh_prep,
        "std_wh_prep": std_wh_prep,
        "p_dangerous": p_dangerous,
        "p_certificate": p_certificate,
        "mean_ext_order": mean_ext_order,
        "std_ext_order": std_ext_order,
        "p_local": p_local,
        "mean_delivery_local": mean_delivery_local,
        "mean_delivery_nonlocal": mean_delivery_nonlocal,
        "inv_period_min": inv_period_min,
        "inv_period_max": inv_period_max,
        "inv_duration_min": inv_duration_min,
        "inv_duration_max": inv_duration_max,
        "time_limit": time_limit,
        "N_init": N_init,
        "epsilon": epsilon,
    }


# ---------------------------------------------------------------------------
# Stability progress callback
# ---------------------------------------------------------------------------

def stability_progress(stage, n_cur, n_star, p_mean, p_var):
    print(
        "  Этап {:d}: N={:d}  →  N*={:d}   "
        "P_success={:.4f}  σ²={:.6f}".format(
            stage, n_cur, n_star, p_mean, p_var
        )
    )


# ---------------------------------------------------------------------------
# Results output
# ---------------------------------------------------------------------------

def print_main_results(results):
    n_runs = results["n_final"]
    p = results["p_mean"]
    t = results["t_mean"]
    w = results["wait_mean"]
    N = results["agg_N_total"]
    Ns = results["agg_N_success"]
    r_np = results["agg_N_rej_noperm"]
    r_ex = results["agg_N_rej_expired"]
    r_ce = results["agg_N_rej_cert"]
    r_tl = results["agg_N_rej_time"]

    print()
    print("=" * 65)
    print("  РЕЗУЛЬТАТЫ МОДЕЛИРОВАНИЯ")
    print("=" * 65)
    print("  Число реализаций (финальное):    {:d}".format(n_runs))
    print("  Всего заявок (суммарно):         {:d}".format(N))
    print("  Выполнено успешно:               {:d}".format(Ns))
    total_rej = r_np + r_ex + r_ce + r_tl
    print("  Отказов всего:                   {:d}".format(total_rej))
    print()
    print("  Показатели эффективности:")
    print("    P_success (вер. выполнения):   {:.4f}".format(p))
    print("    T_mean    (ср. время вып., ч): {:.2f}".format(t))
    print("    T_wait    (ср. время ожид., ч):{:.2f}".format(w))
    print()
    print("  Причины отказов:")
    print("    Нет разрешения:                {:d}".format(r_np))
    print("    Просроченное разрешение:       {:d}".format(r_ex))
    print("    Нет сертификата (опасн. хим.): {:d}".format(r_ce))
    print("    Превышен лимит времени (5 дн): {:d}".format(r_tl))
    print("=" * 65)
    print()


def print_stability_report(N_init, N_final, epsilon):
    print("-" * 65)
    print("  Статистическая устойчивость")
    print("    Начальное N:  {:d}".format(N_init))
    print("    Финальное N:  {:d}".format(N_final))
    print("    Точность ε:   {:.2f}".format(epsilon))
    if N_final <= N_init:
        print("    → Начального числа реализаций оказалось достаточно.")
    else:
        print("    → Число реализаций было увеличено для обеспечения точности.")
    print("-" * 65)
    print()


# ---------------------------------------------------------------------------
# Sensitivity table output
# ---------------------------------------------------------------------------

def print_sensitivity_header(title, param_label):
    print()
    print("-" * 65)
    print("  " + title)
    print("-" * 65)
    print("  {:>12s}  {:>12s}  {:>14s}".format(param_label, "P_success", "T_mean, ч"))
    print("  " + "-" * 42)


def print_sensitivity_row(value, p_success, t_mean):
    print("  {:>12.2f}  {:>12.4f}  {:>14.2f}".format(value, p_success, t_mean))


def print_sensitivity_footer():
    print("  " + "-" * 42)
    print()


def print_plot_notice():
    print("  [Открывается окно с графиками matplotlib...]")
    print()
