import random

import lab1_compute as compute
import terminal_io as io
from hist_plotter import plot_two_histograms


def run_one_experiment(n1, n2, bins, alpha, mean_a, sigma, draw_plot):
    sample_clt = compute.normal_by_clt(n1, mean_a, sigma)
    sample_box = compute.normal_by_box_muller(n2, mean_a, sigma)

    m1 = compute.mean_value(sample_clt)
    s1 = compute.std_deviation(sample_clt)
    m2 = compute.mean_value(sample_box)
    s2 = compute.std_deviation(sample_box)

    io.print_distribution_params(mean_a, sigma)
    io.print_sample_stats(n1, n2, m1, s1, m2, s2)

    hist1 = compute.build_histogram(sample_clt, bins)
    hist2 = compute.build_histogram(sample_box, bins)
    io.print_histogram("Гистограмма выборки 1 (ЦПТ):", hist1, n1)
    io.print_histogram("Гистограмма выборки 2 (Бокс-Маллер):", hist2, n2)

    d, d_alpha, ok = compute.smirnov_two_sample(sample_clt, sample_box, alpha)
    io.print_smirnov_result(d, d_alpha, ok, alpha)

    if draw_plot:
        io.print_plot_notice()
        t1 = "Выборка 1 (ЦПТ), a={0}, sigma={1}".format(mean_a, sigma)
        t2 = "Выборка 2 (Бокс-Маллер), a={0}, sigma={1}".format(mean_a, sigma)
        plot_two_histograms(sample_clt, sample_box, bins, t1, t2)


def study_sample_size(n_list, bins, alpha, mean_a, sigma):
    io.print_study_sample_size_header()
    i = 0
    while i < len(n_list):
        n = n_list[i]
        s1 = compute.normal_by_clt(n, mean_a, sigma)
        s2 = compute.normal_by_box_muller(n, mean_a, sigma)
        d, d_alpha, ok = compute.smirnov_two_sample(s1, s2, alpha)
        io.print_study_sample_size_row(n, bins, d, d_alpha, ok)
        i += 1
    io.print_study_sample_size_footer()


def study_bins(n, bins_list, alpha, mean_a, sigma):
    io.print_study_bins_header()
    base1 = compute.normal_by_clt(n, mean_a, sigma)
    base2 = compute.normal_by_box_muller(n, mean_a, sigma)
    d, d_alpha, ok = compute.smirnov_two_sample(base1, base2, alpha)
    smirnov_text = "H0 не отвергается" if ok else "H0 отвергается"
    i = 0
    while i < len(bins_list):
        b = bins_list[i]
        h1 = compute.build_histogram(base1, b)
        h2 = compute.build_histogram(base2, b)
        io.print_study_bins_row(b, h1[0][0], h1[-1][1], h2[0][0], h2[-1][1], smirnov_text)
        i += 1
    io.print_study_bins_footer(d, d_alpha, smirnov_text)


def main():
    io.print_intro()

    random.seed()

    default_a = 2.0
    default_sigma = 1.0

    mean_a = io.read_mean_or_default(
        "\nМатематическое ожидание a [Enter = 2]: ",
        default_a,
    )
    sigma = io.read_sigma_or_default(
        "Среднее квадратическое отклонение sigma (sigma^2 — дисперсия) [Enter = 1]: ",
        default_sigma,
    )

    n1 = io.read_int("Объем 1-й выборки n1 (>= 20): ", 20)
    n2 = io.read_int("Объем 2-й выборки n2 (>= 20): ", 20)
    bins = io.read_int("Число карманов гистограммы (>= 5): ", 5)
    alpha = io.read_float("Уровень значимости alpha, 0 < alpha < 1: ", 0.0, 1.0)
    draw_plot = io.read_yes_no("Построить графики гистограмм в matplotlib? (yes/no): ")

    n_study = io.read_int_list_or_default(
        "Объемы n для исследования (через запятую, Enter = 50,100,200,500,1000): ",
        [50, 100, 200, 500, 1000],
        20,
    )
    bins_study = io.read_int_list_or_default(
        "Числа карманов для исследования (через запятую, Enter = 5,10,15,20,30): ",
        [5, 10, 15, 20, 30],
        5,
    )

    run_one_experiment(n1, n2, bins, alpha, mean_a, sigma, draw_plot)

    study_sample_size(n_study, bins, alpha, mean_a, sigma)
    study_bins(max(n1, n2), bins_study, alpha, mean_a, sigma)

    io.print_report_reminder()


if __name__ == "__main__":
    main()
