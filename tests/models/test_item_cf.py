import numpy as np
import pytest

from libreco.algorithms import ItemCF
from tests.utils_data import remove_path, set_ranking_labels
from tests.utils_metrics import get_metrics
from tests.utils_pred import ptest_preds
from tests.utils_reco import ptest_recommends
from tests.utils_save_load import save_load_model


@pytest.mark.parametrize("task", ["rating", "ranking"])
@pytest.mark.parametrize("sim_type", ["cosine", "pearson", "jaccard", "unknown"])
@pytest.mark.parametrize("store_top_k", [True, False])
@pytest.mark.parametrize("neg_sampling", [True, False, None])
def test_item_cf(pure_data_small, task, sim_type, store_top_k, neg_sampling):
    pd_data, train_data, eval_data, data_info = pure_data_small
    if neg_sampling is False:
        set_ranking_labels(train_data)
        set_ranking_labels(eval_data)

    model = ItemCF(
        task=task,
        data_info=data_info,
        sim_type=sim_type,
        k_sim=20,
        store_top_k=store_top_k,
    )

    if neg_sampling is None:
        with pytest.raises(AssertionError):
            model.fit(train_data, neg_sampling)
    elif task == "rating" and neg_sampling:
        with pytest.raises(ValueError):
            model.fit(train_data, neg_sampling)
    elif sim_type == "unknown":
        with pytest.raises(ValueError):
            model.fit(train_data, neg_sampling)
    else:
        model.fit(
            train_data,
            neg_sampling,
            verbose=2,
            eval_data=eval_data,
            metrics=get_metrics(task),
            k=10,
            eval_user_num=200,
        )
        ptest_preds(model, task, pd_data, with_feats=False)
        ptest_recommends(model, data_info, pd_data, with_feats=False)
        model.recommend_user(1, 10, random_rec=True)
        with pytest.raises(ValueError):
            model.predict(user="cold user1", item="cold item2", cold_start="other")
        with pytest.raises(TypeError):
            model.recommend_user(1, 7, seq=[1, 2, 3])

        # test save and load model
        loaded_model, loaded_data_info = save_load_model(ItemCF, model, data_info)
        ptest_preds(loaded_model, task, pd_data, with_feats=False)
        ptest_recommends(loaded_model, loaded_data_info, pd_data, with_feats=False)

        with pytest.raises(NotImplementedError):
            model.rebuild_model("model_path", "item_cf")


def test_all_consumed_recommend(pure_data_small, monkeypatch):
    _, train_data, eval_data, data_info = pure_data_small

    model = ItemCF(task="ranking", data_info=data_info)
    model.fit(train_data, neg_sampling=True, verbose=0)
    model.save("not_existed_path", "item_cf2")
    remove_path("not_existed_path")
    with monkeypatch.context() as m:
        m.setitem(model.user_consumed, 0, list(range(model.n_items)))
        recos = model.recommend_user(user=1, n_rec=7)
        assert np.all(np.isin(recos[1], data_info.popular_items))
