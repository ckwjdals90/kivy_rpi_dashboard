import os
import sys
import json

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.logger import Logger

from core.getplugins import getPlugins
from core.dashboard import Dashboard

# Set the current working directory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))


class DashboardApp(App):
    base = None

    def build(self):
        # Window size is hardcoded for resolution of official Raspberry Pi
        # display. Can be altered but plugins may not display correctly.
        Window.size = (800, 480)
        self.base = Dashboard(plugins=plugins)
        return self.base


if __name__ == "__main__":
    # Load our config
    with open("config.json", "r") as cfg_file:
        config = json.load(cfg_file)

    # Get a list of installed plugins
    plugins = getPlugins()

    # Get the base KV language file for the Dashboard app.
    kv_text = "".join(open("base.kv").readlines()) + "\n"

    # Load the master KV file
    Builder.load_file("base.kv")

    # Loop over the plugins
    for p in plugins:

        # and add their custom kv files to create one master KV file
        Builder.load_file(p["kvpath"])

    # Do we want a webserver?
    web = config.get("webserver", dict())

    # Is bottle installed?
    try:
        # I don't like doing it this way (all imports shuld be at the top)
        # but I'm feeling lazy
        from core.webinterface import start_web_server
        web_enabled = True

    except ImportError:
        Logger.warning("Bottle module not found. Cannot start webserver.")
        web_enabled = False

    if web.get("enabled") and web_enabled:

        # Start our webserver
        webport = web.get("webport", 8088)
        apiport = web.get("apiport", 8089)
        debug = web.get("debug", False)
        start_web_server(os.path.dirname(os.path.abspath(__file__)),
                         webport,
                         apiport,
                         debug)

    # Good to go | Let's start the app
    DashboardApp().run()
