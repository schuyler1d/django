import unittest
from django.test.utils import override_settings
from django.utils.unsetting import use_setting

class UnsettingTests(unittest.TestCase):
    def test_use_setting_dec(self):
        with override_settings(USE_TZ=True):
            @use_setting('USE_TZ', 'use_tz')
            def foo(use_tz=None):
                return use_tz
            self.assertTrue(foo())
            self.assertEqual(foo(1), 1)
            self.assertEqual(foo(use_tz=2), 2)

