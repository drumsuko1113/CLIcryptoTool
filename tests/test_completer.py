"""コマンド補完モジュールのテスト"""
from prompt_toolkit.document import Document
from src.completer import EthCommandCompleter


class TestEthCommandCompleter:
    def setup_method(self):
        self.completer = EthCommandCompleter()

    def _get_completions(self, text):
        doc = Document(text, len(text))
        return list(self.completer.get_completions(doc, None))

    def test_slash_shows_all_commands(self):
        completions = self._get_completions("/")
        names = [c.text for c in completions]
        assert "price" in names
        assert "chart" in names
        assert "help" in names
        assert "readme" in names

    def test_partial_match(self):
        completions = self._get_completions("/pr")
        names = [c.text for c in completions]
        assert "price" in names
        assert "chart" not in names

    def test_alert_subcommands(self):
        completions = self._get_completions("/alert ")
        names = [c.text for c in completions]
        assert "remove" in names
        assert "clear" in names

    def test_readme_sections(self):
        completions = self._get_completions("/readme ")
        names = [c.text for c in completions]
        assert "chart" in names
        assert "indicators" in names
        assert "alert" in names

    def test_no_completions_for_plain_text(self):
        completions = self._get_completions("hello")
        assert len(completions) == 0

    def test_completions_have_descriptions(self):
        completions = self._get_completions("/")
        for c in completions:
            assert c.display_meta_text  # 説明テキストが存在する
