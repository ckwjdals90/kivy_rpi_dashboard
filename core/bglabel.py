from kivy.uix.label import Label
from kivy.properties import ListProperty
from kivy.uix.behaviors import ButtonBehavior


class BGLabel(Label):
    # Custom widget to facilitate the ability to set background colour
    # to a label via the "bgcolour" property
    bgcolour = ListProperty([0, 0, 0, 0])

    def __init__(self, **kwargs):
        super().__init__()


class BGLabelButton(ButtonBehavior, BGLabel):
    # Add button behaviour to the BGLabel widget
    pass