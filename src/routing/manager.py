from routing import content_frame
from routing import config_frame

router = None


def init_router(_router):
    global router
    router = _router
    router.run()


class GUIManager:
    def __init__(self, UpdateUI):
        self.UpdateUI = UpdateUI
        self.frameDict = {}

    def get_frame(self, _type):
        frame = self.frameDict.get(_type)

        if frame is None:
            frame = self.create_frame(_type)
            self.frameDict[_type] = frame

        return frame

    def create_frame(self, _type):
        if _type == 0:
            return config_frame.ConfigFrame(parent=None, id=_type,
                                            UpdateUI=self.UpdateUI)
        elif _type == 1:
            return content_frame.ContentFrame(parent=None, id=_type,
                                              UpdateUI=self.UpdateUI)
