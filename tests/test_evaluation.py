from action_semantics.retrieval.evaluation import ndcg_at_k, predict_pairwise_winner, reciprocal_rank


def test_predict_pairwise_winner_tie():
    predicted, tie = predict_pairwise_winner(0.5, 0.5, "a", "b")
    assert predicted is None
    assert tie is True


def test_predict_pairwise_winner_missing_score_is_not_tie():
    predicted, tie = predict_pairwise_winner(None, 0.4, "a", "b")
    assert predicted is None
    assert tie is False


def test_predict_pairwise_winner_left():
    predicted, tie = predict_pairwise_winner(0.7, 0.2, "a", "b")
    assert predicted == "a"
    assert tie is False


def test_basic_ranking_metrics():
    assert reciprocal_rank([0, 1, 0]) == 0.5
    assert ndcg_at_k([1, 0, 0], 3) == 1.0
