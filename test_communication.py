from communication import SmsSender

class TestableSmsSender(SmsSender):
    def __init__(self):
        super().__init__()
        self._send_called = False

    def send(self, scheduler):
        print("테스트용 send 메서드 실행")
        self._send_called = True

    @property
    def send_called(self):
        return self._send_called