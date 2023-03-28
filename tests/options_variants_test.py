#TODO:
# tests
# variant names with set opts
# test string repr changes when opts change 
# test MethodAV creation with opts gives str of variant

import unittest
from tests.test_utils import TestOptionsBase
from options import OptionParser, OptionsError, option, OptionsBase, variant


field_defaults = {
    "data": "MNIST",
    "test": False,
}

@variant("A1")
@variant("A2", abool=True)
@variant("A3", abool=True, aint=2, astr="variantA3")
class MethodA(OptionsBase):
    abool: bool = option(action="store_true")
    aint: int = option()
    astr: str = option()

@variant("B1")
@variant("B2", bbool=True, bint=3)
class MethodB(OptionsBase):
    bbool: bool = option(action="store_false")
    bint: int = option(default=8)


class ExampleOptions2(OptionsBase):
    test: bool = option('-t', action="store_true", help="Test only")
    data: str = option(default=field_defaults['data'], help="MNIST")
    method: MethodA|MethodB = option()
    
    
class TestVariants(TestOptionsBase):
    
    def check_options_fields(self, options, **kwargs):
        """
        Helper function. Check field values from kwargs.
        """
        for filed_name, field_val in kwargs.items():
            self.assertEqual(getattr(options, filed_name), field_val, msg=f"Check of field '{filed_name}' failed.")

    def test_variants_initial_fields(self):
        for variant_name, expected_opts, expected_opts_in_str in [
            ('MethodA', {'abool': False, 'aint': None, 'astr': None},    ['abool', 'aint', 'astr']),
            ('A1',      {'abool': False, 'aint': None, 'astr': None},    ['abool', 'aint', 'astr']),
            ('A2',      {'abool': True, 'aint': None, 'astr': None},     ['aint', 'astr']),
            ('A3',      {'abool': True, 'aint': 2, 'astr': "variantA3"}, []),
            ('MethodB', {'bbool': True, 'bint': 8},                      ['bbool', 'bint']),
            ('B1',      {'bbool': True, 'bint': 8},                      ['bbool', 'bint']),
            ('B2',      {'bbool': True, 'bint': 3},                      []),
        ]:
            with self.subTest(variant_name=variant_name, expected_opts=expected_opts):
                o = ExampleOptions2.parse_args(options_str = f'--method {variant_name}')
                self.check_options_fields(o.method, **expected_opts)
                s = o.str_wo_defaults
                
                #FIXME:
                if variant_name == 'MethodA':
                    variant_name = 'A1'
                if variant_name == 'MethodB':
                    variant_name = 'B1'
                    
                if len(expected_opts_in_str) == 0:
                    expected_str_pieces  = [f"--method {variant_name}"]
                else:
                    expected_str_pieces  = [f"--method '{variant_name}(", ")'"] + [ f"{k}={expected_opts[k]}" for k in expected_opts_in_str]

                if len(expected_opts_in_str) >1 :
                    expected_str_pieces += [',']*(len(expected_opts_in_str)-1)
                self.check_string_is_made_of(s, no_spaces=True, *expected_str_pieces)


    def test_name_changes(self):
        o = ExampleOptions2.parse_args(options_str = f'--method MethodA')
        
        for variant_name, field_opts, expected_opts_in_str in [
            ("A1", {'abool': False, 'aint': None, 'astr': None},    ['abool', 'aint', 'astr']),
            ("A2", {'abool': True, 'aint': None, 'astr': None},     ['aint', 'astr']),
            ("A3", {'abool': True, 'aint': 2, 'astr': "variantA3"}, []),
            ("B1", {'bbool': True, 'bint': 8},                      ['bbool', 'bint']),
            ("B2", {'bbool': True, 'bint': 3},                      [])
        ]:
            if variant_name[0] == 'B' and type(o.method) != MethodB:
                o.parse("--method MethodB")

            with self.subTest(variant_name=variant_name, expected_opts=field_opts):
                o.method.set_fields(**field_opts)
                s = o.str_wo_defaults

                if len(expected_opts_in_str) == 0:
                    expected_str_pieces  = [f"--method {variant_name}"]
                else:
                    expected_str_pieces  = [f"--method '{variant_name}(", ")'"] + [ f"{k}={field_opts[k]}" for k in expected_opts_in_str]

                if len(expected_opts_in_str) >1 :
                    expected_str_pieces += [',']*(len(expected_opts_in_str)-1)
                self.check_string_is_made_of(s, no_spaces=True, *expected_str_pieces)