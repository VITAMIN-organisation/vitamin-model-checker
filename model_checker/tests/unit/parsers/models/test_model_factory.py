"""Model type detection must use section headers, not raw substrings."""

import pytest

from model_checker.models.model_factory import detect_model_type_from_content


@pytest.mark.unit
class TestDetectModelTypeFromContent:
    def test_wallets_header_selects_wallet_cgs(self):
        content = "Transition\n*\nWallets\ns0:1\n"
        assert detect_model_type_from_content(content) == "WalletCGS"

    def test_incidental_wallets_substring_does_not_select_wallet_cgs(self):
        content = (
            "Transition\n*\nName_State\ns0\nInitial_State\ns0\n"
            "Atomic_propositions\nhasWalletsFlag\nLabelling\n1\nNumber_of_agents\n1\n"
        )
        assert detect_model_type_from_content(content) == "CGS"

    def test_clocks_header_selects_timed_cgs(self):
        content = "Transition\n*\nClocks\nx\n"
        assert detect_model_type_from_content(content) == "timedCGS"

    def test_costs_for_actions_split_header_selects_cost_cgs(self):
        content = "Transition\n*\nCosts_for_actions_split\nAA s0$1\n"
        assert detect_model_type_from_content(content) == "costCGS"

    def test_incidental_costs_substring_does_not_select_cost_cgs(self):
        content = (
            "Transition\n*\nName_State\ns0\nInitial_State\ns0\n"
            "Atomic_propositions\nhasCosts_for_actionsFlag\nLabelling\n1\n"
            "Number_of_agents\n1\n"
        )
        assert detect_model_type_from_content(content) == "CGS"

    def test_preorder_header_selects_bcgs(self):
        content = "Transition\n*\nPreorder\n1\n"
        assert detect_model_type_from_content(content) == "BCGS"
