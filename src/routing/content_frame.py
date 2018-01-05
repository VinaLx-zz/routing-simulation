import matplotlib

matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import wx
from routing import io, manager
import sys
import os


class ContentFrame(wx.Frame):
    def __init__(self, parent=None, id=-1, UpdateUI=None):
        self.router = manager.router
        wx.Frame.__init__(self,
                          parent,
                          id,
                          size=(700, 600),
                          title="Router-{}".format(self.router.hostname),
                          pos=(-1, -1))
        self.hostnames = []
        self.neighbor = []
        self._update_hostnames()
        self._update_neighbor()
        self.hostname_choice = None
        self.data_text = None
        self.message_text = None
        self.log_text = None

        self.UpdateUI = UpdateUI
        self.init_UI()
        io.init(self)

    def init_UI(self):
        self.init_main()
        self.init_menu()

    def init_main(self):
        """
        Init Main Frame
        :return:
        """
        panel = wx.Panel(self)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        fgs = wx.FlexGridSizer(5, 2, 10, 10)

        hostname_label = wx.StaticText(panel, label="Hostname:")
        self.hostname_choice = wx.ComboBox(panel, choices=self.hostnames, style=wx.CB_READONLY | wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.update_hostnames_handler, self.hostname_choice)

        data_label = wx.StaticText(panel, label="Data:")
        self.data_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE)

        send_btn = wx.Button(panel, label="Send")
        self.Bind(wx.EVT_BUTTON, self._send_data_handler, send_btn)

        clear_btn = wx.Button(panel, label="Clear")
        self.Bind(wx.EVT_BUTTON, self._clear_handler, clear_btn)

        message = wx.StaticText(panel, label="Message")
        self.message_text = wx.TextCtrl(panel, value="", style=wx.TE_READONLY | wx.TE_MULTILINE)

        log = wx.StaticText(panel, label="Log")
        self.log_text = wx.TextCtrl(panel, value="", style=wx.TE_READONLY | wx.TE_MULTILINE)

        fgs.AddMany(
            [hostname_label, (self.hostname_choice, 1, wx.EXPAND), (data_label, 1, wx.EXPAND),
             (self.data_text, 1, wx.EXPAND),
             (clear_btn, 1, wx.EXPAND), (send_btn, 1, wx.EXPAND), (message, 1, wx.EXPAND),
             (self.message_text, 1, wx.EXPAND),
             (log, 1, wx.EXPAND), (self.log_text, 1, wx.EXPAND)])

        fgs.AddGrowableRow(1, 1)
        fgs.AddGrowableRow(3, 1)
        fgs.AddGrowableRow(4, 1)
        fgs.AddGrowableCol(1, 1)

        hbox.Add(fgs, proportion=2, flag=wx.ALL | wx.EXPAND, border=15)
        panel.SetSizer(hbox)

    def init_menu(self):
        menu_bar = wx.MenuBar()

        file_menu = wx.Menu()

        save_message = wx.MenuItem(file_menu, wx.ID_INFO, text="Save Meesage", kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._save_message_handler, save_message)
        file_menu.Append(save_message)

        save_log = wx.MenuItem(file_menu, wx.ID_FILE, text="Save Log", kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._save_log_handler, save_log)
        file_menu.Append(save_log)

        close = wx.MenuItem(file_menu, wx.ID_CLOSE, text='&Quit\tCtrl+Q')
        self.Bind(wx.EVT_MENU, self._close_handler, close)
        file_menu.Append(close)

        menu_bar.Append(file_menu, "&File")

        config_menu = wx.Menu()

        add_neighbor_item = wx.MenuItem(config_menu, wx.ID_ADD, text="Add New Neighbor", kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._add_neighbor_item_handler, add_neighbor_item)
        config_menu.Append(add_neighbor_item)

        remove_neighbor_item = wx.MenuItem(config_menu, wx.ID_REMOVE, text="Remove Neighbor", kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._remove_neighbor_item_handler, remove_neighbor_item)
        config_menu.Append(remove_neighbor_item)

        menu_bar.Append(config_menu, "&Neighbor")

        display_menu = wx.Menu()

        show_routing_table = wx.MenuItem(display_menu, wx.ID_DEFAULT, text="Show Routing Table", kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._show_routing_table_handler, show_routing_table)
        display_menu.Append(show_routing_table)

        show_neighbor_table = wx.MenuItem(display_menu, wx.ID_DEFAULT, text="Show Neighbor Table", kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._show_neigbor_table_handler, show_neighbor_table)
        display_menu.Append(show_neighbor_table)

        menu_bar.Append(display_menu, "&Display")

        self.SetMenuBar(menu_bar)
        self.Center()

    def update_hostnames_handler(self, _):
        self._update_hostnames()
        self.hostname_choice.SetItems(self.hostnames)

    def listen_message_event(self, data):
        wx.CallAfter(self.message_text.AppendText, data)

    def listen_log_event(self, data):
        wx.CallAfter(self.log_text.AppendText, data)

    def _save_message_handler(self, _):
        dlg = wx.FileDialog(self, "Create a file", os.getcwd(), "message.txt", style=wx.FD_SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            try:
                file = open(dlg.GetPath(), 'a')
                file.write(self.message_text.GetValue())
                wx.MessageBox("Save message file succeed!", "Succeed", wx.OK | wx.ICON_INFORMATION)
            except Exception as err:
                wx.MessageBox(err, "Error", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()

    def _save_log_handler(self, _):
        dlg = wx.FileDialog(self, "Create a file", os.getcwd(), "log.txt", style=wx.FD_SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            try:
                file = open(dlg.GetPath(), 'a')
                file.write(self.log_text.GetValue())
                wx.MessageBox("Save message file succeed!", "Succeed", wx.OK | wx.ICON_INFORMATION)
            except Exception as err:
                wx.MessageBox(err, "Error", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()

    def _close_handler(self, _):
        sys.exit(0)

    def _add_neighbor_item_handler(self, _):
        myDialog = MyDialog(self, "Add Neighbor")
        myDialog.ShowModal()

    def _remove_neighbor_item_handler(self, _):
        self._update_neighbor()
        dlg = wx.SingleChoiceDialog(self, "Which hostname you want to remove", "Remove neighbor", self.neighbor)

        if dlg.ShowModal() == wx.ID_OK:
            self.router.remove_neighbor(dlg.GetStringSelection())
        dlg.Destroy()

    def _send_data_handler(self, _):
        if self.hostname_choice.GetStringSelection() == '' or self.data_text.GetValue() == '':
            wx.MessageBox("Please enter the receiver's hostname and data.", "Error", wx.OK | wx.ICON_ERROR)
        else:
            self.router.send(self.hostname_choice.GetStringSelection(), self.data_text.GetValue())
            self.data_text.Clear()

    def _clear_handler(self, _):
        self.data_text.Clear()

    def _update_hostnames(self):
        self.hostnames = self.router.get_alive()
        self.hostnames.remove(self.router.hostname)

    def _show_routing_table_handler(self, _):
        dlg = DisplayRoutingTableDialog(self)
        dlg.ShowModal()

    def _show_neigbor_table_handler(self, _):
        dlg = DisplayNeighborTableDialog(self)
        dlg.ShowModal()

    def _update_neighbor(self):
        self.neighbor = []
        neighbor_table = self.router.get_neighbor_table()
        for key in neighbor_table:
            self.neighbor.append(key)


class MyDialog(wx.Dialog):
    def __init__(self, parent, text):
        wx.Dialog.__init__(self, parent, -1, text, size=(400, 250))
        self.hostname_text = None
        self.cost_text = None
        self.init_UI()

    def init_UI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        info = wx.StaticBox(panel, -1, 'Information:')
        nmSizer = wx.StaticBoxSizer(info, wx.VERTICAL)

        nmbox = wx.BoxSizer(wx.HORIZONTAL)
        hostname = wx.StaticText(panel, -1, "Hostname:")
        nmbox.Add(hostname, 0, wx.ALL | wx.CENTER, 5)

        self.hostname_text = wx.TextCtrl(panel, -1, style=wx.ALIGN_LEFT)
        self.cost_text = wx.TextCtrl(panel, -1, style=wx.ALIGN_LEFT)
        cost = wx.StaticText(panel, -1, "Cost:")

        nmbox.Add(self.hostname_text, 0, wx.ALL | wx.CENTER, 5)
        nmbox.Add(cost, 0, wx.ALL | wx.CENTER, 5)
        nmbox.Add(self.cost_text, 0, wx.ALL | wx.CENTER, 5)
        nmSizer.Add(nmbox, 0, wx.ALL | wx.CENTER, 10)

        sbox = wx.StaticBox(panel, -1, 'Control:')
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(panel, -1, 'ok')
        self.Bind(wx.EVT_BUTTON, self._ok_handler, okButton)

        hbox.Add(okButton, 0, wx.ALL | wx.LEFT, 10)
        cancelButton = wx.Button(panel, -1, 'cancel')
        self.Bind(wx.EVT_BUTTON, self._close_handler, cancelButton)

        hbox.Add(cancelButton, 0, wx.ALL | wx.LEFT, 10)
        sboxSizer.Add(hbox, 0, wx.ALL | wx.LEFT, 10)
        vbox.Add(nmSizer, 0, wx.ALL | wx.CENTER, 5)
        vbox.Add(sboxSizer, 0, wx.ALL | wx.CENTER, 5)
        panel.SetSizer(vbox)
        self.Centre()
        panel.Fit()

    def _ok_handler(self, _):
        manager.router.update_neighbor(self.hostname_text.GetValue(), self.cost_text.GetValue())
        self.EndModal(wx.ID_CANCEL)

    def _close_handler(self, _):
        self.EndModal(wx.ID_CANCEL)


class DisplayRoutingTableDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Routing Table", size=(400, 300))
        self.init_UI()

    def init_UI(self):
        panel = wx.Panel(self)
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)

        collabel = ("Destination", "Next Hop", "Cost")
        self.axes.axis('off')

        the_table = self.axes.table(cellText=self._get_routint_table(),
                                    colLabels=collabel,
                                    cellLoc='center',
                                    loc='center',
                                    alpha=1)
        the_table.set_fontsize(15)
        the_table.scale(1, 3)

        self.canvas = FigureCanvas(panel, -1, self.figure)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Center()
        panel.Fit()

    def _get_routint_table(self):
        routing_table = manager.router.get_routing_table()
        matrix = []
        for each in routing_table:
            matrix.append([each, routing_table[each]['next'], routing_table[each]['cost']])
        return matrix


class DisplayNeighborTableDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Neighbor Table", size=(400, 300))
        self.init_UI()

    def init_UI(self):
        panel = wx.Panel(self)
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)

        collabel = ("Destination", "Cost")
        self.axes.axis('off')

        the_table = self.axes.table(cellText=self._get_neighbor_table(),
                                    colLabels=collabel,
                                    cellLoc='center',
                                    loc='center',
                                    alpha=1)
        the_table.set_fontsize(15)
        the_table.scale(1, 3)

        self.canvas = FigureCanvas(panel, -1, self.figure)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Center()
        panel.Fit()

    def _get_neighbor_table(self):
        routing_table = manager.router.get_neighbor_table()
        matrix = []
        for key in routing_table:
            matrix.append([key, routing_table[key]])
        if len(matrix) == 0:
            matrix.append(["----", "----"])
        return matrix
