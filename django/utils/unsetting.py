from django.conf import settings
import inspect
"""
This is an incremental project to remove settings dependencies from Django libraries
so that Django core libraries can be imported without a settings file or initialization

"""

def use_setting(setting_name, kw_arg):
    """Decorator for functions
    """
    def _dec(func):
        kw_arg_index = inspect.getargspec(func)[0].index(kw_arg)
        if kw_arg not in inspect.getargspec(func)[0]:
            raise ValueError("Decorator keyword argument, %s, not in function spec." % kw_arg)
        def _wrapper(*args, **kwargs):
            if kw_arg not in kwargs and \
                    hasattr(settings, setting_name):
                setting_val = getattr(settings, setting_name)
                if len(args) > kw_arg_index:
                    args = list(args)
                    print args
                    args[kw_arg_index] = setting_val
                    print args
                else:
                    kwargs[kw_arg] = setting_val
            return func(*args, **kwargs)
        return _wrapper
    return _dec
