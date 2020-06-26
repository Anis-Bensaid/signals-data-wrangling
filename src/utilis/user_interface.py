import easygui


def get_from_input(text, possible_values):
    ask = True
    while ask:
        val = input(text)
        ask = not(val in possible_values)
    return val


def get_path(msg=None, title=None, default='*', filetypes=None, multiple=False, to_list=False):
    path = ''
    while path == '':
        path = easygui.fileopenbox(msg=msg, title=title, default=default, filetypes=filetypes, multiple=multiple)
        if to_list and not isinstance(path, list):
            return [path]
    return path


def get_dir(msg=None, title=None, default='*'):
    path = ''
    while path == '':
        path = easygui.diropenbox(msg=msg, title=title, default=default)
    return path
