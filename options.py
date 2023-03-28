import argparse
from argparse import ArgumentParser
import logging
import typing
from typing import Any, Type, Generic, TypeVar, get_type_hints, get_args, get_origin
import types
from functools import partial
import sys

logger = logging.getLogger(__name__)
FORMAT = "%(levelname)s: %(message)s"
logging.basicConfig(format=FORMAT)


__all__ = ['option', 'OptionsBase', 'OptionParser', 'variant', 'OptionsError']

T = TypeVar('T')


def option(*name_or_flags, **kwargs) -> Any:
    """
    Decorates type with meta-information.
    Arguments:
        *name_or_flags, **kwargs are similar to ArgumentParser.add_argument()
    """
    return (name_or_flags, kwargs)


def variant(name, **kwargs):
    """
    Decorates OptionsBase with name variants and field values set from kwargs, which override the default values.
    """
    def decorate(cls):
        cls.register_variants(name, kwargs)
        return cls

    return decorate


def get_action_value(argparse_kwargs, get_default=True) -> Any:
    """
    :param get_default: If True (default), returns value that is stored when the option is not passed
                        If False, returns value that is stored when the option is passed.
    """
    argumentParser = ArgumentParser()
    argumentParser.add_argument("--opt", **argparse_kwargs)

    if get_default:
        ns = argumentParser.parse_args([])
    else:
        ns = argumentParser.parse_args(["--opt"])

    return ns.opt


def get_all_names(optionsType, optionName):
    for paramName in get_type_hints(optionsType):
        name_or_flags = getattr(optionsType, paramName)[0]
        field_all_names = name_or_flags + (f"--{paramName}",)
        if f"--{optionName}" in field_all_names:
            return field_all_names

    return None


class OptionsError(Exception):
    """
    An error from creating or setting options.
    """

    def __init__(self, message):
        logger.error(message)
        self.message = message

    def __str__(self):
        return self.message


class OptionsBase:
    def __init__(self, **kwargs):
        # set defaults
        self.set_fields(**self.get_default_field_values())

        # set passed args
        self.set_fields(**kwargs)

    def set_fields(self, **kwargs):
        """
        Set fields from kwargs.
        """
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def __setattr__(self, __name: str, __value: Any) -> None:
        self.__check_constraints(__name, __value)
        super(OptionsBase, self).__setattr__(__name, __value)

    def __eq__(self, __o: object) -> bool:
        return type(__o) == type(self) and\
               vars(self) == vars(__o)

    def __str__(self, _vars=None) -> str:
        if _vars is None:
            _vars = vars(self)

        field_strs = []
        for k, v in _vars.items():
            if isinstance(v, OptionsBase):
                field_strs.append(self.option_format(k, v.suboption_str__()))
            else:
                field_strs.append(self.option_format(k, v))

        return " ".join(field_strs)

    @property
    def str_wo_defaults(self):
        return self.to_str(include_defaults=False)
    
    @property
    def as_variant(self):
        return self.suboption_str__()

    @classmethod
    def parse_args(cls: Type[T], options_str=None) -> T:
        """
        See OptionParser.parse_opts
        """
        return OptionParser.parse_opts(cls, options_str=options_str)

    def parse(self, options_str: str) -> None:
        """
        See OptionParser.parse_into.
        """
        OptionParser.parse_into(self, options_str=options_str)

    @classmethod
    def get_default_field_values(cls) -> typing.Dict[str, Any]:
        defaults = dict()

        for fieldName in get_type_hints(cls):
            if not hasattr(cls, fieldName):
                raise OptionsError("All fields must be initialized with options().")
            argparse_kwargs = getattr(cls, fieldName)[1]
            if 'default' in argparse_kwargs:
                defaults[fieldName] = argparse_kwargs['default']
            elif 'action' in argparse_kwargs:
                defaults[fieldName] = get_action_value(argparse_kwargs)
            else:
                defaults[fieldName] = None

        return defaults

    @classmethod
    def register_variants(cls, variant_name, opts):
        for n, v in opts.items():
            cls.__check_constraints(n, v)
        cls.get_variants().update({variant_name: opts})

    @classmethod
    def get_variants(cls):
        if not hasattr(cls, "__variants"):
            setattr(cls, "__variants", dict())
        return getattr(cls, "__variants")

    @classmethod
    def get_variants_help(cls):
        return "\n".join(name + " " + str(opts) for name, opts in cls.get_variants().items())

    @staticmethod
    def option_format(k, v):
        return f"--{k} {v}"

    @staticmethod
    def suboption_field_format(k, v):
        return f"{k}={v}"

    def to_str(self, include_defaults=True) -> str:
        """
        :param include_defaults: If True, values of all fields will be present in the returned string.
                                 If False, fields which values are equal to the default value will be omitted.
        """
        if include_defaults:
            return self.__str__()

        defaults = self.get_default_field_values()
        non_defaults = {k: v for k, v in vars(self).items() if defaults[k] != vars(self)[k]}

        return self.__str__(non_defaults)

    def get_suboption_name(self):
        name = type(self).__name__
        opts = vars(self)

        for var_name, var_opts in self.get_variants().items():
            if all([opts[var_opt_name] == var_opt_val for var_opt_name, var_opt_val in var_opts.items()]):
                name = var_name
                opts = {other_opt_name: other_opt_val for other_opt_name, other_opt_val in opts.items() if other_opt_name not in var_opts}
                break

        return name, opts

    def suboption_str__(self) -> str:
        suboption_name, _vars = self.get_suboption_name()
        if len(_vars) == 0:
            return suboption_name
        return '\'' + suboption_name + "(" + ",".join(self.suboption_field_format(k, v) for k, v in _vars.items()) + ")'"

    @classmethod
    def __check_constraints(cls, name, value):
        try:
            cls.__check_field_exists(name, type(value))
            cls.__check_valid_choice(name, value)
        except OptionsError as e:
            raise OptionsError(f"Constraints check failed for {cls.__name__} field '{name}' and value '{value}': {e.message}") from e

    @classmethod
    def __check_field_exists(cls, name, of_type):
        """
        Checks field with given name and type exists.
        """
        if name not in get_type_hints(cls):
            raise OptionsError(f"{name} is not among {cls.__name__} type fields: {[*get_type_hints(cls)]}")
        cls.__check_field_type_match(name, of_type)

    @classmethod
    def __check_field_type_match(cls, field_name, of_type):
        field_type = get_type_hints(cls)[field_name]
        matched_type = match_type(field_type, of_type)

        if matched_type is None and of_type is not types.NoneType:
            raise OptionsError(f"type {of_type} does not match field type {field_type}.")

    @classmethod
    def __check_valid_choice(cls, field_name, value):
        argparse_args = getattr(cls, field_name)[1]
        
        choices = argparse_args.get('choices', None)
        if choices is not None and value not in choices and value is not None:
            raise OptionsError(f"invalid choice '{value}', (choose from {choices + [None]}).")


