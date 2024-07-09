''' DTNMA-ADM Plugin
Copyright (c) 2023-2024 The Johns Hopkins University Applied Physics
Laboratory LLC.

DTNMA Application Data Model (ADM) of [I-D.ietf-dtn-adm-yang] uses
YANG syntax and extension statements, but not YANG data modeling statements,
to define static data models known as "ADM Modules".

The transforms provided for ADM Modules are used to apply auto-generated
object enumerations where needed.
'''
import optparse
from typing import List
from pyang import plugin, statements
from pyang.plugins.dtnma_amm import MODULE_NAME, AMM_OBJ_NAMES


def pyang_plugin_init():
    ''' Called by plugin framework to initialize this plugin.
    '''
    plugin.register_plugin(DtnmaAdmPlugin())


class DtnmaAdmPlugin(plugin.PyangPlugin):
    ''' A transformer to clean up ADM Module contents. '''

    def add_opts(self, optparser:optparse.OptionParser):
        pass

    def setup_ctx(self, ctx):
        pass

    def add_transform(self, xforms):
        xforms['adm-add-enum'] = self

    def transform(self, ctx, modules:List[statements.ModSubmodStatement]):
        for mod_stmt in modules:
            ns_stmt = mod_stmt.search_one('namespace')
            if not ns_stmt or not ns_stmt.arg.startswith('ari:'):
                continue

            # Each object type gets its own enumeration domain
            for obj_kywd in AMM_OBJ_NAMES:
                enums = {}
                missing = []
                for obj_stmt in mod_stmt.search(obj_kywd):
                    enum_stmt = obj_stmt.search_one((MODULE_NAME, 'enum'))
                    if enum_stmt:
                        enums[int(enum_stmt.arg)] = obj_stmt
                    else:
                        missing.append(obj_stmt)
                if not missing:
                    continue

                amm_prefix = [
                    key
                    for key, (name, _rev) in mod_stmt.i_prefixes.items()
                    if name == MODULE_NAME
                ]
                enum_kywd = (amm_prefix[0], 'enum')

                # Start just beyond the existing values
                next_val = max(enums.keys()) + 1 if enums else 0
                for obj_stmt in missing:
                    enum_stmt = statements.new_statement(mod_stmt, obj_stmt, obj_stmt.pos, enum_kywd, str(next_val))
                    obj_stmt.substmts.insert(0, enum_stmt)
                    next_val += 1
