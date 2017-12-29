import wx
from src.routing import IO
import sys
import os


class ContentFrame(wx.Frame):
    def __init__(self, parent=None, id=-1, UpdateUI=None):
        wx.Frame.__init__(self, parent, id, title="Router", size=(350, 1000), pos=(500, 200))

        self.hostname_text = None
        self.data_text = None
        self.message_text = None
        self.log_text = None
        self.UpdateUI = UpdateUI
        self.init_UI()
        IO.init(self)

    def init_UI(self):
        self.init_main()
        self.init_menu()

    def init_main(self):
        panel = wx.Panel(self)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        fgs = wx.FlexGridSizer(5, 2, 10, 10)

        hostname_label = wx.StaticText(panel, label="Hostname:")
        data_label = wx.StaticText(panel, label="Data:")

        self.hostname_text = wx.TextCtrl(panel)
        self.data_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE)

        send_btn = wx.Button(panel, label="Ok")

        self.Bind(wx.EVT_BUTTON, self._send_data, send_btn)

        clear_btn = wx.Button(panel, label="Close")
        self.Bind(wx.EVT_BUTTON, self._clear, clear_btn)

        messgae = wx.StaticText(panel, label="Message")
        self.message_text = wx.TextCtrl(panel, value="", style=wx.TE_READONLY | wx.TE_MULTILINE)

        log = wx.StaticText(panel, label="Log")
        self.log_text = wx.TextCtrl(panel, value="", style=wx.TE_READONLY | wx.TE_MULTILINE)

        fgs.AddMany(
            [hostname_label, (self.hostname_text, 1, wx.EXPAND), (data_label, 1, wx.EXPAND),
             (self.data_text, 1, wx.EXPAND),
             (clear_btn, 1, wx.EXPAND), (send_btn, 1, wx.EXPAND), (messgae, 1, wx.EXPAND),
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

        config_menu = wx.Menu()
        edit_submenu = wx.Menu()
        add_neighbor_item = wx.MenuItem(edit_submenu, wx.ID_ADD, text="Add New Neighbor", kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._add_neighbor_item_handler, add_neighbor_item)
        edit_submenu.Append(add_neighbor_item)
        remove_neighbor_item = wx.MenuItem(edit_submenu, wx.ID_REMOVE, text="Remove Neighbor", kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self._remove_neighbor_item_handler, remove_neighbor_item)
        edit_submenu.Append(remove_neighbor_item)
        config_menu.Append(wx.ID_ANY, "Edit", edit_submenu)

        display_menu = wx.Menu()
        show_route_table = wx.MenuItem(display_menu, wx.ID_INFO, text="Show route table", kind=wx.ITEM_NORMAL)
        display_menu.Append(show_route_table)
        show_topo_graph = wx.MenuItem(display_menu, wx.ID_INFO, text="Show topological structure", kind=wx.ITEM_NORMAL)
        display_menu.Append(show_topo_graph)

        menu_bar.Append(file_menu, "&File")
        menu_bar.Append(config_menu, "&Config")
        menu_bar.Append(display_menu, "&Show")
        self.SetMenuBar(menu_bar)
        self.SetSize((350, 250))
        self.Center()

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

    def _close_handler(self, event):
        sys.exit(0)

    def _add_neighbor_item_handler(self, event):
        IO.print_message("_add_neighbor_handler")

    def _remove_neighbor_item_handler(self, event):
        self.add_message("remove_neighbor_item")

    def _send_data(self, event):
        self.add_message("Send Message\n")
        print(self.hostname_text.GetValue())
        print(self.data_text.GetValue())
        wx.MessageBox("This is a Message Box", "Message", wx.OK | wx.ICON_INFORMATION)

    def _clear(self, _):
        self.data_text.Clear()
        self.hostname_text.Clear()

    def add_message(self, message):
        self.message_text.AppendText(message)

    def add_log(self, log):
        self.log_text.AppendText(log)
