from internal.decorations.colors import bcolors


class Decorator:
    def white(self, text):
        return text

    def green(self, text):
        return text

    def blue(self, text):
        return text

    def cyan(self, text):
        return text

    def yellow(self, text):
        return text

    def magenta(self, text):
        return text

    def grey(self, text):
        return text

    def black(self, text):
        return text


class KaliDecoratorNaMinimalkax(Decorator):
    def white(self, text):
        return f"{bcolors.WHITE}{text}{bcolors.ENDC}"

    def green(self, text):
        return f"{bcolors.GREEN}{text}{bcolors.ENDC}"

    def blue(self, text):
        return f"{bcolors.BLUE}{text}{bcolors.ENDC}"

    def cyan(self, text):
        return f"{bcolors.CYAN}{text}{bcolors.ENDC}"

    def yellow(self, text):
        return f"{bcolors.YELLOW}{text}{bcolors.ENDC}"

    def magenta(self, text):
        return f"{bcolors.MAGENTA}{text}{bcolors.ENDC}"

    def grey(self, text):
        return f"{bcolors.GREY}{text}{bcolors.ENDC}"

    def black(self, text):
        return f"{bcolors.BLACK}{text}{bcolors.ENDC}"
