"""
Лабораторная работа №2 — упрощённая верификация имитационной модели.

Цель — чтобы ручной расчёт «по карандашу» с параметрами по умолчанию
примерно совпадал с тем, что выводит программа. Для этого из модели
убран весь «большой ±» — каждый датчик заменён на свою центральную
точку (вместо случайного значения):

    gen_exponential(μ)  →  μ · ln 2     (медиана; U=0.5 в формуле -μ·ln(1-U))
    gen_normal(μ, σ)    →  μ            (без ±σ)
    gen_uniform(lo, hi) →  (lo + hi)/2  (середина диапазона)

Случайным остаётся только выбор веток ветвлений (есть/нет разрешение,
склад/внешний поставщик, местный/иногородний и т.п.) — с фиксированным
зерном random.seed(SEED), поэтому каждый запуск даёт одинаковую
последовательность ветвлений, но трасса при этом «живая», без жёстко
прописанных U.

На этих параметрах модель естественным образом проходит по всем 4
каноническим сценариям ручной диаграммы:
    1) Отказ по K1 — нет разрешения / просрочено
    2) Успех — путь через склад (K2)
    3) Успех — внешний поставщик, местный (K3)
    4) Отказ по лимиту — внешний поставщик, иногородний

Запуск:  python3 lab2_verify.py
"""

import math
import random

import lab2_compute as compute


# ---------------------------------------------------------------------------
# Параметры по умолчанию (как в lab2_io.read_params)
# ---------------------------------------------------------------------------

DEFAULT_PARAMS = {
    "T_mod": 2160.0,
    "mean_interarrival": 1.5,
    "p_priority": 0.01,
    "p_new_user": 1.0,
    "mean_perm_check": 48.0,
    "p_no_permission": 0.2,
    "p_expired": 0.3,
    "p_warehouse": 0.5,
    "mean_wh_prep": 4.0,
    "std_wh_prep": 2.0,
    "p_dangerous": 0.5,
    "p_certificate": 0.7,
    "mean_ext_order": 1.5,
    "std_ext_order": 0.2,
    "p_local": 0.5,
    "mean_delivery_local": 72.0,
    "mean_delivery_nonlocal": 144.0,
    "inv_period_min": 120.0,
    "inv_period_max": 216.0,
    "inv_duration_min": 3.0,
    "inv_duration_max": 7.0,
    "time_limit": 120.0,
}

SEED = 42
LN2 = math.log(2.0)
MAX_ORDERS = 12      # сколько заявок прогнать в трассе


# ---------------------------------------------------------------------------
# «Середина датчиков»
# ---------------------------------------------------------------------------

def mid_exp(mean):
    """Медиана экспоненты Exp(mean) — формула -mean·ln(1-U) при U=0.5."""
    return mean * LN2


def mid_norm(mean, _std):
    """N(mean, std) без разброса — берём само mean."""
    return mean


def mid_uniform(lo, hi):
    return (lo + hi) / 2.0


# ---------------------------------------------------------------------------
# Детерминированное расписание инвентаризаций
# ---------------------------------------------------------------------------

def build_inventories(params):
    period = mid_uniform(params["inv_period_min"], params["inv_period_max"])
    duration = mid_uniform(params["inv_duration_min"], params["inv_duration_max"])
    inventories = []
    t = 0.0
    while True:
        t += period
        if t >= params["T_mod"]:
            break
        end = t + duration
        inventories.append((t, end))
        t = end
    return inventories, period, duration


# ---------------------------------------------------------------------------
# Печать заголовков / итогов
# ---------------------------------------------------------------------------

