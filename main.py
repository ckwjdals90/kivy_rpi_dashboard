import imp
import os
# import sys
import json

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.lang import Builder
from kivy.logger import Logger

from core.failedscreen import FailedScreen
from core.getplugins import getPlugins

# Set the current working directory
# os.chdir(os.path.diename(os.path.abspath(sys.argv[0])))


class InfoScreen(FloatLayout):
    # Flag for determining whether screen is locked or not
    locked = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.scrmgr = ObjectProperty(None)

        super().__init__()

        # Get our list of available plugins
        plugins = kwargs["plugins"]

        # We need a list to hold the names of the enabled screens
        self.availablescreens = []

        # and an index so we can loop through them
        self.index = 0

        # We want to handle failures gracefully so set up some variables
        # variable to hold the FiulScreen object (if needed)
        self.failscreen = None

        # Empty lists to track varous failures
        dep_failure = []
        scr_failure = []

        # Create a reference to the screenmanager instance
        # self.scrmgr = self.ids.iscreenmgr

        # Loop over plugins
        for p in plugins:
            # Set up a tuple to store list of unmet dependencies
            plugin_dep = (p["name"], [])

            # Until we hit a failure, there are no unmet dependencies
            unmet = False

            # Loop over dependencies and test if they exist
            for dep in p["dependencies"]:
                try:
                    imp.find_module(dep)
                except ImportError:
                    # We've got at least one unmet dependency for this screen
                    unmet = True
                    plugin_dep[1].append(dep)
                    Logger.error("Unmet dependencies "
                                 "for {} screen. Skipping..."
                                 .format(p["name"]))

            # Can we use the screen?
            if unmet:
                # Add the tupe to our list of unmet dependencies
                dep_failure.append(plugin_dep)

            # No unmet dependencies so let's try to load the screen
            else:
                try:
                    plugin = imp.load_module("screen", *p["info"])
                    screen = getattr(plugin, p["screen"])
                    self.scrmgr.add_widget(screen(name=p["name"],
                                                  master=self,
                                                  params=p["params"]))
                    Logger.info("Screen: {} loaded.".format(p["name"]))

                # Uh oh, something went wrong...
                except Exception as e:
                    # Add the screen name and error message to out list
                    Logger.error("Could not import "
                                 "{} screen. Skipping...".format(p["name"]))
                    scr_failure.append(p["name"], repr(e))

                else:
                    # We can add the screen to out list of available screens
                    self.availablescreens.append(p["name"])

        # if we've got any failure then let's notify the user
        if dep_failure or scr_failure:
            # Create the FailedScreen instance
            self.failscreen = FailedScreen(dep=dep_failure,
                                           failed=scr_failure,
                                           name="FAILEDSCREENS")

            # Add it to our screen manager and make sure it's the first screen
            # the user sees
            self.scrmgr.add_widget(self.failscreen)
            self.scrmgr.current = "FAILEDSCREENS"

    def toggle_lock(self, locked=None):
        if locked is None:
            self.locked = not self.locked
        else:
            self.locked = bool(locked)

    def reload_screen(self, screen):
        # Remove the old screen
        self.remove_screen(screen)

        # and add it again
        self.add_screen(screen)

    def add_screen(self, screenname):

        # Get the info we need to import this screen
        foundscreen = [p for p in getPlugins() if p["name"] == screenname]

        # Check we've found a screen and it's not already running
        if foundscreen and screenname not in self.availablescreens:

            # Get the details for the screen
            p = foundscreen[0]

            # Inport it
            plugin = imp.load_module("screen", *p["info"])

            # Get the reference to the screen class
            screen = getattr(plugin, p["screen"])

            # Add the KV file to the builder
            Builder.load_file(p["kvpath"])

            # Add the screen
            self.scrmgr.add_widget(screen(name=p["name"],
                                          master=self,
                                          params=p["params"]))

            # Add to our list of available screens
            self.availablescreens.append(screenname)

            # Active screen
            self.switch_to(screenname)

        elif screenname in self.availablescreens:

            # This shouldn't happen but we need this to prevent duplicates
            self.reload_screen(screenname)

    def remove_screen(self, screenname):

        # Get the list of screens
        foundscreen = [p for p in getPlugins(inactive=True)
                       if p["name"] == screenname]

        # Loop over list of available screens
        while screenname in self.availablescreens:

            # Remove sreen from list of available screens
            self.availablescreens.remove(screenname)

            # Change the display to the next screen
            self.next_screen()

            # Find the screen in the screen manager
            c = self.scrmgr.get_screen(screenname)

            # Call its "unload" method:
            if hasattr(c, "unload"):
                c.unload()

            # Delete the screen
            self.scrmgr.remove_widget(c)
            del c

        try:
            # Remove the KV file from our builder
            Builder.unload_file(foundscreen[0]["kvpath"])
        except IndexError:
            pass

    def next_screen(self, rev=False):
        if not self.locked:
            if rev:
                self.scrmgr.transition.direction = "right"
                inc = -1
            else:
                self.scrmgr.transition = "left"
                inc = -1
            self.index = (self.index + inc) % len(self.availablescreens)
            self.scrmgr.current = self.availablescreens[self.index]

    def switch_to(self, screen):

        if screen in self.availablescreens:

            # Activate the screen
            self.scrmgr.current = screen

            # Update the screen index
            self.index = self.availablescreens.index(screen)


class InfoScreenApp(App):
    base = None

    def build(self):
        # Window size is hardcoded for resolution of official Raspberry Pi
        # display. Can be altered but plugins may not display correctly.
        Window.size = (800, 480)
        self.base = InfoScreen(plugins=plugins)
        return self.base


if __name__ == "__main__":
    # Load our config
    with open("config.json", "r") as cfg_file:
        config = json.load(cfg_file)

    # Get a list of installed plugins
    plugins = getPlugins()

    # Get the base KV language file for the InfoScreen app.
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

    if web.get("enagles") and web_enabled:

        # Start our webserver
        webport = web.get("webport", 8088)
        apiport = web.get("apiport", 8089)
        debug = web.get("debug", False)
        start_web_server(os.path.dirname(os.path.abspath(__file__)),
                         webport,
                         apiport,
                         debug)

    # Good to go. Let's start the app
    InfoScreenApp().run()
