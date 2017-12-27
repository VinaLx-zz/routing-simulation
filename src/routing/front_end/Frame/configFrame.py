import wx
import os
import wx.lib.buttons as wxButton


class ConfigFrame(wx.Frame):
    def __init__(self, parent=None, id=-1, UpdateUI=None):
        wx.Frame.__init__(self, parent, id, title='Configure Router', size=(300, 120), pos=(500, 200))

        self.help_info = None
        self.UpdateUI = UpdateUI
        self.init_UI()

    def init_UI(self):
        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.help_info = wx.StaticText(panel, -1, "Please config the router!", style=wx.ALIGN_CENTRE)
        self.help_info.SetForegroundColour('#0a74f7')
        vbox.Add(self.help_info, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 20)

        button_config = wxButton.GenButton(panel, -1, 'Configure', style=wx.BORDER_MASK | wx.ALIGN_CENTER)
        button_config.SetBackgroundColour('#0a74f7')
        button_config.SetForegroundColour('white')

        vbox.Add(button_config, 0, wx.ALIGN_CENTER_HORIZONTAL)
        panel.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.config, button_config)

    def config(self, _):
        wildcard = "Text Files (*.txt)|*.txt"
        dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), "", wildcard)

        if dlg.ShowModal() == wx.ID_OK:
            f = open(dlg.GetPath(), 'r')

            with f:
                data = f.read()
                # Handle
                print(data)
                if True:
                    self.UpdateUI(1)
                else:
                    self.help_info.SetLabel("Please use correct config file.")
                    dlg.Destroy()
        else:
            dlg.Destroy()
