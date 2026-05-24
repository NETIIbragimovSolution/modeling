import math
import random


def _lottery(y0_current, y0_init):
    r = random.random()
    if r < 0.4:
        amount = 0.0
    elif r < 0.6:
        amount = 0.5 * y0_init
    elif r < 0.7:
        amount = 0.7 * y0_init
    else:
        amount = 0.4 * y0_init
    return amount


def run_simulation(params):
    # --- Линия A: 1 звено (y11, D11) ---
    # --- Линия B: 3 звена (y21->y12->y22, D21->D22->D23) --- Рис.7 вариант 2
    y0A = float(params["y0A_init"])
    y0B = float(params["y0B_init"])
    y11 = float(params["y11_init"])
    y21 = float(params["y21_init"])
    y12 = float(params["y12_init"])
    y22 = float(params["y22_init"])
    yCA = float(params["yCA_init"])
    yCB = float(params["yCB_init"])

    y0A_init = y0A
    y0B_init = y0B

    PA      = float(params["PA"])
    PB      = float(params["PB"])
    Dmax    = float(params["Dmax"])
    Dsr     = float(params["Dsr"])
    Dmin    = float(params["Dmin"])
    dmu_dop = float(params["delta_mu_dop"])
    alpha   = float(params["alpha"])
    dt      = float(params["dt"])
    T       = float(params["T"])

    X_init = float(params["X_init"])
    D11 = max(Dmin, min(Dmax, y11 / X_init))
    D21 = max(Dmin, min(Dmax, y21 / X_init))
    D22 = max(Dmin, min(Dmax, y12 / X_init))
    D23 = max(Dmin, min(Dmax, y22 / X_init))

    crit_A = 0.2 * y0A_init
    crit_B = 0.2 * y0B_init
    stop_A = 0.05 * y0A_init
    stop_B = 0.05 * y0B_init

    eps = 1e-9

    ts   = [0.0]
    Zcs  = [0.0]
    Y0As = [y0A]
    Y0Bs = [y0B]
    Y11s = [y11]
    Y21s = [y21]
    Y12s = [y12]
    Y22s = [y22]
    YCAs = [yCA]
    YCBs = [yCB]
    D11s = [D11]
    D21s = [D21]
    D22s = [D22]
    D23s = [D23]
    replenish_events = []

    t    = 0.0
    step = 0

    while t < T:
        # --- темпы потоков ---
        X11 = y11 / (D11 + eps)   # линия A: выход звена 11
        X21 = y21 / (D21 + eps)   # линия B: выход звена 21
        X22 = y12 / (D22 + eps)   # линия B: выход звена 12
        X23 = y22 / (D23 + eps)   # линия B: выход звена 22

        # входные потоки ограничены складом
        X10A = min(X11, y0A / (dt + eps))
        X10B = min(X21, y0B / (dt + eps))

        # --- выпуск готовых изделий ---
        Zc = min(yCA / PA, yCB / PB) if PA > 0 and PB > 0 else 0.0
        Zc = max(Zc, 0.0)

        # --- коэффициент сборки ---
        mu_A    = yCA / PA if PA > 0 else 0.0
        mu_B    = yCB / PB if PB > 0 else 0.0
        delta_mu = mu_A - mu_B

        # --- обновление уровней (формула 7) ---
        y11_new = y11 + dt * (X10A - X11)
        y21_new = y21 + dt * (X10B - X21)
        y12_new = y12 + dt * (X21  - X22)
        y22_new = y22 + dt * (X22  - X23)
        yCA_new = yCA + dt * X11  - PA * Zc * dt
        yCB_new = yCB + dt * X23  - PB * Zc * dt
        y0A_new = y0A - dt * X10A
        y0B_new = y0B - dt * X10B

        y11_new = max(y11_new, 0.0)
        y21_new = max(y21_new, 0.0)
        y12_new = max(y12_new, 0.0)
        y22_new = max(y22_new, 0.0)
        yCA_new = max(yCA_new, 0.0)
        yCB_new = max(yCB_new, 0.0)
        y0A_new = max(y0A_new, 0.0)
        y0B_new = max(y0B_new, 0.0)

        # --- обновление задержек (формула 6) ---
        # знаменатель = D_old * X_old = y_old (уровень пред. шага)
        denom11 = D11 * X11 + eps
        denom21 = D21 * X21 + eps
        denom22 = D22 * X22 + eps
        denom23 = D23 * X23 + eps

        if abs(delta_mu) > dmu_dop:
            sgn = 1.0 if delta_mu > 0 else -1.0
        else:
            sgn = 0.0

        # если A опережает (sgn>0): замедляем A (D11↑), ускоряем B (D21,D22,D23↓)
        D11_new = Dmin + Dsr * (y11_new / denom11) + alpha * Dmax * sgn
        D21_new = Dmin + Dsr * (y21_new / denom21) - alpha * Dmax * sgn
        D22_new = Dmin + Dsr * (y12_new / denom22) - alpha * Dmax * sgn
        D23_new = Dmin + Dsr * (y22_new / denom23) - alpha * Dmax * sgn

        D11_new = max(Dmin, min(Dmax, D11_new))
        D21_new = max(Dmin, min(Dmax, D21_new))
        D22_new = max(Dmin, min(Dmax, D22_new))
        D23_new = max(Dmin, min(Dmax, D23_new))

        # --- пополнение склада ---
        repl_A = 0.0
        repl_B = 0.0
        if y0A_new < crit_A:
            repl_A = _lottery(y0A_new, y0A_init)
            if repl_A > 0:
                replenish_events.append((t + dt, "A", repl_A))
        if y0B_new < crit_B:
            repl_B = _lottery(y0B_new, y0B_init)
            if repl_B > 0:
                replenish_events.append((t + dt, "B", repl_B))

        y0A_new += repl_A
        y0B_new += repl_B

        # --- обновление состояния ---
        y11, y21, y12, y22 = y11_new, y21_new, y12_new, y22_new
        yCA, yCB           = yCA_new, yCB_new
        y0A, y0B           = y0A_new, y0B_new
        D11, D21, D22, D23 = D11_new, D21_new, D22_new, D23_new

        t = round(t + dt, 10)
        step += 1

        ts.append(t)
        Zcs.append(Zc)
        Y0As.append(y0A)
        Y0Bs.append(y0B)
        Y11s.append(y11)
        Y21s.append(y21)
        Y12s.append(y12)
        Y22s.append(y22)
        YCAs.append(yCA)
        YCBs.append(yCB)
        D11s.append(D11)
        D21s.append(D21)
        D22s.append(D22)
        D23s.append(D23)

        if y0A <= stop_A and y0B <= stop_B:
            break

    total_Zc = 0.0
    i = 0
    while i < len(Zcs):
        total_Zc += Zcs[i]
        i += 1

    return {
        "t":   ts,
        "Zc":  Zcs,
        "y0A": Y0As,
        "y0B": Y0Bs,
        "y11": Y11s,
        "y21": Y21s,
        "y12": Y12s,
        "y22": Y22s,
        "yCA": YCAs,
        "yCB": YCBs,
        "D11": D11s,
        "D21": D21s,
        "D22": D22s,
        "D23": D23s,
        "replenish_events": replenish_events,
        "total_Zc":  total_Zc,
        "steps":     step,
        "y0A_init":  y0A_init,
        "y0B_init":  y0B_init,
    }
