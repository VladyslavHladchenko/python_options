*** README.md is generated with `jupyter nbconvert --execute --to markdown README.ipynb` *** 

requires python >=3.10

Wrapper for argparse to use set of arguments as class with type and name checking


```python
%load_ext autoreload
%autoreload 2
from ExampleOptions import *
```

Example class with options:


```python
show_class(ExampleOptions)
```


```python
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

```


## 1. Ways to create options instance:

1. Constructor with kwargs:



```python
o = ExampleOptions(W=6, net='net2', ikd='abc')
print(o)
```

    --test False --data MNIST --W 6 --net net2 --ikd abc --cnst None --method None --method2 None


2. Parse from string with static method: 


```python
o = ExampleOptions.parse_args("--W 7 --net net2 --ikd aaa")
print(o)
```

    --test False --data MNIST --W 7 --net net2 --ikd aaa --cnst None --method None --method2 None


3. Parse script arguments with a static method:


```python
%%writefile example_parse_args.py
from ExampleOptions import *
if __name__ == "__main__":
    o = ExampleOptions.parse_args()
    print(o)
```

    Overwriting example_parse_args.py



```python
%run example_parse_args.py --W 414 -t --data data_for_example_parse_args
```

    --test True --data data_for_example_parse_args --W 414 --net net1 --ikd None --cnst None --method None --method2 None


## 2. Ways to change field values:

1. Set fields


```python
o = ExampleOptions()
o.W = 4
print(o)
```

    --test False --data MNIST --W 4 --net net1 --ikd None --cnst None --method None --method2 None


2. set multiple values with `.set_fields()` method, same way as with constructor


```python
o = ExampleOptions()
o.set_fields(W=6,test=True)
print(o)
```

    --test True --data MNIST --W 6 --net net1 --ikd None --cnst None --method None --method2 None


3. Parse from string


```python
o = ExampleOptions()
o.W = 4
o.parse("-W 5 --data DATA -t")
print(o)
```

    --test True --data DATA --W 5 --net net1 --ikd None --cnst None --method None --method2 None


## 3. Values check:

1. Attempt to set an unknown field will not work. Throws `OptionsError` exception and logs error.


```python
o = ExampleOptions()
try:
    o.B=4
    raise Exception('this should not happen, the above code must throw')
except OptionsError as e:
    pass
```

    ERROR: B is not among ExampleOptions type fields: ['test', 'data', 'W', 'net', 'ikd', 'cnst', 'method', 'method2']
    ERROR: Constraints check failed for ExampleOptions field 'B' and value '4': B is not among ExampleOptions type fields: ['test', 'data', 'W', 'net', 'ikd', 'cnst', 'method', 'method2']


2.  Attempt to set incorrect type will not work. Throws `OptionsError` exception and logs error.


```python
o = ExampleOptions()
try:
    o.W='not a number'
    raise Exception('this should not happen, the above code must throw')
except OptionsError as e:
    pass
```

    ERROR: type <class 'str'> does not match field type <class 'int'>.
    ERROR: Constraints check failed for ExampleOptions field 'W' and value 'not a number': type <class 'str'> does not match field type <class 'int'>.


2. Set wrong value for field with `choices`. Throws `OptionsError` exception and logs error.


```python
o = ExampleOptions()
try:
    o.net='net3'
    raise Exception('this should not happen, the above code must throw')
except OptionsError as e:
    pass
```

    ERROR: invalid choice 'net3', (choose from ['net1', 'net2', None]).
    ERROR: Constraints check failed for ExampleOptions field 'net' and value 'net3': invalid choice 'net3', (choose from ['net1', 'net2', None]).


3. Any field can be set to None 


```python
o = ExampleOptions()
o.net=None
print(o)
```

    --test False --data MNIST --W 3 --net None --ikd None --cnst None --method None --method2 None


4. Same rules work when parsing from string or from script arguments.

5. Field with action `store_true` field can be set to False.Works in a similar way with `store_false`


```python
o = ExampleOptions()
print(o)
o.parse('-t')
print(o)
o.parse('-t False')
print(o)
```

    --test False --data MNIST --W 3 --net net1 --ikd None --cnst None --method None --method2 None
    --test True --data MNIST --W 3 --net net1 --ikd None --cnst None --method None --method2 None
    --test False --data MNIST --W 3 --net net1 --ikd None --cnst None --method None --method2 None


## 4. Options to string:

1. By default conversion to string preserves all fields, as seen in previous examples.

2. Default values can be omitted with `.to_str(include_defaults=False)` or `o.str_wo_defaults` property:


```python
o = ExampleOptions()
o.parse('--ikd idk')
o.data="notdefault"

print(o.to_str(include_defaults=False))
print(o.str_wo_defaults)
```

    --data notdefault --ikd idk
    --data notdefault --ikd idk


## 5. Properties


