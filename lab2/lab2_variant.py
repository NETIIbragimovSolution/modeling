"""
Лабораторная работа №2.
Имитационная модель склада химикатов (Q-схема, принцип «особых состояний»).

Запуск:  python lab2_variant.py
"""

import random

import lab2_compute as compute
import lab2_io as io
import lab2_plotter as plotter


# Квантиль нормального распределения для α = 0.95
T_ALPHA = 1.96


# ---------------------------------------------------------------------------
# Verification: deterministic trace for two orders (checklist item 6)
# ---------------------------------------------------------------------------

def run_verification(params):
    """
    Replay the first two orders with a fixed seed so the result can be
    checked by hand against the block-diagram algorithm.

    Architecture matches lab2_compute.py:
    - Permission check (K1) is PARALLEL per order (non-blocking shared resource).
      Only new users wait gen_exponential(mean_perm_check).
    - Warehouse (K2a) is the sole shared bottleneck:
        priority orders wait for t_wh_current_end;
        non-priority orders wait for t_wh_queue_end.
    - External supplier (K2b) has no shared queue.
    """
    print("-" * 65)
    print("  Верификация: ручной прогон для первых двух заявок (seed=42)")
    print("-" * 65)

    random.seed(42)
    T_mod_saved = params["T_mod"]
    params["T_mod"] = 10000.0  # large enough for 2 orders; 1e18 would OOM the schedule

    t_arrival = 0.0
    t_wh_current_end = 0.0
    t_wh_queue_end = 0.0
    inventories, _, _ = compute.generate_inventory_schedule(params)

    order_num = 0
    while order_num < 2:
        t_arrival += compute.gen_exponential(params["mean_interarrival"])
        is_priority = random.random() < params["p_priority"]
        order_num += 1

        # --- K1: parallel permission check ---
        is_new_user = random.random() < params["p_new_user"]
        if is_new_user:
            dt_perm = compute.gen_exponential(params["mean_perm_check"])
        else:
            dt_perm = 0.0
        t_after_perm = t_arrival + dt_perm

        r = random.random()
        if r < params["p_no_permission"]:
            outcome = "ОТКАЗ (нет разрешения, r={:.4f})".format(r)
            _print_order_trace(order_num, t_arrival, None, dt_perm,
                               t_after_perm, is_priority, outcome, None, None)
            continue
        if r < params["p_no_permission"] + params["p_expired"]:
            outcome = "ОТКАЗ (просрочено, r={:.4f})".format(r)
            _print_order_trace(order_num, t_arrival, None, dt_perm,
                               t_after_perm, is_priority, outcome, None, None)
            continue

        path = "СКЛАД" if random.random() < params["p_warehouse"] else "ВНЕШНИЙ"

        if path == "СКЛАД":
            # priority jumps non-priority queue
            if is_priority:
                t_wh_start = max(t_after_perm, t_wh_current_end)
            else:
                t_wh_start = max(t_after_perm, t_wh_queue_end)
            t_wh_start = compute.adjust_for_inventory(t_wh_start, inventories)

            dt_wh = compute.gen_normal(params["mean_wh_prep"], params["std_wh_prep"])
            if dt_wh < 0.0:
                dt_wh = 0.0
            t_done = t_wh_start + dt_wh

            t_wh_current_end = t_done
            if t_done > t_wh_queue_end:
                t_wh_queue_end = t_done

            if random.random() < params["p_dangerous"]:
                if random.random() >= params["p_certificate"]:
                    outcome = "ОТКАЗ (нет сертификата)"
                    _print_order_trace(order_num, t_arrival, t_wh_start, dt_perm,
                                       t_after_perm, is_priority, outcome, path,
                                       t_done - t_arrival)
                    continue
        else:
            dt_place = compute.gen_normal(params["mean_ext_order"],
                                          params["std_ext_order"])
            if dt_place < 0.0:
                dt_place = 0.0
            t_current = t_after_perm + dt_place
            if random.random() < params["p_local"]:
                dt_del = compute.gen_exponential(params["mean_delivery_local"])
            else:
                dt_del = compute.gen_exponential(params["mean_delivery_nonlocal"])
            t_done = t_current + dt_del

        total_time = t_done - t_arrival
        if total_time > params["time_limit"]:
            outcome = "ОТКАЗ (лимит {:.1f}ч > {:.1f}ч)".format(
                total_time, params["time_limit"])
        else:
            outcome = "УСПЕХ"
        t_wh_start_show = (t_wh_start if path == "СКЛАД" else None)
        _print_order_trace(order_num, t_arrival, t_wh_start_show, dt_perm,
                           t_after_perm, is_priority, outcome, path, total_time)

    params["T_mod"] = T_mod_saved
    print()


