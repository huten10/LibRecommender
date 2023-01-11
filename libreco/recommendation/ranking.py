import numpy as np
from numpy.random import default_rng
from scipy.special import expit, softmax

# Numpy doc states that it is recommended to use new random API
# https://numpy.org/doc/stable/reference/random/index.html
np_rng = default_rng()


def rank_recommendations(
    task,
    preds,
    n_rec,
    n_items,
    consumed,
    id2item,
    inner_id,
    filter_consumed=True,
    random_rec=False,
    return_scores=False,
):
    if n_rec > n_items:
        raise ValueError(f"`n_rec` {n_rec} exceeds num of items {n_items}")
    ids = np.arange(len(preds))
    if filter_consumed and n_rec + len(consumed) <= n_items:
        ids, preds = filter_items(ids, preds, consumed)
    if random_rec:
        ids, preds = random_select(ids, preds, n_rec)
    else:
        ids, preds = partition_select(ids, preds, n_rec)

    if not inner_id:
        ids = np.array([id2item[i] for i in ids])
    indices = np.argsort(preds)[::-1]
    ids = ids[indices]
    if return_scores:
        scores = preds[indices]
        if task == "ranking":
            scores = expit(scores)
        return ids, scores
    else:
        return ids


def filter_items(ids, preds, items):
    mask = np.isin(ids, items, assume_unique=True, invert=True)
    return ids[mask], preds[mask]


# add `**0.75` to lower probability of high score items
def get_reco_probs(preds):
    p = np.power(softmax(preds), 0.75) + 1e-8  # avoid zero probs
    return p / p.sum()


def random_select(ids, preds, n_rec):
    p = get_reco_probs(preds)
    mask = np_rng.choice(len(preds), n_rec, p=p, replace=False, shuffle=False)
    return ids[mask], preds[mask]


def partition_select(ids, preds, n_rec):
    mask = np.argpartition(preds, -n_rec)[-n_rec:]
    return ids[mask], preds[mask]
