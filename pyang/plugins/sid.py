"""sid plugin

Plugin used to generate or update .sid files.
"""

import optparse
import sys
import time
import json
import collections
import re
import os

from pyang import plugin
from collections import OrderedDict

def pyang_plugin_init():
    plugin.register_plugin(SidPlugin())

class SidPlugin(plugin.PyangPlugin):

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--sid-help",
                                 dest="sid_help",
                                 action="store_true",
                                 help="Print help on automatic SID generation"),
            optparse.make_option("--generate-sid-file",
                                 action="store",
                                 type="string",
                                 dest="generate_sid_file",
                                 help="Generate a .sid file."),
            optparse.make_option("--update-sid-file",
                                 action="store",
                                 type="string",
                                 dest="update_sid_file",
                                 help="Generate a .sid file based on a previous .sid file."),
            optparse.make_option("--check-sid-file",
                                 action="store",
                                 type="string",
                                 dest="check_sid_file",
                                 help="Check the consistency between a .sid file and the .yang file(s)."),
            optparse.make_option("--list-sid",
                                 action="store_true",
                                 dest="list_sid",
                                 help="Print the list of SID."),
            ]

        g = optparser.add_option_group("SID file specific options")
        g.add_options(optlist)

    def setup_ctx(self, ctx):
        if ctx.opts.sid_help:
            print_help()
            sys.exit(0)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def post_validate_ctx(self, ctx, modules):
        nbr_option_specified = 0
        if ctx.opts.generate_sid_file is not None:
            nbr_option_specified += 1
        if ctx.opts.update_sid_file is not None:
            nbr_option_specified += 1
        if ctx.opts.check_sid_file is not None:
            nbr_option_specified += 1
        if nbr_option_specified == 0:
            return
        if nbr_option_specified > 1:
            sys.stderr.write("Invalid option, only one process on .sid file can be requested.\n")
            return

        if ctx.errors != []:
            sys.stderr.write("Invalid YANG module, .sid file processing aborted.\n")
            return

        sid_file = SidFile()

        if ctx.opts.generate_sid_file is not None:
            sid_file.range = ctx.opts.generate_sid_file
            sid_file.is_consistent = False
            sid_file.sid_file_created = True

        if ctx.opts.update_sid_file is not None:
            sid_file.input_file_name = ctx.opts.update_sid_file

        if ctx.opts.check_sid_file is not None:
            sid_file.input_file_name = ctx.opts.check_sid_file
            sid_file.check_consistency = True
            print("Checking consistency of '%s'" % sid_file.input_file_name)

        if ctx.opts.list_sid:
            sid_file.list_content = True

        try:
            sid_file.process_sid_file(modules[0])

        except SidParcingError as e:
            sys.stderr.write("ERROR, %s\n" % e.msg)
            sys.exit(1)
        except SidFileError as e:
            sys.stderr.write("ERROR in '%s', %s\n" % (sid_file.input_file_name, e.msg))
            sys.exit(1)
        except FileNotFoundError as e:
            sys.stderr.write("ERROR, file '%s' not found\n" % e.filename)
            sys.exit(1)
        except json.decoder.JSONDecodeError as e:
            sys.stderr.write("ERROR in '%s', line %d, column %d, %s\n" % (sid_file.input_file_name, e.lineno, e.colno, e.msg))
            sys.exit(1)

def print_help():
    print("""
Structure IDentifier (SID) are used to map YANG definitions to
CBOR encoding. These SIDs can be automatically generated
for a YANG module using the pyang sid plugin.

   pyang --generate-sid-file <entry-point:size> <yang-module>

For example:
   pyang --generate-sid-file 20000:100 toaster@2009-11-20.yang

The name of the .sid file generated is:

   <module-name>@<module-revision>.sid

Each time new items(s) are added to a YANG module by the
introduction of a new revision of this module, its included
sub-module(s) or imported module(s), the .sid file need to be
updated. This is done by providing the name of the previous
.sid file as argument.

   pyang --update-sid-file <file-name> <yang-module>

For example:
   pyang --update-sid-file toaster@2009-11-20.sid toaster@2009-12-28.yang

The --check-sid-file option can be used at any time to verify
if the .sid file need to be updated.

   pyang --check-sid-file <file-name> <yang-module>

The --list_sid option can be included before any of the previous
option to obtains the list of SIDs assigned or validated.

For example:
   pyang --list-sid --generate-sid-file 20000:100 toaster@2009-11-20.yang
"""
)

############################################################
class SidFileError(Exception):
    def __init__(self, msg=""):
        self.msg = msg

