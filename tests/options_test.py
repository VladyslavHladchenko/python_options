# run all tests:
# quant$ python -m unittest tests.options_test

# run one test:
# quant$ python -m unittest tests.options_test.TestClassName.testFunctionName -v
# for example:
# quant$ python -m unittest tests.options_test.TestOptions.test_defaults -v

from enum import Enum, auto
import itertools
from typing import get_type_hints
import unittest
import itertools
from tests.test_utils import TestOptionsBase

from options import OptionParser, OptionsError, option, OptionsBase, variant


class MethodA(OptionsBase):
    abool: bool = option(action="store_true")
    aint: int = option()
    astr: str = option()

class MethodB(OptionsBase):
    bbool: bool = option(action="store_false")
    bint: int = option(default=8)
    
class MethodC(MethodB):
    cstr: str = option()


# default values of ExampleOptions fields, i.e. when options are created without the corresponding argument
field_defaults = {
    "data": "MNIST",
    "W": 3,
    "net": "net1",
    "test": False,
    "cnst": None,
    "idk": None,
    "method": None,
    "method2": None,
    "method3": MethodC(cstr='abcd',bint=2,bbool=True)
}


class ExampleOptions(OptionsBase):
    test : bool = option('-t', action="store_true", help="Test only")
    data : str = option(default=field_defaults['data'], help="MNIST")
    W : int = option("-W", default=field_defaults['W'], help="quantization levels per weight (0-continuous)")
    net: str = option(default=field_defaults['net'], choices=['net1', 'net2'], help='nets')
    idk: str = option("-k", help='idk:)')
    cnst: int = option("-c" , help='store const', action='store_const', const=42)
    method: MethodA|MethodB = option()
    method2: MethodB = option()
    method3: MethodC = option(default=field_defaults['method3'])

    @property
    def netUpper(self):
        return self.net.upper()


class CreateMethod(Enum):
    CONSTRUCTOR = auto()
    PARSE_ON_CLASS = auto()
    CONSTRUCTOR_THEN_PARSE = auto()
    OPTIONPARSER_STATIC = auto()
    OPTIONPARSER_INSTANCE = auto()


def createOptions(createMethod:CreateMethod, parsed_str="", **kwargs):
    """
    Helper function for creation options in different ways.
    """
    match createMethod:
        case CreateMethod.CONSTRUCTOR:
            return ExampleOptions(**kwargs)
        case CreateMethod.PARSE_ON_CLASS:
            return ExampleOptions.parse_args(parsed_str)
        case CreateMethod.CONSTRUCTOR_THEN_PARSE:
            o = ExampleOptions(**kwargs)
            o.parse(parsed_str)
            return o
        case CreateMethod.OPTIONPARSER_STATIC:
            return OptionParser.parse_opts(ExampleOptions, options_str=parsed_str)
        case CreateMethod.OPTIONPARSER_INSTANCE:
            op = OptionParser(ExampleOptions)
            return op.instance_parse_opts(options_str=parsed_str)


def generate_field_str_variants(field:OptionsBase):
    """
    Helper function.
    Generate all possible variants of nested filed string representations.
    See examples below in TestTestTools.test_generate_field_str_variants().
    """
    field_name = type(field).__name__
    field_vars = vars(field)
    field_vars_names = [*field_vars]

    for ordering in itertools.permutations(field_vars_names):
        yield "'" + field_name + "(" + ",".join( v+'='+str(field_vars[v]) for v in ordering) + ")'"


class TestTestTools(unittest.TestCase):
    def test_generate_field_str_variants(self):
        """
        Tests that helper function generate_field_str_variants works correctly.
        """
        methodC = MethodC(cstr='abcd',bint=2,bbool=True)
        
        expected=["'MethodC(cstr=abcd,bint=2,bbool=True)'",
                  "'MethodC(cstr=abcd,bbool=True,bint=2)'",
                  "'MethodC(bbool=True,cstr=abcd,bint=2)'",
                  "'MethodC(bbool=True,bint=2,cstr=abcd)'",
                  "'MethodC(bint=2,bbool=True,cstr=abcd)'",
                  "'MethodC(bint=2,cstr=abcd,bbool=True)'"]

        actual = list(generate_field_str_variants(methodC))

        self.assertTrue(len(expected) == len(actual))

        for e,a in zip(expected, actual):
            self.assertIn(e, actual)
            self.assertIn(a, expected)


