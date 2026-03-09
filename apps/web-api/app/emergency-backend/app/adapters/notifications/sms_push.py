from .dispatcher import Notifier

class SMSPushNotifier(Notifier):
    def __init__(self, provider_key: str | None = None):
        self.provider_key = provider_key

    async def send(self, to: str, message: str) -> None:
        # TODO: integrate Twilio/FCM/etc.
        pass
