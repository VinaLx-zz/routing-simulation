import wx
from Frame import manager


class MainAPP(wx.App):
    def OnInit(self):
        self.manager = manager.GUIManager(self.update_UI)
        self.frame = self.manager.get_frame(0)
        self.frame.Show()
        return True

    def update_UI(self, type):
        self.frame.Show(False)
        self.frame = self.manager.get_frame(type)
        self.frame.Show(True)


def main():
    app = MainAPP()
    app.MainLoop()


if __name__ == '__main__':
    main()
