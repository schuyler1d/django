from django.conf import settings
import inspect
"""

This is an incremental project to remove settings dependencies from Django
libraries so that Django core libraries can be imported without a settings
file or initialization

"""

OVERWRITE_SENTINEL = 'FAKE_VALUE'

class SettingDetails():
    def __init__(self, setting, setting_details, arg_names):
        self.setting = setting
        setting_list = (list(setting_details)
                        if isinstance(setting_details, (list, tuple))
                        else [setting_details])
        self.arg = setting_list[0]
        self.overwrite_default = setting_list[1:] or OVERWRITE_SENTINEL
        self.index = arg_names.index(self.arg)

        if self.arg not in arg_names:
            raise ValueError("Decorator keyword argument, "
                             "%s, not in function spec." % self.arg)


def use_setting(setting_name_or_dict, kw_arg=None, overwrite_default=OVERWRITE_SENTINEL):
    """
    Decorator for functions
    :param setting_name_or_dict: setting attribute, e.g. 'USE_TZ'.  
                  Alternatively, you can send in a dict like {'USE_TZ': ['use_tz', None]}
                  where the None value is an optionally set overwrite_default per setting key
    :param kw_arg: function parameter that can be used instead of the setting
    :param overwrite_default: In some cases, explicitly setting the parameter
                  should still use the settings attribute, especially when
                  there was an existing required parameter
    """
    def _dec(func):
        setting_map = {}
        arg_names = inspect.getargspec(func).args
        kw_defaults = inspect.getargspec(func).defaults
        if isinstance(setting_name_or_dict, dict):
            for k,v in setting_name_or_dict.items():
                details = SettingDetails(k, v, arg_names)
                setting_map[details.arg] = details
        else: #it should be a string
            if kw_arg is None:
                raise TypeError("required kw_arg argument")
            setting_map[kw_arg] = SettingDetails(
                setting_name_or_dict, [kw_arg, overwrite_default],
                arg_names)

        def _wrapper(*args, **kwargs):
            new_kwargs = kwargs.copy()
                                   
            for counter, arg in enumerate(arg_names):
                try:
                    # First, see if it is set positionally...
                    new_kwargs[arg] = args[counter]
                except IndexError:
                    # ...if not, maybe it's an explicit kwarg...
                    try:
                        # Otherwise, the kwarg is good enough for us.
                        new_kwargs[arg] = kwargs[arg]
                    except KeyError:
                        # ...nope - it must be a default.
                        if arg in setting_map:
                            new_kwargs[arg] = getattr(settings, setting_map[arg].setting)
                        else:
                            position = len(args) - counter
                            new_kwargs[arg] = kw_defaults[position]

                if setting_map.has_key(arg) \
                        and new_kwargs[arg] == setting_map[arg].overwrite_default:
                    new_kwargs[arg] = getattr(settings, setting_map[arg].setting)

            return func(**new_kwargs)
        return _wrapper
    return _dec