class SidParcingError(Exception):
    """raised by plugins to fail the emit() function"""
    def __init__(self, msg=""):
        self.msg = msg

############################################################
class SidFile:
    def __init__(self):
        self.sid_file_created = False
        self.is_consistent = True
        self.check_consistency = False
        self.list_content = False
        self.input_file_name = None
        self.range = None
        self.node_highest = 0


    def process_sid_file(self, module):
        self.module_name = module.i_modulename
        self.module_revision = self.get_module_revision(module)
        self.assignment_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        self.output_file_name = '%s@%s.sid' % (self.module_name, self.module_revision)

        if self.range is not None:
            self.set_initial_range(self.range)

        if self.input_file_name is not None:
            if self.input_file_name[-4:] != ".sid":
                raise SidParcingError("File '%s' is not a .sid file" % self.input_file_name)

            with open(self.input_file_name) as f:
                self.content = json.load(f, object_pairs_hook=collections.OrderedDict)
            self.validate_key_and_value()
            self.sort_ranges()
            self.validate_ovelaping_ranges()
            self.validate_sid()

        self.set_module_information()
        self.collect_module_items(module)
        self.sort_items()
        self.assign_sid()

        if self.list_content:
            self.list_all_items()
        else:
            self.list_deleted_items()

        if self.check_consistency:
            if self.is_consistent:
                print("Check completed successfully")
            else:
                print("The .sid file need to be updated.")
        else:
            if self.is_consistent:
                print("No .sid file generated, the current .sid file is already up to date.")
            else:
                self.generate_file()
                if self.sid_file_created:
                    print("\nFile %s created" % self.output_file_name)
                else:
                    print("\nFile %s updated" % self.output_file_name)
                self.print_statistic()


    ########################################################
    def set_initial_range(self, range):
        components = range.split(':')
        if len(components) != 2 or not re.match(r'\d+:\d+', range):
            raise SidParcingError("invalid range in argument, must be '<entry-point>:<size>'.")

        self.content = OrderedDict([('assignment-ranges', [])])
        self.content['assignment-ranges'].append(OrderedDict([('entry-point', int(components[0])), ('size', int(components[1]))]))

    ########################################################
    # Retrieve the module revision from the pyang context
    def get_module_revision(self, module):
        revision = None
        for substmt in module.substmts:
            if substmt.keyword == 'revision':
                if revision == None:
                    revision = substmt.arg
                else:
                    if revision < substmt.arg:
                        revision = substmt.arg

        if revision == None:
            raise SidParcingError("no revision found in YANG definition file.")
        return revision

    ########################################################
    # Set the 'module-name' and/or 'module-revision' in the .sid file if require
    def set_module_information(self):
        if 'module-name' not in self.content or self.module_name != self.content['module-name']:
            self.content['module-name'] = self.module_name
            if self.check_consistency == True:
                print("ERROR, Mismatch between the module name defined in the .sid file and the .yang file.")
                self.is_consistent = False

        if 'module-revision' not in self.content or self.module_revision != self.content['module-revision']:
            self.content['module-revision'] = self.module_revision
            if self.check_consistency == True:
                print("ERROR, Mismatch between the module revision defined in the .sid file and the .yang file.")
                self.is_consistent = False

    ########################################################
    # Verify the tag and data type of each .sid file JSON object
    def validate_key_and_value(self):
        for key in self.content:

            if key == 'assignment-ranges':
                if type(self.content[key]) != list:
                    raise SidFileError("key 'assignment-ranges', invalid  value.")
                self.validate_ranges(self.content[key])
                continue

            if key == 'module-name':
                continue

            if key == 'module-revision':
                continue

            if key == 'items':
                if type(self.content[key]) != list:
                    raise SidFileError("key 'items', invalid value.")
                self.validate_items(self.content[key])
                continue

            raise SidFileError("invalid key '%s'." % key)

    def validate_ranges(self, ranges):
        for range in ranges:
            for key in range:
                if key == 'entry-point':
                    if type(range[key]) != int:
                        raise SidFileError("invalid 'entry-point' value '%s'." % range[key])
                    continue

                if key == 'size':
                    if type(range[key]) != int:
                        raise SidFileError("invalid 'size' value '%s'." % range[key])
                    continue

                raise SidFileError("invalid key '%s'." % key)

    def validate_items(self, items):
        for item in items:
            for key in item:
                if key == 'type':
                    if type(item[key]) != str or not re.match(r'identity$|node$|notification$|rpc$|action$', item[key]):
                        raise SidFileError("invalid 'type' value '%s'." % item[key])
                    continue

                if key == 'assigned':
                    if type(item[key]) != str or not re.match(r'\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ$', item[key]):
                        raise SidFileError("invalid 'assigned' value '%s'." % item[key])
                    continue

                if key == 'label':
                    if type(item[key]) != str:
                        raise SidFileError("invalid 'label' value '%s'." % item[key])
                    continue

                if key == 'sid':
                    if type(item[key]) != int:
                        raise SidFileError("invalid 'sid' value '%s'." % item[key])
                    continue

                raise SidFileError("invalid key '%s'." % key)

    ########################################################
    # Sort the range list by 'entry-point'
    def sort_ranges(self):
        if 'assignment-ranges' in self.content:
            self.content['assignment-ranges'].sort(key=lambda range:range['entry-point'])

    ########################################################
    # Verify if each range defined in the .sid file is distinct
    def validate_ovelaping_ranges(self):
        if 'assignment-ranges' in self.content:
            last_highest_sid = 0
            for range in self.content['assignment-ranges']:
                if range['entry-point'] < last_highest_sid:
                    raise SidFileError("overlapping ranges are not allowed.")
                last_highest_sid += range['entry-point'] + range['size']

    ########################################################
    # Verify if each SID listed in items is in range and is not duplicate.
    def validate_sid(self):
        self.content['items'].sort(key=lambda item:item['sid'])
        last_sid = -1
        for item in self.content['items']:
            if self.out_of_ranges(item['sid']):
                raise SidFileError("'sid' %d not within 'assignment-ranges'" % item['sid'])
            if item['sid'] == last_sid:
                raise SidFileError("duplicated 'sid' value %d " % item['sid'])
                last_sid = item['sid']

    def out_of_ranges(self, sid):
        for range in self.content['assignment-ranges']:
            if sid >= range['entry-point'] and sid < range['entry-point'] + range['size']:
                return False
        return True

    ########################################################
    # Collection of items defined in .yang file(s)
    def collect_module_items(self, module):
        if 'items' not in self.content:
            self.content['items'] = []

        for item in self.content['items']:
            item['status'] = 'd' # Set to 'd' deleted, updated to 'o' if present in .yang file

        for children in module.i_children:
            if children.keyword == 'leaf' or children.keyword == 'leaf-list' or children.keyword == 'anyxml' or children.keyword == 'anydata':
                self.merge_item(self.getType(children), self.getPath(children))

            if children.keyword == 'container' or children.keyword == 'list':
                self.merge_item(self.getType(children), self.getPath(children))
                self.collect_inner_data_nodes(children.i_children)

            if children.keyword == 'choice' or children.keyword == 'case':
                self.collect_inner_data_nodes(children.i_children)

            if children.keyword == 'rpc':
                self.merge_item('rpc', "/%s" % children.arg)
                for statement in children.i_children:
                    if statement.keyword == 'input' or statement.keyword == 'output':
                        self.collect_inner_data_nodes(statement.i_children)

            if children.keyword == 'notification':
                self.merge_item('notification', "/%s" % children.arg)
                self.collect_inner_data_nodes(children.i_children)

        for identity in module.i_identities:
                self.merge_item('identity', "/%s%s" % (self.get_base_identity(module.i_identities[identity]), identity))

        for substmt in module.substmts:
            if substmt.keyword == 'augment':
                self.collect_inner_data_nodes(substmt.substmts)

    def collect_inner_data_nodes(self, children):
        for statement in children:
            if statement.keyword == 'leaf' or statement.keyword == 'leaf-list' or statement.keyword == 'anyxml' or statement.keyword == 'anydata':
                self.merge_item(self.getType(statement), self.getPath(statement))

            if statement.keyword == 'container' or statement.keyword == 'list':
                self.merge_item(self.getType(statement), self.getPath(statement))
                self.collect_inner_data_nodes(statement.i_children)

            if statement.keyword == 'action':
                self.merge_item('action', self.getPath(statement))
                for children in statement.i_children:
                    if children.keyword == 'input' or children.keyword == 'output':
                        self.collect_inner_data_nodes(children.i_children)

            if statement.keyword == 'notification':
                self.merge_item('notification', self.getPath(statement))
                self.collect_inner_data_nodes(statement.i_children)

            if statement.keyword == 'choice' or statement.keyword == 'case':
                self.collect_inner_data_nodes(statement.i_children)

    def get_base_identity(self, identity):
        for substmts in identity.substmts:
            if substmts.keyword == 'base':
                if substmts.arg.find(':') == -1:
                    return "%s/" % substmts.arg
                else:
                    return "%s/" % substmts.arg[substmts.arg.find(':')+1: ]
        return ""

    def getType(self, statement):
        if statement.keyword == "rpc":
            return 'rpc'
        if statement.keyword == "action":
            return 'action'
        if statement.keyword == "notification":
            return 'notification'
        if statement.parent != None:
            return self.getType(statement.parent)
        return 'node'

    def getPath(self, statement, path = ""):
        current_module = statement.i_module
        return self.constructPath(statement, current_module, "")

    def constructPath(self, statement, current_module, path):
        if statement.keyword == "module":
            return path

        if statement.i_module == None or statement.i_module == current_module:
            path = "/" + statement.arg + path
        else:
            path = "/" + statement.i_module.arg + ":" + statement.arg + path

        if statement.parent != None:
            path = self.constructPath(statement.parent, current_module, path)
        return path

    def merge_item(self, type, label):
        for item in self.content['items']:
            if (type == item['type'] and label == item['label']):
                item['status'] = 'o' # Item already assigned
                return
        self.content['items'].append(OrderedDict([('type', type),('assigned', self.assignment_time), ('label', label), ('sid', -1), ('status', 'n')]))
        self.is_consistent = False

    ########################################################
    # Sort the items list by 'type', 'assigned' and 'label'
    def sort_items(self):
        self.content['items'].sort(key=lambda item:item['label'])
        self.content['items'].sort(key=lambda item:item['assigned'])
        self.content['items'].sort(key=lambda item:item['type'])

    ########################################################
    # Identifier assignment
    def assign_sid(self):
        self.highest_sid = self.get_highest_sid()

        for i in range(len(self.content['items'])):

            if self.content['items'][i]['sid'] == -1:
                self.content['items'][i]['sid'] = self.highest_sid
                self.highest_sid = self.get_next_sid(self.highest_sid)

    def get_highest_sid(self):
        sid = self.content['assignment-ranges'][0]['entry-point']

        for item in self.content['items']:
            if (item['sid'] >= sid):
                sid = item['sid']
                sid = self.get_next_sid(sid)

        return sid

    def get_next_sid(self, sid):
        sid += 1
        for i in range(len(self.content['assignment-ranges'])):
            if sid < self.content['assignment-ranges'][i]['entry-point'] + self.content['assignment-ranges'][i]['size']:
                return sid
            else:
                if i + 1 < len(self.content['assignment-ranges']):
                    if sid < self.content['assignment-ranges'][i+1]['entry-point']:
                        return self.content['assignment-ranges'][i+1]['entry-point']

        raise SidParcingError("SID range(s) exhausted, extend the allocation range or add a new one.")

    ########################################################
    def list_all_items(self):
        definition_removed = False

        print("\nSID        Assigned to")
        print("---------  --------------------------------------------------")
        for item in self.content['items']:
            sys.stdout.write("%-9s  %s %s" % (item['sid'], item['type'], item['label']))
            if item['status'] == 'n' and not self.sid_file_created:
                sys.stdout.write(" (New)")
            if item['status'] == 'd':
                sys.stdout.write(" (Remove)")
                definition_removed = True
            sys.stdout.write("\n")

        if definition_removed:
            print("\nWARNING, obsolete definitions should be defined as 'deprecated' or 'obsolete'.")
        sys.stdout.write("\n")

    ########################################################
    def list_deleted_items(self):
        definition_removed = False
        for item in self.content['items']:
            if item['status'] == 'd':
                print("WARNING, item '%s' have been deleted form the .yang files." % item['label'])
                definition_removed = True

        if definition_removed:
            print("Obsolete definitions MUST NOT be removed from YANG modules, see RFC 6020 section 10.")
            print("These definition(s) should be reintroduced with a 'deprecated' or 'obsolete' status.")

    ########################################################
    def generate_file(self):
        for item in self.content['items']:
            del item['status']

        if os.path.exists(self.output_file_name):
            os.remove(self.output_file_name)

        with open(self.output_file_name, 'w') as outfile:
            json.dump(self.content, outfile, indent=2)

    ########################################################
    def number_of_SIDs(self):
        size = 0
        for range in self.content['assignment-ranges']:
            size += range['size']
        return size

    def number_of_SIDs_used(self, highest_sid):
        if highest_sid == 0:
            return 0

        used = 0
        for range in self.content['assignment-ranges']:
            if highest_sid < ( range['entry-point'] + range['size'] ):
                    return highest_sid - range['entry-point'] + used
            used += range['size']
        return used

    def print_statistic(self):
        print ("Number of SIDs available : %d" % self.number_of_SIDs())
        print ("Number of SIDs assigned : %d" % self.number_of_SIDs_used(self.highest_sid))

