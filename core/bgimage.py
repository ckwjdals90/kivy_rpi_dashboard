from kivy.uix.image import Image
from kivy.properties import ListProperty
from kivy.uix.behaviors import ButtonBehavior


class BGImage(Image):
    # Custom widget to facilitate the ability to set background colour
    # to an image via the "bgcolour" property
    bgcolour = ListProperty([0, 0, 0, 0])
    fgcolour = ListProperty([0, 0, 0, 0])

    def __init__(self, **kwargs):
        super().__init__()


class BGImageButton(ButtonBehavior, BGImage):
    # Add button behavior to the BGImage widget
    pass
