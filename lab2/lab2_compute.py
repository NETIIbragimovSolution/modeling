"""
Simulation engine for Lab 2: Chemical warehouse ordering system.

Architecture (Q-schema):
  W  — Poisson arrivals (exponential inter-arrival), 1% priority
  K1 — Permission check: runs in parallel per order (no shared bottleneck).
       Time penalty only for new users (p_new_user fraction).
       Probabilistic rejection: p_no_permission and p_expired.
  K2a — Warehouse channel (single server): Normal prep time, blocked by
        periodic inventory (L).  Dangerous-goods certificate check.
  K2b — External supplier path (no queue): Normal order-placement time +
        exponential delivery (local or non-local).
  H  — FIFO queue for warehouse channel (priority orders jump non-priority).
  L  — Inventory disturbance: Uniform period, Uniform duration.
  Y1 — Successful orders; Y2 — Rejections (4 reasons).

Constraint: if total order time (from arrival to completion) > time_limit → cancel.
"""

import math
import random


# ---------------------------------------------------------------------------
# Random variable generators
# ---------------------------------------------------------------------------

def gen_exponential(mean):
    """Inverse-transform exponential: -mean * ln(1 - U)."""
    u = random.random()
    if u >= 1.0:
        u = 0.9999999999
    return -mean * math.log(1.0 - u)


def gen_normal(mean, std):
    """Box-Muller normal random variable."""
    u1 = random.random()
    u2 = random.random()
    if u1 <= 0.0:
        u1 = 1e-15
    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return mean + std * z


def gen_uniform(lo, hi):
    return lo + random.random() * (hi - lo)


# ---------------------------------------------------------------------------
# Inventory schedule
# ---------------------------------------------------------------------------

def generate_inventory_schedule(params):
    """Return (schedule, inv_periods, inv_durations) for [0, T_mod]."""
    schedule = []
    inv_periods = []
    inv_durations = []
    t = 0.0
    while True:
        gap = gen_uniform(params["inv_period_min"], params["inv_period_max"])
        inv_periods.append(gap)
        t += gap
        if t >= params["T_mod"]:
            break
        duration = gen_uniform(params["inv_duration_min"], params["inv_duration_max"])
        inv_durations.append(duration)
        end = t + duration
        schedule.append((t, end))
        t = end
    return schedule, inv_periods, inv_durations


def adjust_for_inventory(t_start, inventories):
    """
    Push t_start past any inventory window it falls inside.
    Repeats until t_start is in a free slot.
    """
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(inventories):
            inv_s, inv_e = inventories[i]
            if inv_s <= t_start < inv_e:
                t_start = inv_e
                changed = True
            i += 1
    return t_start


# ---------------------------------------------------------------------------
# One simulation realization
# ---------------------------------------------------------------------------

def simulate_one_realization(params):
    """
    Simulate one quarter.

    Key architectural decision:
    - Permission check (K1) runs IN PARALLEL per order — it adds delay to
      that order's lifecycle but does NOT block the channel for other orders.
    - Warehouse (K2a) is the only shared bottleneck resource.
    - External supplier path (K2b) has no queue.
    - Priority orders jump the warehouse queue (they only wait for the
      currently-running service, not queued non-priority orders).
      Tracked via separate t_wh_free_current (end of current service) vs
      t_wh_free_queue (end of all queued services).
    """
    T_mod = params["T_mod"]

    # warehouse channel tracking
    t_wh_current_end = 0.0   # when the currently-running service finishes
    t_wh_queue_end = 0.0     # when all queued services finish (FIFO)

    N_total = 0
    N_success = 0
    N_rej_noperm = 0
    N_rej_expired = 0
    N_rej_cert = 0
    N_rej_time = 0

    T_sum_completion = 0.0
    T_sum_wait = 0.0
    completion_times = []

    inventories, inv_periods, inv_durations = generate_inventory_schedule(params)

    dist_samples = {
        "interarrival_times": [],
        "perm_check_times": [],
        "wh_prep_times": [],
        "ext_order_times": [],
        "delivery_local_times": [],
        "delivery_nonlocal_times": [],
        "inv_periods": inv_periods,
        "inv_durations": inv_durations,
    }

    t_arrival = 0.0

    while True:
        # generate next arrival
        dt_arr = gen_exponential(params["mean_interarrival"])
        dist_samples["interarrival_times"].append(dt_arr)
        t_arrival += dt_arr
        if t_arrival >= T_mod:
            break

        is_priority = random.random() < params["p_priority"]
        N_total += 1

        # --- Phase 1: permission check (parallel, non-blocking) ---
        # Only new users need the time-consuming check.
        is_new_user = random.random() < params["p_new_user"]
        if is_new_user:
            dt_perm = gen_exponential(params["mean_perm_check"])
            dist_samples["perm_check_times"].append(dt_perm)
        else:
            dt_perm = 0.0
        t_after_perm = t_arrival + dt_perm

        # probabilistic rejection
        r = random.random()
        if r < params["p_no_permission"]:
            N_rej_noperm += 1
            continue
        if r < params["p_no_permission"] + params["p_expired"]:
            N_rej_expired += 1
            continue

        # --- Phase 2: fulfillment path ---
        use_warehouse = random.random() < params["p_warehouse"]

        if use_warehouse:
            # --- Warehouse path (K2a) ---
            # Priority order jumps non-priority queue — waits only for
            # the currently-running service, not the full queue.
            if is_priority:
                t_wh_start = max(t_after_perm, t_wh_current_end)
            else:
                t_wh_start = max(t_after_perm, t_wh_queue_end)

            T_sum_wait += max(0.0, t_wh_start - t_after_perm)

            # account for inventory blockage
            t_wh_start = adjust_for_inventory(t_wh_start, inventories)

            dt_wh = gen_normal(params["mean_wh_prep"], params["std_wh_prep"])
            dist_samples["wh_prep_times"].append(dt_wh)
            if dt_wh < 0.0:
                dt_wh = 0.0
            t_done = t_wh_start + dt_wh

            # update warehouse timeline
            t_wh_current_end = t_done
            if t_done > t_wh_queue_end:
                t_wh_queue_end = t_done

            # dangerous goods certificate check
            if random.random() < params["p_dangerous"]:
                if random.random() >= params["p_certificate"]:
                    N_rej_cert += 1
                    continue

        else:
            T_sum_wait += 0.0  # no queue on this path

            dt_place = gen_normal(params["mean_ext_order"],
                                  params["std_ext_order"])
            dist_samples["ext_order_times"].append(dt_place)
            if dt_place < 0.0:
                dt_place = 0.0
            t_current = t_after_perm + dt_place

            is_local = random.random() < params["p_local"]
            if is_local:
                dt_delivery = gen_exponential(params["mean_delivery_local"])
                dist_samples["delivery_local_times"].append(dt_delivery)
            else:
                dt_delivery = gen_exponential(params["mean_delivery_nonlocal"])
                dist_samples["delivery_nonlocal_times"].append(dt_delivery)
            t_done = t_current + dt_delivery

        # --- Time limit check ---
        total_time = t_done - t_arrival
        if total_time > params["time_limit"]:
            N_rej_time += 1
            continue

        # --- Success ---
        N_success += 1
        T_sum_completion += total_time
        completion_times.append(total_time)

    return {
        "N_total": N_total,
        "N_success": N_success,
        "N_rej_noperm": N_rej_noperm,
        "N_rej_expired": N_rej_expired,
        "N_rej_cert": N_rej_cert,
        "N_rej_time": N_rej_time,
        "T_sum_completion": T_sum_completion,
        "T_sum_wait": T_sum_wait,
        "completion_times": completion_times,
        "dist_samples": dist_samples,
    }


