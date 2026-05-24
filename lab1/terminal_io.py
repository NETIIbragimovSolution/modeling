def read_int(prompt, min_value):
    while True:
        text = input(prompt).strip()
        try:
            value = int(text)
            if value < min_value:
                print("Ошибка: число должно быть не меньше", min_value)
                continue
            return value
        except ValueError:
            print("Ошибка: введите целое число.")


def read_float(prompt, min_value, max_value):
    while True:
        text = input(prompt).strip().replace(",", ".")
        try:
            value = float(text)
            if value <= min_value or value >= max_value:
                print(
                    "Ошибка: число должно быть больше",
                    min_value,
                    "и меньше",
                    max_value,
                )
                continue
            return value
        except ValueError:
            print("Ошибка: введите число.")


def read_mean_or_default(prompt, default):
    while True:
        text = input(prompt).strip().replace(",", ".")
        if text == "":
            return default
        try:
            return float(text)
        except ValueError:
            print("Ошибка: введите число или пустую строку для значения по умолчанию.")


def read_sigma_or_default(prompt, default):
    while True:
        text = input(prompt).strip().replace(",", ".")
        if text == "":
            return default
        try:
            value = float(text)
            if value <= 0.0:
                print("Ошибка: sigma должно быть строго больше 0.")
                continue
            return value
        except ValueError:
            print("Ошибка: введите число или пустую строку для значения по умолчанию.")


def parse_int_list(text, min_value):
    parts = text.split(",")
    result = []
    i = 0
    while i < len(parts):
        part = parts[i].strip()
        if part == "":
            i += 1
            continue
        try:
            value = int(part)
            if value < min_value:
                return None
            result.append(value)
        except ValueError:
            return None
        i += 1
    if len(result) == 0:
        return None
    return result


def read_int_list_or_default(prompt, default_list, min_value):
    while True:
        text = input(prompt).strip()
        if text == "":
            return default_list
        parsed = parse_int_list(text, min_value)
        if parsed is None:
            print(
                "Ошибка: введите целые числа через запятую, каждое не меньше",
                min_value,
                "или пустую строку по умолчанию.",
            )
            continue
        return parsed


def read_yes_no(prompt):
    while True:
        text = input(prompt).strip().lower()
        if text == "y" or text == "yes" or text == "д" or text == "да":
            return True
        if text == "n" or text == "no" or text == "н" or text == "нет":
            return False
        print("Ошибка: введите yes/да или no/нет.")


def print_histogram(title, hist, sample_size):
    print("\n" + title)
    if len(hist) == 0:
        print("Нет данных для гистограммы.")
        return

    max_count = 1
    i = 0
    while i < len(hist):
        if hist[i][2] > max_count:
            max_count = hist[i][2]
        i += 1

    scale = 50.0 / max_count
    i = 0
    while i < len(hist):
        left, right, count = hist[i]
        bar_len = int(count * scale)
        bar = "*" * bar_len
        freq = count / sample_size
        print(
            "[{0:8.4f}; {1:8.4f})  {2:5d}  {3:7.4f}  {4}".format(
                left, right, count, freq, bar
            )
        )
        i += 1


def print_intro():
    print("Лабораторная работа 1, вариант 4")
    print("Вопрос: принадлежат ли две выборки одной генеральной совокупности.")
    print("Выборка 1: нормальное распределение по ЦПТ.")
    print("Выборка 2: метод Бокса-Маллера, затем y = a + sigma * z (текст задания).")
    print("Критерий: двухвыборочный критерий Смирнова.")


def print_distribution_params(mean_a, sigma):
    print(
        "\nПараметры распределения: a = {0}, sigma^2 = {1}".format(
            mean_a, sigma * sigma
        )
    )


