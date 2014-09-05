from functools import wraps, update_wrapper
import inspect

from django.conf import settings

"""
This is an incremental project to remove settings dependencies from Django
libraries so that Django core libraries can be imported without a settings
file or initialization.
"""

_OVERWRITE_SENTINEL = -997
_NEVER_USE_SETTINGS = False

def never_use_settings(nevermind=True):
    _NEVER_USE_SETTINGS = nevermind

class SettingDetails():
    def __init__(self, setting, setting_details, arg_names):
        self.setting = setting
        setting_list = (list(setting_details)
                        if isinstance(setting_details, (list, tuple))
                        else [setting_details])
        self.arg = setting_list[0]
        self.fallback_trigger = (len(setting_list) > 1 and setting_list[1] !=  _OVERWRITE_SENTINEL)
        if self.fallback_trigger:
            self.fallback_trigger_value = setting_list[1]

        try:
            self.index = arg_names.index(self.arg)
        except ValueError:
            self.index = None

    def __repr__(self):
        return str([self.setting, self.index, getattr(self, 'fallback_trigger_value', 'no fallback')])


def uses_settings(setting_name_or_dict, kw_arg=None, fallback_trigger_value=_OVERWRITE_SENTINEL):
    """
    Utility decorator to assist in incrementally removing settings dependencies
    from functions and methods in django core (and, if useful, django apps)

    :param setting_name_or_dict: setting attribute, e.g. 'USE_TZ'.  
                  Alternatively, you can send in a dict like {'USE_TZ': ['use_tz', None]}
                  where the None value is an optionally set fallback_trigger_value per setting key
    :param kw_arg: function parameter that can be used instead of the setting
    :param fallback_trigger_value: In some cases, explicitly setting the parameter
                  should still use the settings attribute, especially when
                  there was an existing required parameter

    The typical use case is a an old function/method looks like:
        def foobar(a, b, c=None):
            if getattr(settings, 'FOO_ENABLE_C', False):
                do_something(c)
            ...
    This decorator makes it easy to remove the need for a django settings import.
    You would modify this function above to something like:
        @uses_settings('FOO_ENABLE_C', 'enable_c')
        def foobar(a, b, c=None, enable_c=False):
            if enable_c:
                do_something(c)
            ...
    which will allow you to import foobar's module without settings needing
    to be run just to enable whatever 'c' does.
    The change above might be considered a 'lazy' api change -- just adding an 
    argument and moving on.  However, since foobar() already has a 'c' parameter
    maybe c=None is pretty much the same as FOO_ENABLE_C=False.  In that case,
    we would change the code to something like:
        @uses_settings('FOO_ENABLE_C', 'c', fallback_trigger_value=None)
        def foobar(a, b, c=None):
            if c is not None:
                do_something(c)
            ...
    This is a slightly cleaner api going forward.
    The last setting for fallback_trigger_value, handles a sublte case.
    With the @uses_setting decorator, calling foobar(1, 2) will
    result in c being set to getattr(settings, 'FOO_ENABLE', None)
    because c is not set explicitly as an argument.  If we had not
    included the fallback_trigger_value, then foobar(1, 2, c=None)
    would *keep* c=None, because c is set explicitly.

    However, with some of django's APIs, setting, e.g. c=None is meant
    to signal that the function should use the setting.  This is what
    fallback_trigger_value is for.  If the argument is set explicitly to
    a certain value, then that should *also* trigger using settings

    Some functions/methods have more than one setting and you want to
    map mutliple settings to arguments.  In that case, stacking will
    not work for obscure and frustrating python decorator context issues
    WRONG:
        @uses_settings('FOO', 'foo')
        @uses_settings('BAR', 'bar', False)
        def abc(foo=None, bar=False):
            ...
    Instead, you can send @uses_settings a dictionary like so:
    RIGHT:
        @uses_settings({'FOO': 'foo',
                        'BAR': ['bar', False]})
        def abc(foo=None, bar=False):
    """
    def _dec(func):
        if _NEVER_USE_SETTINGS:
            return func
        setting_map = []
        arg_names = inspect.getargspec(func).args
        if isinstance(setting_name_or_dict, dict):
            for setting_name, v in setting_name_or_dict.items():
                details = SettingDetails(setting_name, v, arg_names)
                setting_map.append(details)
        else: #it should be a string
            if kw_arg is None:
                raise TypeError("required kw_arg argument")
            setting_map.append(SettingDetails(
                    setting_name_or_dict,
                    [kw_arg, fallback_trigger_value],
                    arg_names))

        def _wrapper(*args, **kwargs):
            args = list(args) #if tuple, make it writable
            args_len = len(args)
            for s in setting_map:
                if s.index is not None and s.index < args_len:
                    if s.fallback_trigger and s.fallback_trigger_value == args[s.index]:
                        args[s.index] = getattr(settings, s.setting, s.fallback_trigger_value)
                elif (not kwargs.has_key(s.arg) \
                          or (s.fallback_trigger and kwargs[s.arg] == s.fallback_trigger_value)) \
                          and hasattr(settings, s.setting):
                    kwargs[s.arg] = getattr(settings, s.setting)

            return func(*args, **kwargs)
        update_wrapper(_wrapper, func)
        return _wrapper
    return _dec

