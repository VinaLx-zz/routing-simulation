import wx
import os
import json
import wx.lib.buttons as wxButton
from routing import router
from routing import config
from routing import manager


alg = {
    "DV": config.Algorithm.DV,
    "LS": config.Algorithm.LS,
    "LS_CENTRALIZE": config.Algorithm.LS_CENTRALIZE,
    "LS_CONTROL": config.Algorithm.LS_CONTROL
}


class ConfigFrame(wx.Frame):
    def __init__(self, parent=None, id=-1, UpdateUI=None):
        wx.Frame.__init__(self, parent, id, title='Configure Router', size=(300, 120), pos=(500, 300))

        self.help_info = None
        self.UpdateUI = UpdateUI
        self.init_UI()

    def init_UI(self):
        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.help_info = wx.StaticText(panel, -1, "Please config the router!", style=wx.ALIGN_CENTER)
        self.help_info.SetForegroundColour('#0a74f7')
        vbox.Add(self.help_info, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 20)

        button_config = wxButton.GenButton(panel, -1, 'Configure', style=wx.BORDER_NONE)
        button_config.SetBackgroundColour('#0a74f7')
        button_config.SetForegroundColour('white')

        vbox.Add(button_config, 0, wx.ALIGN_CENTER_HORIZONTAL)
        panel.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.config, button_config)

    def config(self, _):
        wildcard = "Text Files (*.json)|*.json"
        dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), "", wildcard)

        if dlg.ShowModal() == wx.ID_OK:
            f = open(dlg.GetPath(), 'r')

            with f:
                data = f.read()
                _config = json.loads(data)

                try:
                    self._validate_init(_config)
                    self.UpdateUI(1)
                except Exception as err:
                    wx.MessageBox(err, "Error", wx.OK | wx.ICON_ERROR)
                    dlg.Destroy()
        else:
            dlg.Destroy()

    def _validate_init(self, _config):
        try:
            hns_addr = config.Address(_config['hns_ip'], _config['hns_port'])
            self_addr = config.Address(_config['ip'], _config['port'])
            print(alg[_config['algorithm']])
            c = config.Config(algorithm=alg[_config['algorithm']],
                              hostname=_config['hostname'],
                              self_addr=self_addr,
                              hns_addr=hns_addr,
                              dead_timeout=_config['dead_timeout'],
                              update_interval=_config['update_interval'],
                              controller_hostname=_config['controller_hostname'])
            _router = router.Router(c)
            for each in _config['neighbors']:
                _router.update_neighbor(each['hostname'], each['cost'])
            manager.init_router(_router)
        except Exception as err:
            raise err
