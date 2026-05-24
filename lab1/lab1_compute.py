import math
import random
import statistics


def mean_value(data):
    n = len(data)
    if n == 0:
        return 0.0
    s = 0.0
    i = 0
    while i < n:
        s += data[i]
        i += 1
    return s / n


def std_deviation(data):
    n = len(data)
    if n < 2:
        return 0.0
    m = mean_value(data)
    s = 0.0
    i = 0
    while i < n:
        d = data[i] - m
        s += d * d
        i += 1
    return math.sqrt(s / (n - 1))


def normal_by_clt(size, mean_a, sigma):
    
    result = []
    i = 0
    while i < size:
        s = 0.0
        j = 0
        while j < 12:
            s += random.random()
            j += 1
        z = s - 6.0
        x = mean_a + sigma * z
        result.append(x)
        i += 1
    return result


def normal_by_box_muller(size, mean_a, sigma):
    result = []
    while len(result) < size:
        u1 = random.random()
        u2 = random.random()
        if u1 <= 0.0:
            continue
        r = math.sqrt(-2.0 * math.log(u1))
        angle = 2.0 * math.pi * u2
        z1 = r * math.cos(angle)
        z2 = r * math.sin(angle)
        result.append(mean_a + sigma * z1)
        if len(result) < size:
            result.append(mean_a + sigma * z2)
    return result


def build_histogram(data, bins):
    n = len(data)
    if n == 0:
        return []

    min_v = data[0]
    max_v = data[0]
    i = 1
    while i < n:
        if data[i] < min_v:
            min_v = data[i]
        if data[i] > max_v:
            max_v = data[i]
        i += 1

    if min_v == max_v:
        max_v = min_v + 1.0

    width = (max_v - min_v) / bins
    counts = [0] * bins

    i = 0
    while i < n:
        index = int((data[i] - min_v) / width)
        if index >= bins:
            index = bins - 1
        if index < 0:
            index = 0
        counts[index] += 1
        i += 1

    hist = []
    i = 0
    while i < bins:
        left = min_v + i * width
        right = left + width
        hist.append((left, right, counts[i]))
        i += 1
    return hist

# Критерий Смирнова для двух датчиков
def smirnov_two_sample(sample1, sample2, alpha):

    n1 = len(sample1)
    n2 = len(sample2)

    sorted_u = sorted(sample1)
    sorted_z = sorted(sample2)

    i = 0
    j = 0
    f1 = 0.0
    f2 = 0.0
    d_max = 0.0

    while i < n1 and j < n2:
        if sorted_u[i] < sorted_z[j]:
            f1 = (i + 1) / n1
            i += 1
        elif sorted_z[j] < sorted_u[i]:
            f2 = (j + 1) / n2
            j += 1
        else:
            value = sorted_u[i]
            while i < n1 and sorted_u[i] == value:
                i += 1
            while j < n2 and sorted_z[j] == value:
                j += 1
            f1 = i / n1
            f2 = j / n2

        d = abs(f1 - f2)
        if d > d_max:
            d_max = d

    while i < n1:
        f1 = (i + 1) / n1
        i += 1
        d = abs(f1 - f2)
        if d > d_max:
            d_max = d

    while j < n2:
        f2 = (j + 1) / n2
        j += 1
        d = abs(f1 - f2)
        if d > d_max:
            d_max = d

    c_alpha = math.sqrt(-0.5 * math.log(alpha / 2.0))
    d_alpha = c_alpha * math.sqrt((n1 + n2) / (n1 * n2))

    accept_h0 = d_max <= d_alpha
    return d_max, d_alpha, accept_h0


def normal_cdf(x, mean_a, sigma):
    if sigma <= 0.0:
        if x < mean_a:
            return 0.0
        if x > mean_a:
            return 1.0
        return 0.5
    z = (x - mean_a) / (sigma * math.sqrt(2.0))
    return 0.5 * (1.0 + math.erf(z))


def chi2_critical_upper(df, alpha):
    if df <= 0:
        return float("inf")
    if df <= 2 and abs(alpha - 0.05) < 1e-9:
        if df == 1:
            return 3.841
        if df == 2:
            return 5.991
    z = statistics.NormalDist().inv_cdf(1.0 - alpha)
    h = 2.0 / (9.0 * df)
    inner = 1.0 - h + z * math.sqrt(h)
    if inner <= 0.0:
        inner = 0.01
    return df * (inner ** 3)


def _merge_low_expected(obs, exp, min_exp):
    o = [float(obs[i]) for i in range(len(obs))]
    e = [float(exp[i]) for i in range(len(exp))]
    changed = True
    while changed and len(e) > 1:
        changed = False
        i = 0
        while i < len(e):
            if e[i] < min_exp:
                if i + 1 < len(e):
                    o[i] += o[i + 1]
                    e[i] += e[i + 1]
                    del o[i + 1]
                    del e[i + 1]
                elif i > 0:
                    o[i - 1] += o[i]
                    e[i - 1] += e[i]
                    del o[i]
                    del e[i]
                else:
                    i += 1
                    continue
                changed = True
                break
            i += 1
    return o, e


def pearson_chi2_normal_gof(sample, num_bins, mean_a, sigma, alpha, min_expected=5.0):
    n = len(sample)
    if n < 10:
        return None
    if num_bins < 3:
        return None
    if sigma <= 0.0:
        return None

    L = mean_a - 4.0 * sigma
    R = mean_a + 4.0 * sigma
    w = (R - L) / float(num_bins)

    obs = [0] * num_bins
    i = 0
    while i < n:
        x = sample[i]
        e1 = L + w
        e_last = L + (num_bins - 1) * w
        if x < e1:
            obs[0] += 1
        elif x >= e_last:
            obs[num_bins - 1] += 1
        else:
            k = int((x - L) / w)
            if k <= 0:
                k = 1
            if k >= num_bins:
                k = num_bins - 1
            obs[k] += 1
        i += 1

    exp_p = []
    j = 0
    while j < num_bins:
        if j == 0:
            left = -1.0e100
            right = L + w
        elif j == num_bins - 1:
            left = L + (num_bins - 1) * w
            right = 1.0e100
        else:
            left = L + j * w
            right = L + (j + 1) * w
        p = normal_cdf(right, mean_a, sigma) - normal_cdf(left, mean_a, sigma)
        if p < 1.0e-15:
            p = 1.0e-15
        exp_p.append(p)
        j += 1

    exp = [n * p for p in exp_p]

    o_m, e_m = _merge_low_expected(obs, exp, min_expected)
    if len(o_m) < 2:
        return None

    chi2 = 0.0
    i = 0
    while i < len(o_m):
        diff = o_m[i] - e_m[i]
        chi2 += (diff * diff) / e_m[i]
        i += 1

    d = len(o_m)
    r = 0
    df = d - r - 1
    if df < 1:
        return None

    chi2_crit = chi2_critical_upper(df, alpha)
    accept_h0 = chi2 <= chi2_crit

    return {
        "chi2": chi2,
        "df": df,
        "chi2_crit": chi2_crit,
        "accept_h0": accept_h0,
        "num_merged_bins": d,
    }
