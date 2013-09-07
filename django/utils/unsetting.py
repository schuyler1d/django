from django.conf import settings
import inspect
"""

This is an incremental project to remove settings dependencies from Django
libraries so that Django core libraries can be imported without a settings
file or initialization

"""


def use_setting(setting_name, kw_arg, overwrite_default='FAKE_VALUE'):
    """
    Decorator for functions
    :param setting_name: setting attribute, e.g. 'USE_TZ'
    :param kw_arg: function parameter that can be used instead of the setting
    :param overwrite_default: In some cases, explicitly setting the parameter
                  should still use the setting
    """
    def _dec(func):
        kw_arg_index = inspect.getargspec(func)[0].index(kw_arg)
        arg_names = inspect.getargspec(func).args
        kw_defaults = inspect.getargspec(func).defaults

        if kw_arg not in arg_names:
            raise ValueError("Decorator keyword argument, "
                             "%s, not in function spec." % kw_arg)

        def _wrapper(*args, **kwargs):
            new_kwargs = {}

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
                        if arg == kw_arg:
                            new_kwargs[arg] = getattr(settings, setting_name)
                        else:
                            position = len(args) - counter
                            new_kwargs[arg] = kw_defaults[position]

            if new_kwargs[kw_arg] == overwrite_default:
                new_kwargs[kw_arg] = getattr(settings, setting_name)

            return func(**new_kwargs)
        return _wrapper
    return _dec
