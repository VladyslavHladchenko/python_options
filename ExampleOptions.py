from options import OptionsBase, option, variant, OptionsError
from IPython.display import display
import inspect

@variant("A", abool=True, aint=1)
@variant("AA", abool=False, aint=2, astr="This")
@variant("AAA", aint=2, astr="AAA!")
class MethodA(OptionsBase):
    abool: bool = option(action="store_true")
    aint : int  = option()
    astr : str  = option()

class MethodB(OptionsBase):
    bbool: bool = option( action="store_true")
    bint : int  = option()

class MethodC(MethodB):
    cstr : str = option()
    
class ExampleOptions(OptionsBase):
    test: bool = option('-t', action="store_true", help="Test only")
    data: str = option(default='MNIST', help="MNIST")
    W: int =  option("-W", default=3, help="quantization levels per weight (0-continuous)")
    net: str = option(default="net1", choices=['net1', 'net2'], help='nets')
    ikd: str = option("--idk" , "-k", help='lll')
    cnst: int = option("-c" , help='store const', action='store_const', const=42 )
    method: MethodA|MethodB = option()  # Union of types
    method2: MethodA = option()  # one type

    @property
    def netUpper(self):
        return self.net.upper()


def show_class(cls):
    code = inspect.getsource(cls)
    md = f"```python\n{code}\n```"
    
    display({'text/plain': code,
             'text/markdown': md},
            raw=True)
