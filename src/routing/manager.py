from src.routing import contentFrame
from src.routing import configFrame


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
            return configFrame.ConfigFrame(parent=None, id=_type, UpdateUI=self.UpdateUI)
        elif _type == 1:
            return contentFrame.ContentFrame(parent=None, id=_type, UpdateUI=self.UpdateUI)
