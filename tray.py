#!/usr/bin/env python3
import os
import subprocess
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3

ICON_OFF = "/home/user/wireguardGuiV2/iconWireguard.png"
ICON_ON = "/home/user/wireguardGuiV2/iconWireguardON.png"
CONFIG_FILE = os.path.expanduser("~/.vpn_interface")
mainInterface = "wg2"
indicator = None  

def load_last_interface():
    global mainInterface
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            mainInterface = f.read().strip()

def save_current_interface():
    with open(CONFIG_FILE, 'w') as f:
        f.write(mainInterface)

def show_notification(title, message, icon_path=None):
    if icon_path is None:
        icon_path = ICON_OFF
    subprocess.Popen(["notify-send", "-i", icon_path, title, message])

def connect_vpn():
    global mainInterface
    try:
        subprocess.run(["wg-quick", "up", mainInterface], check=True)
        indicator.set_icon(ICON_ON)
        indicator.set_label("VPN включен", "")
        show_notification("Wireguard", f"VPN подключён: {mainInterface}", ICON_ON)
        return True
    except subprocess.CalledProcessError:
        indicator.set_icon(ICON_OFF)
        show_notification("Ошибка", "Ошибка подключения VPN", ICON_OFF)
        return False

def disconnect_vpn():
    global mainInterface
    try:
        subprocess.run(["wg-quick", "down", mainInterface], check=True)
        indicator.set_icon(ICON_OFF)
        indicator.set_label("VPN выключен", "")
        show_notification("Wireguard", f"VPN отключён: {mainInterface}", ICON_OFF)
        return True
    except subprocess.CalledProcessError:
        show_notification("Ошибка", "Ошибка отключения VPN", ICON_OFF)
        return False

def on_toggle_vpn(check_item):
    if check_item.get_active():
        if not connect_vpn():
            check_item.set_active(False)
    else:
        if not disconnect_vpn():
            check_item.set_active(True)

def on_interface_selected(menu_item, interface_name):
    global mainInterface
    mainInterface = interface_name
    save_current_interface()
    show_notification("Wireguard", f"Выбран интерфейс: {mainInterface}")
    print(f"Интерфейс выбран из меню: {mainInterface}")

def on_add_new_interface(_):
    dialog = Gtk.FileChooserDialog(
        title="Выбор .conf файла.",
        action=Gtk.FileChooserAction.OPEN,
        buttons=(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
    )

    filter_conf = Gtk.FileFilter()
    filter_conf.set_name("WireGuard .conf файлы")
    filter_conf.add_pattern("*.conf")
    dialog.add_filter(filter_conf)

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        path = dialog.get_filename()
        iface_name = os.path.basename(path).replace(".conf", "")
        global mainInterface
        mainInterface = iface_name
        save_current_interface()
        show_notification("Wireguard", f"Добавлен и выбран: {mainInterface}")

    dialog.destroy()

def create_interface_menu():
    menu = Gtk.Menu()
    try:
        files = os.listdir("/etc/wireguard")
        for f in files:
            if f.endswith(".conf"):
                iface = f.replace(".conf", "")
                item = Gtk.MenuItem(label=iface)
                item.connect("activate", on_interface_selected, iface)
                menu.append(item)
    except PermissionError:
        item = Gtk.MenuItem(label="Нет доступа к /etc/wireguard")
        menu.append(item)

    # Добавляем пункт "Добавить новый интерфейс"
    menu.append(Gtk.SeparatorMenuItem())
    add_item = Gtk.MenuItem(label="➕ Добавить новый интерфейс")
    add_item.connect("activate", on_add_new_interface)
    menu.append(add_item)

    menu.show_all()
    return menu

def create_tray():
    global indicator
    indicator = AppIndicator3.Indicator.new(
        "vpn-tray",
        ICON_OFF,
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    indicator.set_label("VPN GUI", "")

    menu = Gtk.Menu()

    vpn_item = Gtk.CheckMenuItem(label="VPN")
    vpn_item.set_active(False)
    vpn_item.connect("toggled", on_toggle_vpn)
    menu.append(vpn_item)

    iface_item = Gtk.MenuItem(label="Выбрать интерфейс")
    iface_submenu = create_interface_menu()
    iface_item.set_submenu(iface_submenu)
    menu.append(iface_item)

    quit_item = Gtk.MenuItem(label="Выход")
    quit_item.connect("activate", Gtk.main_quit)
    menu.append(quit_item)

    menu.show_all()
    indicator.set_menu(menu)

if __name__ == "__main__":
    load_last_interface()
    create_tray()
    Gtk.main()