def print_sample_stats(n1, n2, m1, s1, m2, s2):
    print("Выборка 1 (ЦПТ):  n = {0}, mean = {1:.6f}, std = {2:.6f}".format(n1, m1, s1))
    print(
        "Выборка 2 (Бокс-Маллер): n = {0}, mean = {1:.6f}, std = {2:.6f}".format(
            n2, m2, s2
        )
    )


def print_pearson_result(label, result, alpha):
    if result is None:
        print(
            "\nКритерий Пирсона ({0}): недостаточно данных или нельзя добиться E >= 5 в каждом кармане (увеличьте n или уменьшите число интервалов).".format(
                label
            )
        )
        return
    print("\nКритерий Пирсона:")
    print("H0: эмпирическое распределение согласуется с N(a, sigma^2) с заданными a и sigma.")
    print("Выборка: {0}".format(label))
    print("chi^2_набл = {0:.6f}".format(result["chi2"]))
    print("Число степеней свободы k = d - r - 1, r = 0 (параметры закона заданы): k = {0}".format(result["df"]))
    print("Число карманов d (после объединения малых E): {0}".format(result["num_bins"]))
    print(
        "Критическое значение chi^2 для k = {0} и уровня значимости alpha = {1} найдите по таблице распределения chi^2.".format(
            result["df"], alpha
        )
    )
    print(
        "Правило: если chi^2_набл <= chi^2_крит из таблицы — H0 не отвергают; если больше — отвергают."
    )


def print_smirnov_result(d, d_alpha, accept_h0, alpha):
    beta = 1.0 - alpha
    print("\nКритерий Смирнова:")
    print("H0: две выборки относятся к одной генеральной совокупности.")
    print("D = max|F_E(U) - F_E(Z)| по эмпирическим функциям распределения.")
    print("D       = {0:.6f}".format(d))
    print("D_alpha = {0:.6f} при уровне значимости alpha = {1}".format(d_alpha, alpha))
    print("beta = 1 - alpha = {0:.6f} (доверительная вероятность)".format(beta))
    if accept_h0:
        print(
            "Вывод: D <= D_alpha — H0 не отвергается (выборки согласуются с гипотезой об одной совокупности)."
        )
    else:
        print(
            "Вывод: D > D_alpha — H0 отвергается (при D > D_alpha гипотеза отвергается с beta = 1 - alpha)."
        )


def print_plot_notice():
    print("\nОткроется окно с графиками гистограмм (закройте его — программа продолжит работу).")


def print_study_sample_size_header():
    print("\nИсследование влияния объема выборки:")
    print("Для каждого n заново генерируются две выборки; сравниваются D и D_alpha.")


def print_study_sample_size_row(n, bins, d, d_alpha, accept_h0):
    text = "H0 не отвергается" if accept_h0 else "H0 отвергается"
    print(
        "n = {0:5d}, bins = {1:3d}, D = {2:.6f}, D_alpha = {3:.6f}, {4}".format(
            n, bins, d, d_alpha, text
        )
    )


def print_study_sample_size_footer():
    print(
        "Итог: при росте n оценка D обычно стабилизируется; "
        "D_alpha убывает — порог для критерия Смирнова становится строже."
    )


def print_study_bins_header():
    print("\nИсследование влияния числа карманов гистограммы:")


def print_study_bins_row(b, h1_left, h1_right, h2_left, h2_right, smirnov_text):
    print(
        "bins = {0:3d}, диапазон1=({1:.3f}; {2:.3f}), диапазон2=({3:.3f}; {4:.3f}), вывод по Смирнову: {5}".format(
            b, h1_left, h1_right, h2_left, h2_right, smirnov_text
        )
    )


def print_study_bins_footer(d, d_alpha, smirnov_text):
    print("Для критерия Смирнова число карманов не входит в расчет D и D_alpha.")
    print("Карманы влияют на гистограмму (эмпирическую плотность), но не на вывод по D.")
    print("Фиксированная пара выборок: D = {0:.6f}, D_alpha = {1:.6f}, {2}".format(
        d, d_alpha, smirnov_text
    ))