class TestOptions(TestOptionsBase):
    def check_options_fields(self, options, **kwargs):
        """
        Helper function. Check field values.
        Non-default field value is taken from kwargs if present, otherwise checks default from global field_defaults dictionary
        """
        for field_name in get_type_hints(type(options)):
            expected = kwargs.get(field_name) if field_name in kwargs else field_defaults[field_name]
            self.assertEqual(getattr(options, field_name),
                             expected)

    def check_recreatable_from_string(self, options: OptionsBase):
        """
        Helper function.
        Check that options can be reconstructed from string representation.
        """
        for include_defaults in [False, True]:
            with self.subTest(subtest_name = "check_recreatable_from_string", include_defaults=include_defaults):
                string = options.to_str(include_defaults=include_defaults)
                created_from_string = options.parse_args(string)
                self.check_options_fields(created_from_string, **vars(options))


    def test_defaults(self):
        """
        Tests that default values of ExampleOptions are set correctly.
        """
        for createMethod in CreateMethod:
            with self.subTest(createMethod=createMethod):
                o = createOptions(createMethod)
                self.check_options_fields(o)
                self.check_recreatable_from_string(o)


    #TODO: unknown option names in string 
    

    def test_passed_values(self,
                            test=True,
                            data='abcdefg',
                            idk='1i2dk3',
                            cnst=42,
                            method2 = MethodB(bint=234,bbool=False),
                           ):
        method2_str = next(generate_field_str_variants(method2))
        test_args_dict = self.get_test_args()

        for method, parsed_str, constructor_args in\
            [
             (CreateMethod.CONSTRUCTOR, "", test_args_dict),
             (CreateMethod.CONSTRUCTOR_THEN_PARSE, f"--test {test} --data {data} --idk {idk} --cnst --method2 {method2_str}", {"test":False, "data":"bcd", "idk":"3", "cnst": 41, 'method2': MethodB(bint=324, bbool=True)}),
             (CreateMethod.PARSE_ON_CLASS, f"--test {test} --data {data} --idk {idk} --cnst --method2 {method2_str}", {}),
             (CreateMethod.PARSE_ON_CLASS, f"--test {test} --data {data} --idk {idk} --cnst {cnst} --method2 {method2_str}", {}),
             (CreateMethod.OPTIONPARSER_STATIC, f"--test {test} --data {data} --idk {idk} --cnst {cnst} --method2 {method2_str}", {}),
             (CreateMethod.OPTIONPARSER_INSTANCE, f"--test {test} --data {data} --idk {idk} --cnst {cnst} --method2 {method2_str}", {}),
             ]:

            with self.subTest(method=method, parsed_str=parsed_str, constructor_args=constructor_args):
                o = createOptions(method, parsed_str=parsed_str, **constructor_args)
                self.check_options_fields(o, **test_args_dict)
                self.check_recreatable_from_string(o)

    def test_parse_string_name_variants(self):
        # values for test
        W = 6
        cnst=42
        test=False
        data="somedata"
        method3=MethodC(cstr=None,bbool=True,bint=8)

        # all values in sublists are equivalent
        parsed_params = [
            [f"-W {W}", f"--W {W}"],
            ["-c", f'-c {cnst}', '--cnst', f'--cnst {cnst}'],
            ["", f"-t {test}", f'--test {test}'],
            [f"--data {data}"],
            ['--method3 MethodC', '--method3 \'MethodC\'', '--method3 MethodC()', '--method3 \'MethodC(cstr=None,bbool=True,bint=8)\'', '--method3 MethodC(cstr=None,bint=8)', '--method3 MethodC(bint=8)']
        ]

        for param_combinations in itertools.product(*parsed_params):
             for method in [
                            CreateMethod.PARSE_ON_CLASS,
                            CreateMethod.CONSTRUCTOR_THEN_PARSE,
                            CreateMethod.OPTIONPARSER_STATIC,
                            CreateMethod.OPTIONPARSER_INSTANCE
                            ]:
                parsed_str = " ".join(param_combinations)
                with self.subTest(method=method, parsed_str=parsed_str):
                    o = createOptions(method, parsed_str=parsed_str)
                    self.check_options_fields(o, W=W, cnst=cnst, data=data, test=test, method3=method3)
                    self.check_recreatable_from_string(o)

    def test_wrong_choice_parsed_string(self):
        test=True
        data="abc"
        idk='1234'
        net="net33"
        method2_str = "MethodB(bint=234,bbool=False)"

        parsed_str = f"--method2 {method2_str} --test {test} --data {data} --idk {idk} --net {net} --cnst"

        for method in\
            [
             CreateMethod.CONSTRUCTOR_THEN_PARSE,
             CreateMethod.PARSE_ON_CLASS,
             CreateMethod.OPTIONPARSER_STATIC,
             CreateMethod.OPTIONPARSER_INSTANCE,
             ]:
                with self.subTest(method=method, parsed_str=parsed_str):
                    with self.assertRaisesRegex(OptionsError, 'invalid choice.*net33'):
                        createOptions(method, parsed_str=parsed_str)


    def test_wrong_choice_constructor(self):
        with self.assertRaisesRegex(OptionsError, 'invalid choice.*net55'):
            ExampleOptions(net="net55", data = "somedata")


    def test_correct_choice_constructor(self):
        o = ExampleOptions(net="net2", data = "somedata")
        self.check_options_fields(o, net="net2", data="somedata")
        self.check_recreatable_from_string(o)


    def test_wrong_choice_set(self):
        with self.assertRaisesRegex(OptionsError, 'invalid choice.*omg'):
            o = ExampleOptions(net="net2", data = "somedata")
            o.net = "omg"


    def test_correct_choice_set(self):
        o = ExampleOptions(data = "somedata")
        o.net = "net2"
        self.check_options_fields(o, net="net2", data="somedata")
        o.net = "net1"
        self.check_options_fields(o, net="net1", data="somedata")
        self.check_recreatable_from_string(o)


    def test_str_without_defaults_only_defaults(self):
        for method in CreateMethod:
            with self.subTest(method=method):
                o = createOptions(method)
                s = o.to_str(include_defaults=False)
                self.assertEqual(s,"")
                
                s = o.str_wo_defaults
                self.assertEqual(s,"")


    def test_str_without_defaults_not_only_defaults(self):
        W=1
        test=True
        net="net2"
        method2 = MethodB(bint=234,bbool=False)
        method2_str_vars = list(generate_field_str_variants(method2))

        parsed_str = f"--W {W} --test {test} --net {net} --method2 {method2_str_vars[0]}"

        for method, constructor_args in\
            [
             (CreateMethod.CONSTRUCTOR, {"W": W, "test":test, "net":net, 'method2':method2}),
             (CreateMethod.CONSTRUCTOR_THEN_PARSE, {"W": 3, "test":False, "net":"net1", 'method2':method2}),
             (CreateMethod.PARSE_ON_CLASS, {}),
             (CreateMethod.OPTIONPARSER_STATIC, {}),
             (CreateMethod.OPTIONPARSER_INSTANCE, {}),
             ]:

            with self.subTest(method=method, parsed_str=parsed_str, constructor_args=constructor_args):
                o = createOptions(method, parsed_str=parsed_str, **constructor_args)
                s = o.to_str(include_defaults=False)

                self.check_string_is_made_of(s,
                                                f"--W {W}",
                                                f"--test {test}",
                                                f"--net {net}",
                                                [f"--method2 {s}" for s in method2_str_vars])

    def test_str_with_defaults_create_with_only_defaults(self):

        for method in CreateMethod:
            with self.subTest(method=method):
                o = createOptions(method)
                s = o.to_str()

                self.check_string_is_made_of(s,
                                        f"--W {field_defaults['W']}",
                                        f"--test {field_defaults['test']}",
                                        f"--net {field_defaults['net']}",
                                        f"--cnst {field_defaults['cnst']}",
                                        f"--data {field_defaults['data']}",
                                        f"--idk {field_defaults['idk']}",
                                        f"--method {field_defaults['method']}",
                                        f"--method2 {field_defaults['method2']}",
                                        [f"--method3 {v}" for v in generate_field_str_variants( field_defaults['method3'] )])

    def test_str_with_defaults_not_only_defaults(self):
        W=5
        test=True
        method2 = MethodB(bint=9991,bbool=True)
        method2_str_vars = list(generate_field_str_variants(method2))
        
        parsed_str = f"--W {W} --test {test} --method2 {method2_str_vars[0]}"

        for method, constructor_args in\
            [
            (CreateMethod.CONSTRUCTOR, {"W": W, "test":test,'method2':method2}),
            (CreateMethod.CONSTRUCTOR_THEN_PARSE, {"W": 3, "test":test, 'method2':method2}),
            (CreateMethod.PARSE_ON_CLASS, {}),
            (CreateMethod.OPTIONPARSER_STATIC, {}),
            (CreateMethod.OPTIONPARSER_INSTANCE, {}),
            ]:

            with self.subTest(method=method, parsed_str=parsed_str, constructor_args=constructor_args):
                o = createOptions(method, parsed_str=parsed_str, **constructor_args)

                s = o.to_str()

                self.check_string_is_made_of(s,
                                        f"--W {W}",
                                        f"--test {test}",
                                        f"--net {field_defaults['net']}",
                                        f"--cnst {field_defaults['cnst']}",
                                        f"--data {field_defaults['data']}",
                                        f"--idk {field_defaults['idk']}",
                                        [f"--method2 {v}" for v in method2_str_vars],
                                        f"--method {field_defaults['method']}",
                                        [f"--method3 {v}" for v in generate_field_str_variants( field_defaults['method3'] )])


    def test_set_union_field_type_works(self):
        test=True
        data='abcdefg'
        idk='1i2dk3'
        cnst=42

        for method_field, method_field_str in [
            (MethodB(bint=234,bbool=False), "MethodB(bint=234,bbool=False)"),
            (MethodA(aint=0,abool=False), "MethodA(aint=0,abool=False)"),
            (None, "None")
        ]:
            for createMethod, parsed_str, constructor_args in\
                [
                (CreateMethod.CONSTRUCTOR, "", {"test":test, "data":data, "idk":idk, "cnst": cnst, 'method': method_field}),
                (CreateMethod.CONSTRUCTOR_THEN_PARSE, f"--test {test} --data {data} --idk {idk} --cnst --method {method_field_str}", {"test":False, "data":"bcd", "idk":"3", "cnst": 41, 'method': MethodB(bint=324, bbool=True)}),
                (CreateMethod.PARSE_ON_CLASS, f"--test {test} --data {data} --idk {idk} --cnst --method {method_field_str}", {}),
                (CreateMethod.PARSE_ON_CLASS, f"--test {test} --data {data} --idk {idk} --cnst {cnst} --method {method_field_str}", {}),
                (CreateMethod.OPTIONPARSER_STATIC, f"--test {test} --data {data} --idk {idk} --cnst {cnst} --method {method_field_str}", {}),
                (CreateMethod.OPTIONPARSER_INSTANCE, f"--test {test} --data {data} --idk {idk} --cnst {cnst} --method {method_field_str}", {}),
                ]:

                with self.subTest(createMethod=createMethod, parsed_str=parsed_str, constructor_args=constructor_args):
                    o = createOptions(createMethod, parsed_str=parsed_str, **constructor_args)
                    self.check_options_fields(o, test=test, data=data, idk=idk, cnst=cnst,method=method_field)
                    self.check_recreatable_from_string(o)


    def test_parse_suboption_wrong_type(self):
        test=True
        data='abcdefg'
        idk='1i2dk3'
        cnst=42

        method_field, method_field_str = MethodC(bint=234,bbool=False), "MethodC(bint=234,bbool=False)"
        
        for createMethod, parsed_str, constructor_args in\
            [
            (CreateMethod.CONSTRUCTOR, "", {"test":test, "data":data, "idk":idk, "cnst": cnst, 'method': method_field}),
            (CreateMethod.CONSTRUCTOR_THEN_PARSE, f"--test {test} --data {data} --idk {idk} --cnst --method {method_field_str}", {"test":False, "data":"bcd", "idk":"3", "cnst": 41, 'method': MethodB(bint=324, bbool=True)}),
            (CreateMethod.PARSE_ON_CLASS, f"--test {test} --data {data} --idk {idk} --cnst --method {method_field_str}", {}),
            (CreateMethod.PARSE_ON_CLASS, f"--test {test} --data {data} --idk {idk} --cnst {cnst} --method {method_field_str}", {}),
            (CreateMethod.OPTIONPARSER_STATIC, f"--test {test} --data {data} --idk {idk} --cnst {cnst} --method {method_field_str}", {}),
            (CreateMethod.OPTIONPARSER_INSTANCE, f"--test {test} --data {data} --idk {idk} --cnst {cnst} --method {method_field_str}", {}),
            ]:

            with self.subTest(createMethod=createMethod, parsed_str=parsed_str, constructor_args=constructor_args):
                with self.assertRaisesRegex(OptionsError, ".*".join(["MethodC","does not match","MethodA","|","MethodB"])):
                    createOptions(createMethod, parsed_str=parsed_str, **constructor_args)
    

    def test_inheritance(self):
        class MA(OptionsBase):
            aint: int = option()

        class MB(OptionsBase):
            bint: int = option(default=8)
            
        class MC(MB):
            cstr: str = option()

        class OptsA(OptionsBase):
            methodInA: MA = option()

        class OptsB(OptsA):
            methodInB: MC = option()

        o = OptsB.parse_args("--methodInA MA --methodInB MC")
        self.check_options_fields(o, methodInA=MA(aint=None), methodInB=MC(cstr=None, bint=8))


if __name__ == '__main__':
    unittest.main()