# ---------------------------------------------------------------------------
# Run N realizations and aggregate
# ---------------------------------------------------------------------------

def run_n_realizations(params, n_runs):
    p_list = []
    t_list = []
    wait_list = []

    agg = {k: 0 for k in ("N_total", "N_success", "N_rej_noperm",
                           "N_rej_expired", "N_rej_cert", "N_rej_time")}
    all_completion_times = []
    agg_dist = {
        "interarrival_times": [],
        "perm_check_times": [],
        "wh_prep_times": [],
        "ext_order_times": [],
        "delivery_local_times": [],
        "delivery_nonlocal_times": [],
        "inv_periods": [],
        "inv_durations": [],
    }

    i = 0
    while i < n_runs:
        r = simulate_one_realization(params)

        for k in agg:
            agg[k] += r[k]
        all_completion_times.extend(r["completion_times"])

        for k in agg_dist:
            agg_dist[k].extend(r["dist_samples"][k])

        if r["N_total"] > 0:
            p_list.append(r["N_success"] / r["N_total"])
            wait_list.append(r["T_sum_wait"] / r["N_total"])
        else:
            p_list.append(0.0)
            wait_list.append(0.0)

        if r["N_success"] > 0:
            t_list.append(r["T_sum_completion"] / r["N_success"])
        else:
            t_list.append(0.0)

        i += 1

    p_mean = _mean(p_list)
    t_mean = _mean(t_list)
    wait_mean = _mean(wait_list)
    p_var = _variance(p_list, p_mean)

    return {
        "n_runs": n_runs,
        "p_mean": p_mean,
        "p_var": p_var,
        "t_mean": t_mean,
        "wait_mean": wait_mean,
        "agg_N_total": agg["N_total"],
        "agg_N_success": agg["N_success"],
        "agg_N_rej_noperm": agg["N_rej_noperm"],
        "agg_N_rej_expired": agg["N_rej_expired"],
        "agg_N_rej_cert": agg["N_rej_cert"],
        "agg_N_rej_time": agg["N_rej_time"],
        "all_completion_times": all_completion_times,
        "distribution_samples": agg_dist,
        "p_list": p_list,
        "t_list": t_list,
    }


# ---------------------------------------------------------------------------
# Statistical stability
# ---------------------------------------------------------------------------

def determine_n_realizations(params, epsilon, t_alpha, n_init, progress_cb=None):
    n_cur = n_init
    results = None
    stage = 0

    while True:
        results = run_n_realizations(params, n_cur)
        stage += 1

        p_var = results["p_var"]
        if p_var <= 0.0:
            break

        n_star = int(math.ceil(t_alpha * t_alpha * p_var / (epsilon * epsilon)))

        if progress_cb is not None:
            progress_cb(stage, n_cur, n_star, results["p_mean"], p_var)

        if n_star <= n_cur:
            break

        n_cur = n_star

    results["n_final"] = n_cur
    return results


# ---------------------------------------------------------------------------
# Sensitivity analysis
# ---------------------------------------------------------------------------

def sensitivity_run(params, param_name, values, n_runs):
    rows = []
    for v in values:
        p_copy = dict(params)
        p_copy[param_name] = v
        res = run_n_realizations(p_copy, n_runs)
        rows.append((v, res["p_mean"], res["t_mean"]))
    return rows


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def _mean(data):
    if len(data) == 0:
        return 0.0
    total = 0.0
    i = 0
    while i < len(data):
        total += data[i]
        i += 1
    return total / len(data)


def _variance(data, mean_val):
    n = len(data)
    if n < 2:
        return 0.0
    s = 0.0
    i = 0
    while i < n:
        d = data[i] - mean_val
        s += d * d
        i += 1
    return s / (n - 1)


def std_dev(data):
    m = _mean(data)
    return math.sqrt(_variance(data, m))
