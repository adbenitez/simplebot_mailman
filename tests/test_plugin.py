class TestPlugin:
    def test_list(self, mocker) -> None:
        msg = mocker.get_one_reply("/list")
        assert "❌" in msg.text
