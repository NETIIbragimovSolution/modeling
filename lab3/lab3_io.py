def _read_float_ge0(prompt, default):
    while True:
        text = input(prompt).strip().replace(",", ".")
        if text == "":
            return default
        try:
            v = float(text)
            if v < 0.0:
                print("  Ошибка: значение не может быть отрицательным.")
                continue
            return v
        except ValueError:
            print("  Ошибка: введите число.")


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


def _read_int_gt0(prompt, default):
    while True:
        text = input(prompt).strip()
        if text == "":
            return default
        try:
            v = int(text)
            if v <= 0:
                print("  Ошибка: значение должно быть больше 0.")
                continue
            return v
        except ValueError:
            print("  Ошибка: введите целое число.")


DEFAULTS = {
    "y0A_init":      120.0,
    "y0B_init":      150.0,
    "y11_init":       40.0,
    "y21_init":       40.0,
    "y12_init":       40.0,
    "y22_init":       40.0,
    "yCA_init":       20.0,
    "yCB_init":       30.0,
    "X_init":         15.0,
    "PA":             40.0,
    "PB":             60.0,
    "Dmax":           10.0,
    "Dsr":             6.0,
    "Dmin":            2.0,
    "delta_mu_dop":    0.04,
    "alpha":           0.5,
    "dt":              1.0,
    "T":             100.0,
}


def read_params():
    print("=" * 60)
    print("  Лабораторная работа №3. Динамическое моделирование")
    print("  производственной системы. Вариант 2б")
    print("=" * 60)
    print("  Нажмите Enter для использования значения по умолчанию.\n")

    p = {}
    p["y0A_init"]     = _read_float_gt0(f"  Начальный запас склада A y0A [={DEFAULTS['y0A_init']}]: ", DEFAULTS["y0A_init"])
    p["y0B_init"]     = _read_float_gt0(f"  Начальный запас склада B y0B [={DEFAULTS['y0B_init']}]: ", DEFAULTS["y0B_init"])
    p["y11_init"]     = _read_float_gt0(f"  Начальный уровень звена 11 y11 [={DEFAULTS['y11_init']}]: ", DEFAULTS["y11_init"])
    p["y21_init"]     = _read_float_gt0(f"  Начальный уровень звена 21 y21 [={DEFAULTS['y21_init']}]: ", DEFAULTS["y21_init"])
    p["y12_init"]     = _read_float_gt0(f"  Начальный уровень звена 12 y12 [={DEFAULTS['y12_init']}]: ", DEFAULTS["y12_init"])
    p["y22_init"]     = _read_float_gt0(f"  Начальный уровень звена 22 y22 [={DEFAULTS['y22_init']}]: ", DEFAULTS["y22_init"])
    p["yCA_init"]     = _read_float_ge0(f"  Начальный запас узла сборки A yCА [={DEFAULTS['yCA_init']}]: ", DEFAULTS["yCA_init"])
    p["yCB_init"]     = _read_float_ge0(f"  Начальный запас узла сборки B yCВ [={DEFAULTS['yCB_init']}]: ", DEFAULTS["yCB_init"])
    p["X_init"]       = _read_float_gt0(f"  Начальные потоки Xij(0) [={DEFAULTS['X_init']}]: ", DEFAULTS["X_init"])
    p["PA"]           = _read_float_gt0(f"  Потребность в деталях A на изделие ПА [={DEFAULTS['PA']}]: ", DEFAULTS["PA"])
    p["PB"]           = _read_float_gt0(f"  Потребность в деталях B на изделие ПВ [={DEFAULTS['PB']}]: ", DEFAULTS["PB"])
    p["Dmax"]         = _read_float_gt0(f"  Максимальная задержка Дmax [={DEFAULTS['Dmax']}]: ", DEFAULTS["Dmax"])
    p["Dsr"]          = _read_float_gt0(f"  Средняя задержка Дср [={DEFAULTS['Dsr']}]: ", DEFAULTS["Dsr"])
    p["Dmin"]         = _read_float_gt0(f"  Минимальная задержка Дmin [={DEFAULTS['Dmin']}]: ", DEFAULTS["Dmin"])
    p["delta_mu_dop"] = _read_float_gt0(f"  Допустимое отклонение коэф. сборки Δμдоп [={DEFAULTS['delta_mu_dop']}]: ", DEFAULTS["delta_mu_dop"])
    p["alpha"]        = _read_float_gt0(f"  Коэффициент регулирования α [={DEFAULTS['alpha']}]: ", DEFAULTS["alpha"])
    p["dt"]           = _read_float_gt0(f"  Шаг моделирования Δt [={DEFAULTS['dt']}]: ", DEFAULTS["dt"])
    p["T"]            = _read_float_gt0(f"  Горизонт моделирования T [={DEFAULTS['T']}]: ", DEFAULTS["T"])
    print()
    return p


def print_results(results):
    print("=" * 60)
    print("  РЕЗУЛЬТАТЫ МОДЕЛИРОВАНИЯ")
    print("=" * 60)
    print(f"  Шагов выполнено:              {results['steps']}")
    print(f"  Итоговый выпуск продукции Zc: {results['total_Zc']:.4f}")
    print(f"  Остаток склада A:             {results['y0A'][-1]:.4f}")
    print(f"  Остаток склада B:             {results['y0B'][-1]:.4f}")

    events = results["replenish_events"]
    if events:
        print(f"\n  Событий пополнения склада: {len(events)}")
        i = 0
        while i < len(events) and i < 10:
            ev = events[i]
            print(f"    t={ev[0]:.1f}  склад {ev[1]}  +{ev[2]:.2f}")
            i += 1
        if len(events) > 10:
            print(f"    ... (ещё {len(events) - 10})")
    else:
        print("  Пополнений склада не было.")
    print("=" * 60)