def _print_order_trace(num, t_arr, t_wh_start, dt_perm, t_perm, priority,
                       outcome, path, total_time):
    print()
    print("  Заявка #{:d}{}".format(num, " [ПРИОРИТЕТ]" if priority else ""))
    print("    t_прихода         = {:.4f} ч".format(t_arr))
    print("    Δt_разрешение     = {:.4f} ч".format(dt_perm))
    print("    t_конец прав. пр. = {:.4f} ч".format(t_perm))
    if t_wh_start is not None:
        print("    t_начала склада   = {:.4f} ч".format(t_wh_start))
    if path is not None:
        print("    Путь выполнения   = {}".format(path))
    if total_time is not None:
        print("    Суммарное время   = {:.4f} ч".format(total_time))
    print("    Исход             = {}".format(outcome))


# ---------------------------------------------------------------------------
# Sensitivity experiment 1: vary mean_interarrival
# ---------------------------------------------------------------------------

def run_sensitivity_interarrival(params, n_runs):
    print("\n  Эксперимент 1: P_success и T_mean vs среднее время между заявками")
    io.print_sensitivity_header(
        "Анализ чувствительности — среднее время между заявками",
        "Интервал, ч",
    )
    values = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0]
    rows = compute.sensitivity_run(params, "mean_interarrival", values, n_runs)
    x_vals, p_vals, t_vals = [], [], []
    for v, p, t in rows:
        io.print_sensitivity_row(v, p, t)
        x_vals.append(v)
        p_vals.append(p)
        t_vals.append(t)
    io.print_sensitivity_footer()

    io.print_plot_notice()
    plotter.plot_sensitivity_combined(
        x_vals, p_vals, t_vals,
        "Среднее время между заявками, ч",
        "Эксперимент 1: влияние интенсивности потока заявок",
    )


# ---------------------------------------------------------------------------
# Sensitivity experiment 2: vary mean_perm_check
# ---------------------------------------------------------------------------

def run_sensitivity_perm(params, n_runs):
    print("  Эксперимент 2: P_success и T_mean vs среднее время проверки разрешения")
    io.print_sensitivity_header(
        "Анализ чувствительности — время проверки разрешения",
        "Пров., ч",
    )
    values = [4.0, 8.0, 12.0, 24.0, 48.0, 72.0, 96.0, 120.0, 144.0, 192.0, 240.0]
    rows = compute.sensitivity_run(params, "mean_perm_check", values, n_runs)
    x_vals, p_vals, t_vals = [], [], []
    for v, p, t in rows:
        io.print_sensitivity_row(v, p, t)
        x_vals.append(v)
        p_vals.append(p)
        t_vals.append(t)
    io.print_sensitivity_footer()

    io.print_plot_notice()
    plotter.plot_sensitivity_combined(
        x_vals, p_vals, t_vals,
        "Среднее время проверки разрешения, ч",
        "Эксперимент 2: влияние времени проверки разрешения",
    )


# ---------------------------------------------------------------------------
# Sensitivity experiment 3: vary time_limit
# ---------------------------------------------------------------------------

def run_sensitivity_time_limit(params, n_runs):
    print("  Эксперимент 3: P_success и T_mean vs лимит времени выполнения заказа")
    io.print_sensitivity_header(
        "Анализ чувствительности — лимит времени выполнения",
        "Лимит, ч",
    )
    values = [48.0, 72.0, 96.0, 120.0, 144.0, 168.0, 216.0, 240.0]
    rows = compute.sensitivity_run(params, "time_limit", values, n_runs)
    x_vals, p_vals, t_vals = [], [], []
    for v, p, t in rows:
        io.print_sensitivity_row(v, p, t)
        x_vals.append(v)
        p_vals.append(p)
        t_vals.append(t)
    io.print_sensitivity_footer()

    io.print_plot_notice()
    plotter.plot_sensitivity_combined(
        x_vals, p_vals, t_vals,
        "Лимит времени выполнения заказа, ч",
        "Эксперимент 3: влияние допустимого лимита времени",
    )


# ---------------------------------------------------------------------------
# Sensitivity experiment 4: vary mean_wh_prep
# ---------------------------------------------------------------------------

def run_sensitivity_wh_prep(params, n_runs):
    print("  Эксперимент 4: P_success и T_mean vs среднее время подготовки на складе")
    io.print_sensitivity_header(
        "Анализ чувствительности — время подготовки контейнера на складе",
        "Подгот., ч",
    )
    values = [1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 14.0, 18.0]
    rows = compute.sensitivity_run(params, "mean_wh_prep", values, n_runs)
    x_vals, p_vals, t_vals = [], [], []
    for v, p, t in rows:
        io.print_sensitivity_row(v, p, t)
        x_vals.append(v)
        p_vals.append(p)
        t_vals.append(t)
    io.print_sensitivity_footer()

    io.print_plot_notice()
    plotter.plot_sensitivity_combined(
        x_vals, p_vals, t_vals,
        "Среднее время подготовки контейнера, ч",
        "Эксперимент 4: влияние загруженности складского канала",
    )


