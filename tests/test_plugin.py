class TestPlugin:
    def test_score(self, mocker) -> None:
        admin = "admin1@example.org"
        user = "user1@example.org"
        mocker.bot.add_admin(admin)

        msg = mocker.get_one_reply("/score", addr=admin)
        assert "0" in msg.text
        msg = mocker.get_one_reply(f"/score {user}")
        assert "0" in msg.text

        mocker.get_one_reply(f"{user} +10", addr=admin)

        msg = mocker.get_one_reply(f"/score {user}")
        assert "10" in msg.text

        mocker.get_one_reply(f"{admin} +4", addr=user)

        msg = mocker.get_one_reply(f"/score", addr=admin)
        assert "4" in msg.text

    def test_filter(self, mocker) -> None:
        user = "user1@example.org"
        admin = "admin1@example.org"
        mocker.bot.add_admin(admin)

        quote = mocker.make_incoming_message(addr=user, group="mockgroup")

        msg = mocker.get_one_reply("+1", addr=admin, quote=quote, group=quote.chat)
        assert "1" in msg.text
        msg = mocker.get_one_reply("+4", addr=admin, quote=quote, group=quote.chat)
        assert "5" in msg.text
        msg = mocker.get_one_reply("-6", addr=admin, quote=quote, group=quote.chat)
        assert "-1" in msg.text

        msg = mocker.get_one_reply(f"{user} +10", addr=admin)
        assert "9" in msg.text
        msg = mocker.get_one_reply(f"{user} -4", addr=admin)
        assert "5" in msg.text
        msgs = mocker.get_replies(f"{admin} -1", addr=user)
        assert not msgs
        msg = mocker.get_one_reply(f"{admin} +1", addr=user)
        assert "1" in msg.text
        assert "4" in msg.text

        msg = mocker.get_one_reply(f"{admin} +100", addr=user)
        assert "❌" in msg.text
