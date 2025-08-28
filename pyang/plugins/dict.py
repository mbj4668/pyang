"""Copyright 2023 Cisco Systems
Author - Sibam Senapati

Dict provides the parsed yang module in dictionary format

Current:
    1. Supports multiple modules
    2. Given modules, it converts them to dictionary format.

Format of the dictionary:

"""

import optparse
import csv
import sys
import json

from pyang import plugin
from pyang import statements, types


def pyang_plugin_init():
    plugin.register_plugin(DictPlugin())


class DictPlugin(plugin.PyangPlugin):
    def __init__(self):
        plugin.PyangPlugin.__init__(self, "dict")
        self.ignore_keyword_list = list()

    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts["dict"] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--dict-help",
                                 dest="dict_help",
                                 action="store_true",
                                 help="Print the dictionary format and then exit"),
            optparse.make_option(
                "--ignore-keyword",
                dest="ignore_keyword",
                help="Filter output to only desired keywords.",
                action="append",
            ),
            ]
        g = optparser.add_option_group("Dict output specific options")
        g.add_options(optlist)

    def setup_ctx(self, ctx):
        if ctx.opts.dict_help:
            self.print_help()
            sys.exit(0)

        self.ignore_keyword_list.extend(ctx.opts.ignore_keyword)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        """
            This function is responsible to create the dictionary for all the modules given as input.
            This inturn calls module specific function to create the dictionary module wise.
        """

        all_modules_dict = self.gen_a_new_dict_with_tally()

        for module in sorted(modules, key=lambda m: m.arg):
            module_dict = self.gen_dict_module(ctx, module)
            self.add_key_value_to_dict(dest_dict = all_modules_dict, key_word = 'module' , source = module_dict)

        fd.write(json.dumps(all_modules_dict))


    def gen_dict_module(
        self,
        ctx,
        stmt,
    ):
        """
            This function takes a statement - stmt, and recursively creates 
            a dictionary which contains all the values that this stmt contains.
        """


        current_dict = self.gen_a_new_dict_with_tally()

        ## Get the statement sets
        stmt_sets = set(stmt.substmts)
        if hasattr(stmt, 'i_children'):
            stmt_sets.update(stmt.i_children)

        stmt_sets = [ s for s in stmt_sets if s.keyword not in self.ignore_keyword_list]

        if len(stmt_sets) > 0:

            ## First lets add the current name to the dictionary
            self.add_key_value_to_dict(dest_dict=current_dict, key_word='@name', source=stmt.arg)

            for s in stmt_sets:
                key = s.keyword

                if type(key) == tuple:
                    key = key[0] + '::' + key[1]

                value = self.gen_dict_module(ctx, s)

                self.add_key_value_to_dict(dest_dict = current_dict, key_word=key, source=value)

            return current_dict
        else:
            return stmt.arg

    def gen_a_new_dict_with_tally(self, ):
        new_dict = dict()
        new_dict['tally'] = dict()
        return new_dict
    
    def add_key_value_to_dict(self, dest_dict, key_word, source):
        """
            This function add the source to the key  - key_word

            Assumption: The dest_dict must be created from the function - gen_a_new_dict_with_tally, 
            so that it will have 'tally' as a key.
        """

        number = 0
        if key_word in dest_dict['tally'].keys():
            number = dest_dict['tally'][key_word]

        key = key_word + str(number)
        dest_dict[key] = source
        number+=1
        dest_dict['tally'][key_word] = number


    def print_help(self,):
        print("""
            Fill in the dictionary format. And give some help
            for manuevering through the dictionary.

            As the yang file is formatted as in a hierarchy structure, the dictionary is going to be 
            of recursive structure.

            Now, remember that inside a statement there could be one to many mapping of the substatements.
            Now the way to convert it to dictionary is to add some numbering to the keywords.

            For example a leaf can contain multiple 'must' substatements. now the way it is saved in the leaf subdict is
            {
                'must0' : 'count(.) > 5'
                'must1' : 'sum(.) <= 10'

                'tally' : {
                    'must' : 2
                }
            }

            Now when we are manuevering we must have the count of the number of keywords present. This count is present in the same dictionary with the
            key name as 'tally'. This is a dictionary which contains the number of the keyword present in this statement.

            The way to manuevere the current statement is to go through the tally dict, and for all keywords present in it, 
            all those keywords will be there with the index number suffixed to it.
        """)
