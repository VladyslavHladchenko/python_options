
import unittest
import inspect

class TestOptionsBase(unittest.TestCase):
    def get_test_args(self):
        fullargspec = inspect.getfullargspec(getattr(self, self._testMethodName))
        args = fullargspec.args[1:]
        defaults = fullargspec.defaults
        test_args_dict = dict(zip(args, defaults))
        print(f"\nTestOptions.get_test_args for test {self._testMethodName=} : {test_args_dict}")
        return test_args_dict


    def check_string_is_made_of(self, s, *elements, no_spaces=False):
        """
        Helper function.
        """
        for e in elements:
            if isinstance(e, str):
                self.assertIn(e, s, msg=f"check_string_is_made_of: substring '{e}' should be in string '{s}' !")
                s = s.replace(e,'',1)
            else:
                found = False
                for variant in e:
                    if variant in s:
                        found=True
                        s = s.replace(variant,'',1)
                        break
                self.assertTrue(found, msg=f"none from {e} is found in {s}")

        if no_spaces:
            should_be_empty=s
        else:
            should_be_empty = s.replace(' ','')
        self.assertEqual(should_be_empty, "")