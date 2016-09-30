import sublime
import json
import os.path
from sublime_plugin import TextCommand
from sublime_plugin import EventListener


def plugin_loaded():
    # update settings.
    SettingStore().update_settings()

    # update config.
    SettingStore().update_config()

    # add settings modified listener.
    SettingStore().settings.add_on_change(
        'reload', SettingStore().update_settings)


class TabControlListener(EventListener):

    def on_window_command(self, window, command, option):

        if (command == 'toggle_tabs'
                and not self._toggle_tabs(command, option)):
            return ('None')
        elif command == 'new_window':
            self._new_window()

    def _new_window(self):
        TabStatusStore().active_window_status = TabStatusStore().show_tab_status

    def _toggle_tabs(self, command, option):
        if (option == 'sidebar_separator'
                and SettingStore().get_auto_hide_option()
                and TabStatusStore().show_tab_status):
            # set tab hide flag.
            TabStatusStore().show_tab_status = False
            return True
        elif not SettingStore().get_auto_hide_option():
            TabStatusStore().toggle_show_tab_status()
            return True
        elif SettingStore().get_auto_hide_option():
            return False
        return False


class TabStatusStore():
    # singleton instance.
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(TabStatusStore, cls).__new__(
                cls, *args, **kwargs)

            # show_tabs parameter from Session.sublime_session.
            cls.__show_tab_status = {}

            # just before active window status.
            cls.__active_window_status = None

        return cls.__instance

    @property
    def active_window_status(self):
        return self.__active_window_status

    @active_window_status.setter
    def active_window_status(self, status):
        self.__active_window_status = status

    @property
    def show_tab_status(self):
        # get active window_id
        window_id = self._get_active_window_id()

        if not window_id in self.__show_tab_status:
            # set just before active window id.
            self.__show_tab_status[window_id] = self.__active_window_status

        return self.__show_tab_status[window_id]

    @show_tab_status.setter
    def show_tab_status(self, status):
        # set show_tab_status.
        self.__show_tab_status[self._get_active_window_id()] = status

    def toggle_show_tab_status(self):
        self.__show_tab_status[
            self._get_active_window_id()] = not self.show_tab_status

    def _get_active_window_id(self):
        return sublime.active_window().id()


class SettingStore():
    # singleton instance.
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(SettingStore, cls).__new__(
                cls, *args, **kwargs)

            # initial value of the setting file.
            cls.__settings = None

            # initial value of the configuration file.
            cls.__config = None

        return cls.__instance

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, config):
        self.__config = config

    @property
    def settings(self):
        return self.__settings

    @settings.setter
    def settings(self, settings):
        self.__settings = settings

    def update_config(self):
        def _load_config():

            path = sublime.packages_path().replace('Packages', '')

            CONFIG_AUTO = os.path.join(
                os.sep, path, 'Local', 'Auto Save Session.sublime_session')
            CONFIG_SYS = os.path.join(
                os.sep, path, 'Local', 'Session.sublime_session')

            # read preferentially with automatic writing file.
            # get the latest status.
            if os.path.isfile(CONFIG_AUTO):
                return _parse_json(CONFIG_AUTO)
            else:
                return _parse_json(CONFIG_SYS)

        def _parse_json(config_file):
            # parse json from config file.
            opened_file = open(config_file, 'r', encoding="utf8")
            return json.loads(opened_file.read(), strict=False)

        if SettingStore().config is None:
            SettingStore().config = _load_config()

        TabStatusStore().show_tab_status = SettingStore().get_tab_visibility_option()

    def update_settings(self):
        # load settings value from setting file.
        self.settings = sublime.load_settings(
            'sidebar_separator.sublime-settings')

    def get_auto_hide_option(self):
        # return the hide option flag.
        return self.settings.get('auto_tab_hide', False)

    def get_tab_visibility_option(self):
        # return the show_tabs option.
        return self.config['windows'][0]['show_tabs']


class SidebarSeparator(TextCommand):

    def run(self, edit):
        # create separate file.
        self.create_separater()

        # auto tab hide.
        self.hide_tab_bar()

    def create_separater(self):
         # create separate file.
        separate_file = sublime.active_window().new_file()

        # set buffer name.
        separate_file.set_name(self.get_separate_value())

        # set not save as separate file propertie.
        separate_file.set_scratch(True)

        # set read only propertie.
        separate_file.set_read_only(True)

    def hide_tab_bar(self):
        # controlling the tabs when the flag is true.
        if (SettingStore().get_auto_hide_option()
                and TabStatusStore().show_tab_status):

            sublime.active_window().run_command('toggle_tabs', 'sidebar_separator')

    def get_separate_value(self):
        # get separate value and create separater.
        value = SettingStore().settings.get('separate_value', '-')
        count = SettingStore().settings.get('separate_count', 100)

        return value * count
