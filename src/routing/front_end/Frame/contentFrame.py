import wx


class ContentFrame(wx.Frame):
    def __init__(self, parent=None, id=-1, UpdateUI=None):
        wx.Frame.__init__(self, parent, id, title="Router", size=(350, 350), pos=(500, 200))

        self.log = ""
        self.UpdateUI = UpdateUI
        self.init_UI()

    def init_UI(self):
        self.init_main()
        self.init_menu()

    def init_main(self):
        panel = wx.Panel(self)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        fgs = wx.FlexGridSizer(4, 2, 10, 10)

        hostname_label = wx.StaticText(panel, label="Hostname:")
        data_label = wx.StaticText(panel, label="Data:")

        hostname_text = wx.TextCtrl(panel)
        data_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE)

        send_btn = wx.Button(panel, label="Ok")
        clear_btn = wx.Button(panel, label="Close")

        log = wx.StaticText(panel, label="Log")
        log_text = wx.TextCtrl(panel, value=self.log, style=wx.TE_READONLY | wx.TE_CENTER)

        fgs.AddMany(
            [hostname_label, (hostname_text, 1, wx.EXPAND), (data_label, 1, wx.EXPAND), (data_text, 1, wx.EXPAND),
             (clear_btn, 1, wx.EXPAND), (send_btn, 1, wx.EXPAND), (log, 1, wx.EXPAND), (log_text, 1, wx.EXPAND)])

        fgs.AddGrowableRow(1, 1)
        fgs.AddGrowableRow(3, 1)
        fgs.AddGrowableCol(1, 1)

        hbox.Add(fgs, proportion=2, flag=wx.ALL | wx.EXPAND, border=15)
        panel.SetSizer(hbox)

    def init_menu(self):
        menu_bar = wx.MenuBar()

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

        menu_bar.Append(config_menu, "&Config")
        menu_bar.Append(display_menu, "&Show")
        self.SetMenuBar(menu_bar)
        self.SetSize((350, 250))
        self.Center()

    def _add_neighbor_item_handler(self, event):
        print("_add_neighbor_handler")

    def _remove_neighbor_item_handler(self, event):
        print("remove_neighbor_item")
