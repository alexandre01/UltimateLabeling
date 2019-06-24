from .palettes import dark_palette, light_palette, dark_image_bg, light_image_bg


class Theme:
    LIGHT = "light"
    DARK = "dark"

    @staticmethod
    def get_palette(theme):
        if theme == Theme.DARK:
            return dark_palette()
        elif theme == Theme.LIGHT:
            return light_palette()

        raise ValueError("No theme named {}".format(theme))

    @staticmethod
    def get_image_bg(theme):
        if theme == Theme.DARK:
            return dark_image_bg
        elif theme == Theme.LIGHT:
            return light_image_bg

        raise ValueError("No theme named {}".format(theme))