# ---------------------------------------------------------------------------
# Sensitivity experiment 5: vary p_warehouse
# ---------------------------------------------------------------------------

def run_sensitivity_p_warehouse(params, n_runs):
    print("  Эксперимент 5: P_success и T_mean vs доля заказов через склад")
    io.print_sensitivity_header(
        "Анализ чувствительности — маршрутизация: склад vs внешний поставщик",
        "P(склад)",
    )
    values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    rows = compute.sensitivity_run(params, "p_warehouse", values, n_runs)
    x_vals, p_vals, t_vals = [], [], []
    for v, p, t in rows:
        io.print_sensitivity_row(v, p, t)
        x_vals.append(v)
        p_vals.append(p)
        t_vals.append(t)
    io.print_sensitivity_footer()

    io.print_plot_notice()
    plotter.plot_sensitivity_combined(
        x_vals, p_vals, t_vals,
        "Доля заказов через склад",
        "Эксперимент 5: влияние маршрутизации (склад vs внешний поставщик)",
    )


# ---------------------------------------------------------------------------
# Summary: P_success for all experiments on one figure
# ---------------------------------------------------------------------------

def _plot_sensitivity_summary(params, n_runs):
    """Сводный график: P_success для всех 5 экспериментов на одном рисунке."""
    experiments = [
        {
            "param": "mean_interarrival",
            "values": [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0],
            "xlabel": "Межзаявочный интервал, ч",
            "title": "Эксп. 1: интенсивность потока",
        },
        {
            "param": "mean_perm_check",
            "values": [12.0, 24.0, 48.0, 72.0, 96.0, 120.0, 144.0],
            "xlabel": "Время проверки разрешения, ч",
            "title": "Эксп. 2: проверка разрешения",
        },
        {
            "param": "time_limit",
            "values": [48.0, 72.0, 96.0, 120.0, 144.0, 168.0, 216.0, 240.0],
            "xlabel": "Лимит времени, ч",
            "title": "Эксп. 3: лимит времени",
        },
        {
            "param": "mean_wh_prep",
            "values": [1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 14.0, 18.0],
            "xlabel": "Подготовка на складе, ч",
            "title": "Эксп. 4: загруженность склада",
        },
        {
            "param": "p_warehouse",
            "values": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
            "xlabel": "Доля заказов через склад",
            "title": "Эксп. 5: маршрутизация",
        },
    ]
    plotter.plot_sensitivity_summary(params, experiments, compute.sensitivity_run, n_runs)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    io.print_intro()
    params = io.read_params()

    random.seed()  # use system entropy

    # --- statistical stability: determine N ---
    print("-" * 65)
    print("  Определение числа реализаций (точность ε = {:.2f})".format(
        params["epsilon"]))
    print("-" * 65)

    results = compute.determine_n_realizations(
        params,
        epsilon=params["epsilon"],
        t_alpha=T_ALPHA,
        n_init=params["N_init"],
        progress_cb=io.stability_progress,
    )

    io.print_stability_report(params["N_init"], results["n_final"],
                              params["epsilon"])
    io.print_main_results(results)

    # --- charts: rejection breakdown + completion time histogram ---
    io.print_plot_notice()
    plotter.plot_rejection_breakdown(results)
    plotter.plot_completion_time_hist(results["all_completion_times"])

    # --- normality check: P_success and T_mean across realizations ---
    io.print_plot_notice()
    plotter.plot_normality_histograms(results["p_list"], results["t_list"])

    # --- distribution check: histograms of actual simulated values vs PDF ---
    io.print_plot_notice()
    plotter.plot_distribution_checks(params, results["distribution_samples"])

    # --- temporal diagram (methodology style) ---
    io.print_plot_notice()
    plotter.plot_temporal_diagram()

    # --- verification trace ---
    run_verification(params)

    # --- sensitivity experiments ---
    n_sens = max(results["n_final"], 30)
    run_sensitivity_interarrival(params, n_sens)
    run_sensitivity_perm(params, n_sens)
    run_sensitivity_time_limit(params, n_sens)
    run_sensitivity_wh_prep(params, n_sens)
    run_sensitivity_p_warehouse(params, n_sens)

    # --- summary: P_success vs all parameters on one figure ---
    io.print_plot_notice()
    _plot_sensitivity_summary(params, n_sens)

    print("=" * 65)
    print("  Моделирование завершено.")
    print("=" * 65)


if __name__ == "__main__":
    main()