def process_arguments(optionsType: Type[T], splitted_opts):
    argparse_compatible_opts = []
    additional_opts = dict()
    for idx in range(len(splitted_opts)):
        aco, ao = process_argument(optionsType, idx, splitted_opts)
        argparse_compatible_opts.extend(aco)
        additional_opts = dict(additional_opts, **ao)

    return argparse_compatible_opts, additional_opts


def process_argument(optionsType: Type[T], idx, splitted_opts):
    argument_str_name = splitted_opts[idx]
    argparse_compatible_pieces = []
    additional_opt = dict()

    if not argument_str_name.startswith("-"):
        return [], dict()

    if idx == len(splitted_opts) - 1 or\
       splitted_opts[idx+1].startswith("-"):
        if argument_str_name.startswith("-"):
            argparse_compatible_pieces.append(argument_str_name)
        return argparse_compatible_pieces, dict()

    argument_str_val = splitted_opts[idx+1]
    type_hints = get_type_hints(optionsType)

    for fieldName, field_type in type_hints.items():
        name_or_flags, argparse_kwargs = getattr(optionsType, fieldName)
        name_or_flags += (f"--{fieldName}",)
        if argument_str_name not in name_or_flags:
            continue

        if argument_str_val == "None":
            additional_opt[fieldName] = None
            logger.debug(f"Store None into {fieldName} field.")

        elif 'action' in argparse_kwargs:
            action_store_val = get_action_value(argparse_kwargs, get_default=False)
            if argument_str_val == str(action_store_val):
                logger.debug(f"ignore option value that is equal to the value stored by its action: {splitted_opts[idx]} {argument_str_val}")
                argparse_compatible_pieces.append(argument_str_name)
            else:
                logger.debug(f"explicitly store options value that is not equal to the value stored by its action: {splitted_opts[idx]} {argument_str_val}")
                additional_opt[fieldName] = parse_val(field_type, argument_str_val)
        else:
            argparse_compatible_pieces.extend(splitted_opts[idx:idx+2])

        break

    if not argparse_compatible_pieces and not additional_opt:
        raise OptionsError(f'{argument_str_name} is not found among {optionsType.__name__} fields.')

    return argparse_compatible_pieces, additional_opt


def parse_val(val_type: Type[T], val_str: str) -> T:
    if val_type == bool:
        if val_str == "True":
            return True
        if val_str == "False":
            return False
        raise OptionsError(f'Cannot parse bool from {val_str}.')

    # let python try to parse
    return val_type(val_str)


T1 = TypeVar('T1')


def match_type(dst: Type[T1] | types.UnionType, src: Type[T]) -> T | types.NoneType:

    if get_origin(dst) is types.UnionType:
        if src not in get_args(dst):
            return None
    else:
        if dst is not src and\
           not (dst is float and src is int):  # can assign int to float
            return None

    return src


