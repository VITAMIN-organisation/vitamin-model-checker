"""Model type detection from file content."""

import pytest

from model_checker.models.model_factory import detect_model_type_from_content


@pytest.mark.unit
def test_detect_walletcgs_from_wallets_section():
    content = "Transition\nWallets\ns0: 10 20\n"
    assert detect_model_type_from_content(content) == "WalletCGS"


@pytest.mark.unit
def test_detect_timedcgs_from_clocks_section():
    content = "Transition_With_Costs\nClocks\nx\n"
    assert detect_model_type_from_content(content) == "timedCGS"