```python
o = ExampleOptions()
print(o.netUpper)
print(o.method)
```

    NET1
    None


## 6. Option field of custom type:

1. Fields can have OptionsBase derived type or union of OptionsBase derived types:


```python
show_class(ExampleOptions)
```


```python
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

```


2. Nested fields types must inherit OptionsBase


```python
show_class(MethodB)
```


```python
class MethodB(OptionsBase):
    bbool: bool = option( action="store_true")
    bint : int  = option()

```


3. Parsing:


```python
o = ExampleOptions.parse_args("--method MethodB() --method2 MethodA(abool=True,aint=7)")
print(o.str_wo_defaults)
```

    --method 'MethodB(bbool=False,bint=None)' --method2 'MethodA(abool=True,aint=7,astr=None)'


4. If passed in command line, '(' and ')' must be escaped or whole field surrounded with quotes:


```bash
%%bash
python example_parse_args.py --method MethodB\(\) --method2 'MethodA(abool=True,aint=7)'
```

    --test False --data MNIST --W 3 --net net1 --ikd None --cnst None --method 'MethodB(bbool=False,bint=None)' --method2 'MethodA(abool=True,aint=7,astr=None)'


5. Default value is set with an object instance:
```python
class ExampleOptions(OptionsBase):
    ...
    method2: MethodA = option(default=MethodA(abool=True,aint=7))
```

### 6.1 Variants

With `@variant` it is possible to give a suboption a shorter name and predefine some of its fields.

First argument to `@variant` is name, options for given name are passed as kwargs, these options override the default field values.


```python
show_class(MethodA)
```


```python
@variant("A", abool=True, aint=1)
@variant("AA", abool=False, aint=2, astr="This")
@variant("AAA", aint=2, astr="AAA!")
class MethodA(OptionsBase):
    abool: bool = option(action="store_true")
    aint : int  = option()
    astr : str  = option()

```


Options that passed to `@variant` are checked for correctness. (Same way as during OptionsBase field set).


```python
try:
    @variant("A", abool='not a bool :( ')
    class SomeNestedOption(OptionsBase):
        abool : bool = option()

    raise Exception('this should not happen, the above code must throw')
except OptionsError:
    pass
```

    ERROR: type <class 'str'> does not match field type <class 'bool'>.
    ERROR: Constraints check failed for SomeNestedOption field 'abool' and value 'not a bool :( ': type <class 'str'> does not match field type <class 'bool'>.


Suboptions can be parsed from variant names.


```python
print(ExampleOptions.parse_args("--method A").str_wo_defaults)
print(ExampleOptions.parse_args("--method AAA(abool=True)").str_wo_defaults)
print(ExampleOptions.parse_args("--method AA()").str_wo_defaults)
```

    --method 'A(astr=None)'
    --method 'AAA(abool=True)'
    --method AA


If corresponding subset of suboptions' fields is equal to all fields that are passed to some `variant`, it is shown in options string representation by the matching variant name and these fields are omitted from string:

MethodA(aint=2,astr=AAA!) matches the AAA variant of MethodA:


```python
print(ExampleOptions.parse_args("--method MethodA(aint=2,astr=AAA!)").str_wo_defaults)
```

    --method 'AAA(abool=False)'


To print one fled of type derived from `OptionsBase` use `.as_variant` property:


```python
o = ExampleOptions.parse_args("--method MethodA(aint=2,astr=AAA!)")
print(o.method.as_variant)
```

    'AAA(abool=False)'


## 7. Inheritance


```python
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
print(o)
```

    --methodInA 'MA(aint=None)' --methodInB 'MC(bint=8,cstr=None)'


❗Inheritance does not fully work for fields of custom type: 
```python
class MD(MC):
    ...
```
String `--methodInB MD` can not be parsed unless `MD` is listed among all the types possible for `methodInB` field like this:
```python
methodInB: MD|MC = option()
```

# Limitations

1. String value "None" can't be parsed, field value will be set to `None`
2. Fields of type `str` should not contain spaces (as in ArgumentParser library).

# Side effects
1. All values can be set to `None` or parsed as `None` from string or script arguments (plain `ArgumentParser` forbids such strings).
2. String value `"None"` can't be parsed, field value will be set to `None` (NoneType)
3. Unlike in `ArgumentParser`, value of argument with non-default action can be set, e.g. in `ExampleOptions`:
    - when parsing from string '--cnst', field `cnst` will contain 42 (plain `ArgumentParser` behaves this way)
    - when parsing from string '--cnst 33', field cnst will contain 33 (plain `ArgumentParser` forbids such string)
    - when parsing from string '--test', field test will contain True (plain `ArgumentParser` behaves this way)
    - when parsing from string '--test True', field test will contain True (plain `ArgumentParser` forbids such string)
    - when parsing from string '--test False', field test will contain False (plain `ArgumentParser` forbids such string)