def print_header(params, period, duration):
    print()
    print("=" * 88)
    print("  Лабораторная работа №2 — упрощённая верификация (модель без разброса)")
    print("=" * 88)
    print("  Параметры модели (по умолчанию):")
    print("    Δt_прибытия (Expr 1.5)         ≈ {:.3f} ч  (медиана)".format(
        mid_exp(params["mean_interarrival"])))
    print("    Δt_разрешения (Expr 48)        ≈ {:.2f} ч   (медиана)".format(
        mid_exp(params["mean_perm_check"])))
    print("    Δt_подготовки склада N(4, 2)   = {:.2f} ч   (без ±)".format(
        params["mean_wh_prep"]))
    print("    Δt_размещения N(1.5, 0.2)      = {:.2f} ч   (без ±)".format(
        params["mean_ext_order"]))
    print("    Δt_доставки местный (Expr 72)  ≈ {:.2f} ч  (медиана)".format(
        mid_exp(params["mean_delivery_local"])))
    print("    Δt_доставки иногор. (Expr 144) ≈ {:.2f} ч  (медиана)".format(
        mid_exp(params["mean_delivery_nonlocal"])))
    print("    Инвентаризация:  каждые {:.0f} ч по {:.0f} ч".format(period, duration))
    print("    Лимит времени:   {:.0f} ч,   p_no_perm = {:.2f}, "
          "p_expired = {:.2f}".format(
            params["time_limit"], params["p_no_permission"], params["p_expired"]))
    print("    p_warehouse = {:.2f},  p_dangerous = {:.2f},  p_certificate = {:.2f}, "
          "p_local = {:.2f}".format(
            params["p_warehouse"], params["p_dangerous"],
            params["p_certificate"], params["p_local"]))
    print("    random.seed = {:d}".format(SEED))
    print("=" * 88)
    print()


# ---------------------------------------------------------------------------
# Один шаг — обработка одной заявки с распечаткой трассы
# ---------------------------------------------------------------------------

def process_order(p, order_num, t_arrival, state):
    """Возвращает строковое описание исхода: success / rej_noperm / ..."""
    is_priority = random.random() < p["p_priority"]
    badge = " [приоритет]" if is_priority else ""
    print("─" * 88)
    print("  Заявка #{:d}{}    t_прихода = {:.2f} ч".format(
        order_num, badge, t_arrival))

    # --- K1: проверка разрешения ---
    is_new = random.random() < p["p_new_user"]
    dt_perm = mid_exp(p["mean_perm_check"]) if is_new else 0.0
    t_after_perm = t_arrival + dt_perm
    print("  K1:  Δt разрешения = {:.2f} ч{}  →  t = {:.2f} ч".format(
        dt_perm, "  (новый пользователь)" if is_new else "  (повторный, без проверки)",
        t_after_perm))

    r = random.random()
    if r < p["p_no_permission"]:
        print("       r = {:.3f} < {:.2f}  →  ОТКАЗ: нет разрешения".format(
            r, p["p_no_permission"]))
        return ("rej_noperm", t_after_perm, None)
    if r < p["p_no_permission"] + p["p_expired"]:
        print("       r = {:.3f} < {:.2f}  →  ОТКАЗ: просрочено".format(
            r, p["p_no_permission"] + p["p_expired"]))
        return ("rej_expired", t_after_perm, None)
    print("       r = {:.3f}  →  разрешение OK".format(r))

    # --- маршрутизация ---
    u_path = random.random()
    use_wh = u_path < p["p_warehouse"]
    print("  Маршрут:  U = {:.3f}  →  {}".format(
        u_path, "СКЛАД (K2)" if use_wh else "ВНЕШНИЙ ПОСТАВЩИК (K3)"))

    if use_wh:
        # очередь склада
        if is_priority:
            t_start = max(t_after_perm, state["t_wh_current_end"])
        else:
            t_start = max(t_after_perm, state["t_wh_queue_end"])
        wait = max(0.0, t_start - t_after_perm)
        t_start = compute.adjust_for_inventory(t_start, state["inventories"])
        if wait > 0.0:
            print("       ожидание очереди = {:.2f} ч".format(wait))

        dt_wh = mid_norm(p["mean_wh_prep"], p["std_wh_prep"])
        t_done = t_start + dt_wh
        print("  K2:  начало {:.2f} ч, Δt подготовки {:.2f} ч  →  t завершения = {:.2f} ч"
              .format(t_start, dt_wh, t_done))

        state["t_wh_current_end"] = t_done
        if t_done > state["t_wh_queue_end"]:
            state["t_wh_queue_end"] = t_done

        # опасный груз + сертификат
        if random.random() < p["p_dangerous"]:
            if random.random() >= p["p_certificate"]:
                print("       опасный груз, сертификат отсутствует  →  ОТКАЗ")
                return ("rej_cert", t_done, t_done - t_arrival)
            print("       опасный груз, сертификат есть")

    else:
        dt_place = mid_norm(p["mean_ext_order"], p["std_ext_order"])
        t_current = t_after_perm + dt_place
        print("  K3:  Δt размещения = {:.2f} ч  →  t = {:.2f} ч".format(
            dt_place, t_current))

        is_local = random.random() < p["p_local"]
        if is_local:
            dt_del = mid_exp(p["mean_delivery_local"])
            print("       доставка местная,  Δt = {:.2f} ч".format(dt_del))
        else:
            dt_del = mid_exp(p["mean_delivery_nonlocal"])
            print("       доставка иногородняя,  Δt = {:.2f} ч".format(dt_del))
        t_done = t_current + dt_del

    total = t_done - t_arrival
    if total > p["time_limit"]:
        print("  Итог:  T = {:.2f} ч  > лимит {:.0f} ч  →  ОТКАЗ по лимиту".format(
            total, p["time_limit"]))
        return ("rej_time", t_done, total)

    print("  Итог:  T_completion = {:.2f} ч  ≤ {:.0f} ч  →  УСПЕХ".format(
        total, p["time_limit"]))
    return ("success", t_done, total)


