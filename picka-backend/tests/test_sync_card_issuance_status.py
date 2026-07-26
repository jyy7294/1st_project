from scripts.sync_card_issuance_status import resolve_is_issuable


def test_explicit_discontinued_card_is_inactive():
    assert resolve_is_issuable({"is_discon": True}) is False


def test_explicit_non_discontinued_card_is_active_without_event_or_online_only():
    payload = {
        "is_discon": False,
        "only_online": False,
        "event": None,
        "request_yn": False,
    }

    assert resolve_is_issuable(payload) is True


def test_missing_or_invalid_discontinuation_flag_is_unknown():
    assert resolve_is_issuable({}) is None
    assert resolve_is_issuable({"is_discon": "false"}) is None
