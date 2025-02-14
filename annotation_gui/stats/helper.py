import numpy as np
import scipy.stats as stats


def calc_z_value(confidence_level: int) -> float:
    return stats.norm.ppf(1 - (1 - confidence_level) / 2)


def is_stop_criterion_met(
    n_labeled: int,
    min_n_samples: int,
    n_bad: float,
    z_value: float,
    moe_threshhold: float,
) -> bool:
    if n_labeled >= min_n_samples:
        p_hat = calc_p_hat(n_bad, n_labeled)
        curr_moe = calc_curr_moe(z_value, p_hat, n_labeled)
        if curr_moe <= moe_threshhold:
            return True
    return False

def calc_p_hat(n_bad, n_labeled):
    p_hat = n_bad / n_labeled if n_labeled > 0 else 0
    return p_hat

def calc_curr_moe(z_value, p_hat, n_labeled):
    curr_moe = (
        z_value * np.sqrt((p_hat * (1 - p_hat)) / n_labeled)
        if n_labeled > 0
        else 1.0
    )
    return curr_moe