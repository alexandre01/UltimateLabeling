from .palettes import dark_palette, light_palette


class Theme:
    LIGHT = "light"
    DARK = "dark"

    @staticmethod
    def get_palette(theme):
        if theme == Theme.DARK:
            return dark_palette()
        elif theme == Theme.LIGHT:
            return light_palette()

        raise ValueError("No palette named {}".format(theme))