# ---------------------------------------------------------------------------
# Основная трасса
# ---------------------------------------------------------------------------

def run_trace(params, max_orders=MAX_ORDERS):
    random.seed(SEED)

    inventories, period, duration = build_inventories(params)
    print_header(params, period, duration)

    state = {
        "t_wh_current_end": 0.0,
        "t_wh_queue_end": 0.0,
        "inventories": inventories,
    }

    counters = {"success": 0, "rej_noperm": 0, "rej_expired": 0,
                "rej_cert": 0, "rej_time": 0}
    completion_times = []
    in_system_times = []

    t_arrival = 0.0
    dt_arrive_const = mid_exp(params["mean_interarrival"])

    order_num = 0
    while order_num < max_orders:
        t_arrival += dt_arrive_const
        order_num += 1

        outcome, t_done, t_complete = process_order(
            params, order_num, t_arrival, state)
        counters[outcome] += 1
        if outcome == "success":
            completion_times.append(t_complete)
        else:
            # время «пребывания в системе» считается только справочно
            if t_complete is not None:
                in_system_times.append(t_complete)

    print("─" * 88)
    print_summary(counters, completion_times)


# ---------------------------------------------------------------------------
# Сводная статистика
# ---------------------------------------------------------------------------

def print_summary(counters, completion_times):
    print()
    print("=" * 88)
    print("  СВОДКА ПО ТРАССЕ")
    print("=" * 88)

    n_total = sum(counters.values())
    n_success = counters["success"]

    print("  Всего заявок:                        {:d}".format(n_total))
    print("  Успешно выполнено:                   {:d}".format(n_success))
    print("  Отказов всего:                       {:d}".format(n_total - n_success))
    print()
    print("  По причинам:")
    print("    Нет разрешения (K1):               {:d}".format(counters["rej_noperm"]))
    print("    Просрочено разрешение (K1):        {:d}".format(counters["rej_expired"]))
    print("    Нет сертификата (опасн. хим.):     {:d}".format(counters["rej_cert"]))
    print("    Превышен лимит времени:            {:d}".format(counters["rej_time"]))
    print()

    p_success = n_success / n_total if n_total else 0.0
    if completion_times:
        t_mean = sum(completion_times) / len(completion_times)
        t_min = min(completion_times)
        t_max = max(completion_times)
        print("  Показатели:")
        print("    P_success                       = {:.4f}".format(p_success))
        print("    T_mean (по {:d} успешным заявкам) = {:.2f} ч".format(
            len(completion_times), t_mean))
        print("    T_min / T_max                   = {:.2f} ч / {:.2f} ч".format(
            t_min, t_max))
    else:
        print("  Показатели:  P_success = {:.4f},  успешных заявок нет".format(p_success))
    print("=" * 88)
    print()
    print("  Сравнить с ручным расчётом по 4 сценариям диаграммы:")
    print("    • Сценарий 1 (отказ K1 'нет разрешения') — ищите в трассе строку")
    print("      'ОТКАЗ: нет разрешения' (вероятность {:.0f}%).".format(
        DEFAULT_PARAMS["p_no_permission"] * 100))
    print("    • Сценарий 2 (успех через склад)         — путь СКЛАД, успех.")
    print("    • Сценарий 3 (успех, местный поставщик)  — путь ВНЕШНИЙ + 'местная'.")
    print("    • Сценарий 4 (отказ по лимиту)           — путь ВНЕШНИЙ + 'иногородняя'.")
    print("=" * 88)
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    run_trace(DEFAULT_PARAMS, max_orders=MAX_ORDERS)


if __name__ == "__main__":
    main()
