import math
import random


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
