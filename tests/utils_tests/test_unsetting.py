import unittest
from django.test.utils import override_settings
from django.utils.unsetting import uses_settings


class UnsettingTests(unittest.TestCase):
    def test_uses_settings_decorator(self):
        with override_settings(USE_TZ=True):
            @uses_settings('USE_TZ', 'use_tz')
            def foo(use_tz=None):
                return use_tz
            self.assertTrue(foo())
            self.assertEqual(foo(use_tz=None), None)
            self.assertEqual(foo(None), None)
            self.assertEqual(foo(1), 1)
            self.assertEqual(foo(use_tz=2), 2)

    def test_uses_settings_fallback(self):
        with override_settings(USE_TZ=True):
            @uses_settings('USE_TZ', 'use_tz', overwrite_default=None)
            def foo(use_tz=None):
                return use_tz
            self.assertTrue(foo())
            self.assertTrue(foo(use_tz=None))
            self.assertTrue(foo(None))
            self.assertEqual(foo(1), 1)
            self.assertEqual(foo(use_tz=2), 2)