def match_variant_by_name(find_in: Type[T1] | types.UnionType, to_match: str) -> T | types.NoneType:
    target_type = None
    variant_opts = dict()

    if get_origin(find_in) is types.UnionType:
        find_in_types = get_args(find_in)
    else:
        find_in_types = [find_in]

    for t in find_in_types:
        if t.__name__ == to_match:
            target_type = t
            break
        variants = t.get_variants()
        if to_match in variants:
            target_type = t
            variant_opts = variants[to_match]
            break

    return target_type, variant_opts


def suboptionWrapper(parsed_types, string: str):
    if string.startswith('\'') and string.endswith('\''):
        string = string[1:-1]
    elif string.startswith('\'') or string.endswith('\''):
        raise OptionsError(f"unexpected suboption str : {string}. It starts or ends with ' sign, probably string is parsed incorrectly. Suboption string should not contain spaces!")

    idx = string.find('(')
    if idx == -1:
        name = string
        args = ''
    else:
        name = string[:idx]
        args = string[idx:]
        if args == "()":
            args = ''
        else:
            args = args.replace('(', '--')\
                       .replace(')', '')\
                       .replace('=', ' ')\
                       .replace(',', ' --')

    if name == "None":
        return None

    target_type, variant_opts = match_variant_by_name(parsed_types, name)

    if target_type is None:
        raise OptionsError(f'{name} is not among types or variants permitted for {parsed_types}')

    opts = target_type(**variant_opts)
    try:
        opts.parse(options_str=args)
    except OptionsError as e:
        raise OptionsError(f"failed to parse suboption of type {target_type} from '{args}' : {e}") from e
    return opts


class OptionParser(Generic[T]):

    def __init__(self, optionsType: Type[T]) -> None:
        self.optionsType = optionsType
        self.argumentParser = OptionParser.create_argumentParser()
        OptionParser.register_opts(self.argumentParser, self.optionsType)

    @staticmethod
    def create_argumentParser():
        return ArgumentParser(exit_on_error=False)

    @staticmethod
    def register_opts(argumentParser: ArgumentParser, optionsType: Type[T]):
        for param, hint_type in get_type_hints(optionsType).items():
            name_or_flags, argparse_kwargs = getattr(optionsType, param)

            if get_origin(hint_type) is types.UnionType:
                if all(issubclass(t, OptionsBase) for t in get_args(hint_type)):
                    suboption_parser = partial(suboptionWrapper, hint_type)
                    argparse_kwargs['type'] = suboption_parser
                else:
                    logger.error(f'not all types of {hint_type} are subclasses of {OptionsBase}')

            elif issubclass(hint_type, OptionsBase):
                suboption_parser = partial(suboptionWrapper, hint_type)
                argparse_kwargs['type'] = suboption_parser
                argparse_kwargs['help'] = argparse_kwargs.get('help', '') + hint_type.get_variants_help()
            elif 'action' not in argparse_kwargs:
                argparse_kwargs['type'] = hint_type

            argumentParser.add_argument(f"--{param}", *name_or_flags, **argparse_kwargs)

    def instance_parse_opts(self, options_str: str = None) -> T:
        return OptionParser.parse_opts(self.optionsType,
                                       argumentParser=self.argumentParser,
                                       options_str=options_str)

    @staticmethod
    def parse_opts(optionsType: Type[T], *, argumentParser: ArgumentParser = None, options_str: str = None) -> T:
        """
            Creates options from options_str.

            :param argumentParser: If not None, must have options already registered
                                   via OptionParser.register_opts(argumentParser, optionsType)
            :param options_str: If not None, options are parsed from options_str
                                If None, options are parsed from the script arguments
        """
        options = optionsType()
        OptionParser.parse_into(options, argumentParser=argumentParser, options_str=options_str)
        return options

    @staticmethod
    def parse_into(options: OptionsBase, *, argumentParser: ArgumentParser = None,  options_str: str = None):
        """
        Sets only fields contained in options_str.
        """
        if argumentParser is None:
            argumentParser = OptionParser.create_argumentParser()
            OptionParser.register_opts(argumentParser, type(options))

        if options_str is None:
            splitted = sys.argv[1:]
        else:
            splitted = options_str.split()

        argparse_compatible_opts, additional_opts = process_arguments(type(options), splitted)
        argparse_compatible_opts_str = " ".join(argparse_compatible_opts)

        try:
            parsed_by_argparse = argumentParser.parse_args(argparse_compatible_opts)
        except argparse.ArgumentError as e:
            raise OptionsError(f"Failed to parse '{argparse_compatible_opts_str}' with argumentParser: {e}") from e

        for k, v in vars(parsed_by_argparse).items():
            names = get_all_names(type(options), k)
            if any([n in argparse_compatible_opts_str for n in names]):
                options.__setattr__(k, v)

        for k, v in additional_opts.items():
            options.__setattr__(k, v)
