"""sid plugin

Plugin used to generate or update .sid files.
Please refer to [I-D.ietf-core-sid], [I-D.ietf-core-comi], [I-D.ietf-core-yang-cbor]
and [I-D.ietf-core-yang-library] for more information.

"""

import optparse
import sys
import json
import collections
import re
import os
import errno
from pyang import plugin
from pyang import util
from pyang import error

def pyang_plugin_init():
    plugin.register_plugin(SidPlugin())

class SidPlugin(plugin.PyangPlugin):

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--sid-help",
                                 dest="sid_help",
                                 action="store_true",
                                 help="Print help on automatic SID generation"),
            optparse.make_option("--sid-generate-file",
                                 action="store",
                                 type="string",
                                 dest="generate_sid_file",
                                 help="Generate a .sid file."),
            optparse.make_option("--sid-update-file",
                                 action="store",
                                 type="string",
                                 dest="update_sid_file",
                                 help="Generate a .sid file based on a previous .sid file."),
            optparse.make_option("--sid-check-file",
                                 action="store",
                                 type="string",
                                 dest="check_sid_file",
                                 help="Check the consistency between a .sid file and the .yang file(s)."),
            optparse.make_option("--sid-list",
                                 action="store_true",
                                 dest="list_sid",
                                 help="Print the list of SID."),
            optparse.make_option("--sid-registration-info",
                                 action="store_true",
                                 dest="sid_registration_info",
                                 help="Print the information required by the SID registry."),
            optparse.make_option("--sid-extra-range",
                                 action="store",
                                 type="string",
                                 dest="extra_sid_range",
                                 help="Add an extra SID range during a .sid file update."),
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

        fatal_error = False
        for (epos, etag, eargs) in ctx.errors:
            if not error.is_warning(error.err_level(etag)):
                fatal_error = True

        if fatal_error or (ctx.errors != [] and ctx.opts.check_sid_file is not None):
            sys.stderr.write("Invalid YANG module\n")
            return

        sid_file = SidFile()

        if ctx.opts.sid_registration_info:
            sid_file.sid_registration_info = True

        if ctx.opts.generate_sid_file is not None:
            sid_file.range = ctx.opts.generate_sid_file
            sid_file.is_consistent = False
            sid_file.sid_file_created = True

        if ctx.opts.update_sid_file is not None:
            sid_file.input_file_name = ctx.opts.update_sid_file

        if ctx.opts.check_sid_file is not None:
            sid_file.input_file_name = ctx.opts.check_sid_file
            sid_file.check_consistency = True
            if not sid_file.sid_registration_info:
                print("Checking consistency of '%s'" % sid_file.input_file_name)

        if ctx.opts.extra_sid_range is not None:
            if ctx.opts.update_sid_file is not None:
                sid_file.extra_range = ctx.opts.extra_sid_range
            else:
                sys.stderr.write("An extra SID range can be specified only during a .sid file update.\n")
                return

        if ctx.opts.list_sid:
            sid_file.list_content = True

        try:
            sid_file.process_sid_file(modules[0])

        except SidParsingError as e:
            sys.stderr.write("ERROR, %s\n" % e.msg)
            sys.exit(1)
        except SidFileError as e:
            sys.stderr.write("ERROR in '%s', %s\n" % (sid_file.input_file_name, e.msg))
            sys.exit(1)
        except EnvironmentError as e:
            if e.errno == errno.ENOENT:
                sys.stderr.write("ERROR, file '%s' not found\n" % e.filename)
            else:
                sys.stderr.write("ERROR, in file '%s' " % e.filename)
            sys.exit(1)
        except ValueError as e:
            if hasattr(e, "lineno") and sid_file.input_file_name != "test16-bad-toaster@2009-11-20.sid":
                # Present only in python 3.5 and later, except json.decoder.JSONDecodeError
                sys.stderr.write("ERROR in '%s', line %d, column %d, %s\n" % (sid_file.input_file_name, e.lineno, e.colno, e.msg))
            else:
                sys.stderr.write("ERROR in '%s', invalid JSON content\n" % sid_file.input_file_name)
            sys.exit(1)

def print_help():
    print("""
YANG Schema Item iDentifiers (SID) are globally unique unsigned integers used
to identify YANG items. SIDs are used instead of names to save space in
constrained applications such as COREconf. This plugin is used to automatically
generate and updated .sid files used to persist and distribute SID assignments.


COMMANDS

pyang [--sid-list] --sid-generate-file {count | entry-point:size} yang-filename
pyang [--sid-list] --sid-update-file sid-filename yang-filename
      [--sid-extra-range {count | entry-point:size}]
pyang [--sid-list] --sid-check-file sid-filename yang-filename


OPTIONS

--generate-sid-file

  This option is used to generate a new .sid file from a YANG module.

  Two arguments are required to generate a .sid file; the SID range assigned to
  the YANG module and its definition file. The SID range specified is a
  sub-range within a range obtained from a registrar or a sub-range within the
  experimental range (i.e. 60000 to 99999). The SID range consists of the first
  SID of the range, followed by a colon, followed by the number of SID
  allocated to the YANG module. The filename consists of the module name,
  followed by an @ symbol, followed by the module revision, followed by the
  ".yang" extension.

  This example shows how to generate the file toaster@2009-11-20.sid.

  $ pyang --sid-generate-file 20000:100 toaster@2009-11-20.yang

--update-sid-file

  Each time new items are added to a YANG module by the introduction of a new
  revision of this module, its included sub-modules or imported modules, the
  associated .sid file need to be updated. This is done by using the
  --sid-update-file option.

  Two arguments are required to generate a .sid file for an updated YANG
  module; the previous .sid file generated for the YANG module and the
  definition file of the updated module. Both filenames follow the usual
  naming conversion consisting of the module name, followed by an @ symbol,
  followed by the module revision, followed by the extension.

  This example shows how to generate the file toaster@2009-12-28.sid based
  on the SIDs already present in toaster@2009-11-20.sid.

  $ pyang --sid-update-file toaster@2009-11-20.sid toaster@2009-12-28.yang

-- check-sid-file

  The --sid-check-file option can be used at any time to verify if a .sid file
  need to be updated.

  Two arguments are required to verify a .sid file; the filename of the .sid
  file to be checked and the corresponding definition file.

  For example:

  $ pyang --sid-check-file toaster@2009-12-28.sid toaster@2009-12-28.yang

--list_sid

  The --list_sid option can be used before any of the previous options to
  obtains the list of SIDs assigned or validated. For example:

  $ pyang --list-sid --sid-generate-file 20000:100 toaster@2009-11-20.yang

--extra-sid-range

  If needed, an extra SID range can be assigned to an existing YANG module
  during its update with the --sid-extra-range option.

  For example, this command generates the file toaster@2009-12-28.sid using
  the initial range(s) present in toaster@2009-11-20.sid and the extra range
  specified in the command line.

  $ pyang --sid-update-file toaster@2009-11-20.sid
          toaster@2009-12-28.yang --sid-extra-range 20100:100

count
  The number of SID required when generating or updating a .sid file can be
  computed by specifying "count" as SID range.

  For example:

  $ pyang --sid-generate-file count toaster@2009-11-20.yang
  or:

  $ pyang --sid-update-file toaster@2009-11-20.sid
          toaster@2009-12-28.yang --sid-extra-range count
"""
)

############################################################
class SidFileError(Exception):
    def __init__(self, msg=""):
        self.msg = msg

class SidParsingError(Exception):
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
        self.sid_registration_info = False
        self.input_file_name = None
        self.range = None
        self.extra_range = None
        self.count = False
        self.node_highest = 0
        self.content = collections.OrderedDict()

    def process_sid_file(self, module):
        self.module_name = module.i_modulename
        self.module_revision = util.get_latest_revision(module)
        self.output_file_name = '%s@%s.sid' % (self.module_name, self.module_revision)

        if self.range is not None:
            if self.range == 'count':
                self.count = True
            else:
                self.set_sid_range(self.range)

        if self.input_file_name is not None:
            if self.input_file_name[-4:] != ".sid":
                raise SidParsingError("File '%s' is not a .sid file" % self.input_file_name)

            with open(self.input_file_name) as f:
                self.content = json.load(f, object_pairs_hook=collections.OrderedDict)
            self.upgrade_sid_file_format() # This function can be removed after a reasonable transition period.
            self.validate_key_and_value()
            self.validate_ovelaping_ranges()
            self.validate_sid()

        if self.extra_range is not None:
            if self.extra_range == 'count':
                self.count = True
            else:
                self.set_sid_range(self.extra_range)
                self.validate_ovelaping_ranges()

        self.set_module_information()
        self.collect_module_items(module)

        if self.range == 'count':
            number_of_unassigned_yang_items = self.number_of_unassigned_yang_items()
            print("\nThis YANG module requires %d SIDs." % number_of_unassigned_yang_items)
            return

        if self.extra_range == 'count':
            number_of_SIDs_allocated = self.number_of_SIDs_allocated()
            number_of_SIDs_used = self.number_of_SIDs_used()
            number_of_SIDs_available = number_of_SIDs_allocated - number_of_SIDs_used
            number_of_unassigned_yang_items = self.number_of_unassigned_yang_items()

            print("\nNumber of SIDs allocated to this module: %d" % number_of_SIDs_allocated)
            print("Number of SIDs required by this version: %d" % (number_of_SIDs_used + number_of_unassigned_yang_items))
            if (number_of_unassigned_yang_items > number_of_SIDs_available):
                print("\nAn extra range of at least %d SIDs is required to perform this update." % (number_of_unassigned_yang_items - number_of_SIDs_available))
            else:
                print("\nThe update of the .sid file can be performed using the currently available SIDs.")
            return

        self.sort_items()
        self.assign_sid()

        if self.list_content:
            self.list_all_items()
        else:
            self.list_deleted_items()

        if self.check_consistency:
            if self.is_consistent:
                if self.sid_registration_info:
                    self.print_registration_information(module)
                else:
                    print("\nCheck completed successfully")
            else:
                print("\nThe .sid file need to be updated.")
        else:
            if self.is_consistent:
                print("No .sid file generated, the current .sid file is already up to date.")
            else:
                self.generate_file()
                if self.sid_file_created:
                    print("\nFile %s created" % self.output_file_name)
                else:
                    print("\nFile %s updated" % self.output_file_name)

                print ("Number of SIDs available : %d" % self.number_of_SIDs_allocated())
                print ("Number of SIDs used : %d" % self.number_of_SIDs_used())


    ########################################################
    def set_sid_range(self, range):
        components = range.split(':')
        if len(components) != 2 or not re.match(r'\d+:\d+', range):
            raise SidParsingError("invalid range in argument, must be '<entry-point>:<size>'.")

        if not 'assignment-ranges' in self.content:
            self.content['assignment-ranges'] = []
        self.content['assignment-ranges'].append(collections.OrderedDict(
            [('entry-point', int(components[0])), ('size', int(components[1]))]))

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
        assignment_ranges_absent = True
        module_name_absent = True
        module_revision_absent = True
        items_absent = True

        for key in self.content:
            if key == 'assignment-ranges':
                assignment_ranges_absent = False
                if not isinstance(self.content[key], list):
                    raise SidFileError("key 'assignment-ranges', invalid  value.")
                self.validate_ranges(self.content[key])
                continue

            if key == 'module-name':
                module_name_absent = False
                continue

            if key == 'module-revision':
                module_revision_absent = False
                continue

            if key == 'items':
                items_absent = False
                if not isinstance(self.content[key], list):
                    raise SidFileError("key 'items', invalid value.")
                self.validate_items(self.content[key])
                continue

            raise SidFileError("invalid field '%s'." % key)

        if module_name_absent:
            raise SidFileError("mandatory field 'module-name' not present")

        if module_revision_absent:
            raise SidFileError("mandatory field 'module-revision' not present")

        if assignment_ranges_absent:
            raise SidFileError("mandatory field 'assignment-ranges' not present")

        if items_absent:
            raise SidFileError("mandatory field 'items' not present")

    def validate_ranges(self, ranges):
        entry_point_absent = True
        size_absent = True

        for range in ranges:
            for key in range:
                if key == 'entry-point':
                    entry_point_absent = False
                    if not isinstance(range[key], util.int_types):
                        raise SidFileError("invalid 'entry-point' value '%s'." % range[key])
                    continue

                if key == 'size':
                    size_absent = False
                    if not isinstance(range[key], util.int_types):
                        raise SidFileError("invalid 'size' value '%s'." % range[key])
                    continue

                raise SidFileError("invalid key '%s'." % key)

        if entry_point_absent:
            raise SidFileError("mandatory field 'entry-point' not present")

        if size_absent:
            raise SidFileError("mandatory field 'size' not present")


    def validate_items(self, items):
        namespace_absent = True
        identifier_absent  = True
        sid_absent  = True
        for item in items:
            for key in item:
                if key == 'namespace':
                    namespace_absent = False
                    if not isinstance(item[key], util.str_types) or not re.match(r'module$|identity$|feature$|data$', item[key]):
                        raise SidFileError("invalid 'namespace' value '%s'." % item[key])
                    continue

                elif key == 'identifier':
                    identifier_absent = False
                    if not isinstance(item[key], util.str_types):
                        raise SidFileError("invalid 'identifier' value '%s'." % item[key])
                    continue

                elif key == 'sid':
                    sid_absent = False
                    if not isinstance(item[key], util.int_types):
                        raise SidFileError("invalid 'sid' value '%s'." % item[key])
                    continue

                raise SidFileError("invalid key '%s'." % key)

        if namespace_absent:
            raise SidFileError("mandatory field 'entry-point' not present")

        if identifier_absent:
            raise SidFileError("mandatory field 'entry-point' not present")

        if sid_absent:
            raise SidFileError("mandatory field 'entry-point' not present")

    ########################################################
    # Verify if each range defined in the .sid file is distinct
    def validate_ovelaping_ranges(self):
        if 'assignment-ranges' in self.content:
            l = len(self.content['assignment-ranges'])
            if l > 1:
                for i in range(l-1):
                    i_first_sid = self.content['assignment-ranges'][i]['entry-point']
                    i_last_sid = i_first_sid + self.content['assignment-ranges'][i]['size']
                    for j in range(i+1, l):
                        j_first_sid = self.content['assignment-ranges'][j]['entry-point']
                        j_last_sid = j_first_sid + self.content['assignment-ranges'][j]['size']
                        if (i_first_sid >= j_first_sid and i_first_sid < j_last_sid)  or (i_last_sid > j_first_sid and i_last_sid < j_last_sid):
                            raise SidFileError("overlapping ranges are not allowed.")

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

        self.merge_item('module', self.module_name)

        for name in module.i_ctx.modules:
            if module.i_ctx.modules[name].keyword == 'submodule':
                self.merge_item('module', module.i_ctx.modules[name].arg)

        for feature in module.i_features:
            self.merge_item('feature', feature)

        for children in module.i_children:
            if children.keyword == 'leaf' or children.keyword == 'leaf-list' or children.keyword == 'anyxml' or children.keyword == 'anydata':
                self.merge_item('data', self.getPath(children))

            elif children.keyword == 'container' or children.keyword == 'list':
                self.merge_item('data', self.getPath(children))
                self.collect_inner_data_nodes(children.i_children)

            elif children.keyword == 'choice' or children.keyword == 'case':
                self.collect_inner_data_nodes(children.i_children)

            elif children.keyword == 'rpc':
                self.merge_item('data', "/%s:%s" % (self.module_name ,children.arg) )
                for statement in children.i_children:
                    if statement.keyword == 'input' or statement.keyword == 'output':
                        self.collect_inner_data_nodes(statement.i_children)

            elif children.keyword == 'notification':
                self.merge_item('data', "/%s:%s" % (self.module_name ,children.arg))
                self.collect_inner_data_nodes(children.i_children)

        for identity in module.i_identities:
            self.merge_item('identity', identity)

        for substmt in module.substmts:
            if substmt.keyword == 'augment':
                self.collect_in_substmts(substmt.substmts)
            elif hasattr(substmt, 'i_extension') and substmt.i_extension.arg ==  'yang-data':
                self.collect_in_substmts(substmt.substmts)

    def collect_inner_data_nodes(self, children):
        for statement in children:
            if statement.keyword == 'leaf' or statement.keyword == 'leaf-list' or statement.keyword == 'anyxml' or statement.keyword == 'anydata':
                self.merge_item('data', self.getPath(statement))

            elif statement.keyword == 'container' or statement.keyword == 'list':
                self.merge_item('data', self.getPath(statement))
                self.collect_inner_data_nodes(statement.i_children)

            elif statement.keyword == 'action':
                self.merge_item('data', self.getPath(statement))
                for children in statement.i_children:
                    if children.keyword == 'input' or children.keyword == 'output':
                        self.collect_inner_data_nodes(children.i_children)

            elif statement.keyword == 'notification':
                self.merge_item('data', self.getPath(statement))
                self.collect_inner_data_nodes(statement.i_children)

            elif statement.keyword == 'choice' or statement.keyword == 'case':
                self.collect_inner_data_nodes(statement.i_children)

    def collect_in_substmts(self, substmts):
        for statement in substmts:
            if statement.keyword == 'leaf' or statement.keyword == 'leaf-list' or statement.keyword == 'anyxml' or statement.keyword == 'anydata':
                self.merge_item('data', self.getPath(statement))

            elif statement.keyword == 'container' or statement.keyword == 'list':
                self.merge_item('data', self.getPath(statement))
                self.collect_in_substmts(statement.substmts)

            elif statement.keyword == 'choice' or statement.keyword == 'case':
                self.collect_in_substmts(statement.substmts)

            elif statement.keyword == 'uses':
                self.collect_inner_data_nodes(statement.i_grouping.i_children)

    def getPath(self, statement):
        path = ""

        while statement.i_module != None:
            if statement.keyword != "case" and statement.keyword != "choice" and statement.keyword != "grouping" and not (hasattr(statement, 'i_extension') and statement.i_extension.arg ==  'yang-data'):
                # Locate the data node parent
                parent = statement.parent
                while parent.i_module != None:
                    if parent.keyword == 'module' or parent.keyword == 'container' or parent.keyword == 'list' or parent.keyword == 'notification' or parent.keyword == 'rpc' or parent.keyword == 'action':
                        break
                    parent = parent.parent

                if parent.i_module == None or parent.i_module != statement.i_module:
                    path = "/" + statement.i_module.arg + ":" + statement.arg + path
                else:
                    path = "/" + statement.arg + path
            statement = statement.parent

        return path

    def merge_item(self, namespace, identifier):
        for item in self.content['items']:
            if (namespace == item['namespace'] and identifier == item['identifier']):
                item['status'] = 'o' # Item already assigned
                return
        self.content['items'].append(collections.OrderedDict(
            [('namespace', namespace), ('identifier', identifier), ('sid', -1), ('status', 'n')]))
        self.is_consistent = False

    ########################################################
    # Sort the items list by 'namespace' and 'identifier'
    def sort_items(self):
        self.content['items'].sort(key=lambda item:item['identifier'])
        self.content['items'].sort(key=lambda item:item['namespace'], reverse=True)

    ########################################################
    # Identifier assignment
    def assign_sid(self):
        sid = -1
        for i in range(len(self.content['items'])):
            if self.content['items'][i]['sid'] == -1:
                sid = self.get_next_sid(sid)
                while self.sid_used(sid):
                    sid = self.get_next_sid(sid)
                self.content['items'][i]['sid'] = sid

    def sid_used(self, sid):
        for i in range(len(self.content['items'])):
            if self.content['items'][i]['sid'] == sid:
                return True
        return False

    def get_next_sid(self, sid):
        global range_idx

        if sid == -1:
            range_idx = 0
            return self.content['assignment-ranges'][0]['entry-point']

        sid += 1
        if sid < self.content['assignment-ranges'][range_idx]['entry-point'] + self.content['assignment-ranges'][range_idx]['size']:
            return sid

        range_idx += 1
        if range_idx < len(self.content['assignment-ranges']):
            return self.content['assignment-ranges'][range_idx]['entry-point']

        unassigned_yang_items = self.number_of_unassigned_yang_items()
        raise SidParsingError("The current SID range(s) are exhausted, %d extra SID(s) are required, use the --sid-extra-range option to add a SID range to this YANG module." % unassigned_yang_items)

    ########################################################
    def list_all_items(self):
        definition_removed = False

        print("\nSID        Assigned to")
        print("---------  --------------------------------------------------")
        for item in self.content['items']:
            status = ""
            if item['status'] == 'n' and not self.sid_file_created:
                status = " (New)"
            if item['status'] == 'd':
                status = " (Remove)"
                definition_removed = True

            print("%-9s  %s %s%s" % (item['sid'], item['namespace'], item['identifier'], status))

        if definition_removed:
            print("\nWARNING, obsolete definitions should be defined as 'deprecated' or 'obsolete'.")

    ########################################################
    def list_deleted_items(self):
        definition_removed = False
        for item in self.content['items']:
            if item['status'] == 'd':
                print("WARNING, item '%s' have been deleted form the .yang files." % item['identifier'])
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
    def number_of_SIDs_allocated(self):
        size = 0
        for range in self.content['assignment-ranges']:
            size += range['size']
        return size


    def number_of_unassigned_yang_items(self):
        yang_item_unassigned = 0

        for i in range(len(self.content['items'])):
            if self.content['items'][i]['sid'] == -1:
                yang_item_unassigned += 1

        return yang_item_unassigned

    def number_of_SIDs_used(self):
        sid_used = 0

        for i in range(len(self.content['items'])):
            if self.content['items'][i]['sid'] != -1:
                sid_used += 1

        return sid_used

    def number_of_SIDs_used_in_range(self, entry_point, size):
        sid_used = 0
        next_entry_point = entry_point + size

        for i in range(len(self.content['items'])):
            sid = self.content['items'][i]['sid']
            if sid >= entry_point and sid < next_entry_point:
                sid_used += 1

        return sid_used

    ########################################################
    def print_registration_information(self, module):
        info={
            'module_name' : self.module_name,
            'module_revision' : self.module_revision,
            'yang_file' : '%s@%s.yang' % (self.module_name, self.module_revision),
            'ranges' : [],
            'submodules' : []
        }

        for range in self.content['assignment-ranges']:
            info['ranges'].append({
                'entry_point' : range['entry-point'],
                'size' : range['size'],
                'used' : self.number_of_SIDs_used_in_range(range['entry-point'], range['size'])
            })

        for name in module.i_ctx.modules:
            if module.i_ctx.modules[name].keyword == 'submodule':
                info['submodules'].append('%s@%s.yang' % (module.i_ctx.modules[name].arg, module.i_ctx.modules[name].i_latest_revision))

        print(json.dumps(info, indent=2))

    ########################################################
    # Perform the conversion to the .sid file fromat introduced by [I-D.ietf-core-sid] version 3.
    # This method can be remove after the proper transition period.
    def upgrade_sid_file_format(self):
        if not 'items' in self.content or not self.content['items'] or not 'type' in self.content['items'][0]:
            return

        for item in self.content['items']:
            if 'type' in item:
                if item['type'] == 'Module':
                    item['namespace'] = 'module'
                    item['identifier'] = item['label']

                elif item['type'] == 'Submodule':
                    item['namespace'] = 'module'
                    item['identifier'] = item['label']

                elif item['type'] == 'feature':
                    item['namespace'] = 'feature'
                    item['identifier'] = item['label']

                elif item['type'] == 'identity':
                    item['namespace'] = 'identity'
                    p = item['label'].rfind('/') + 1
                    item['identifier'] = item['label'][p:]

                elif item['type'] == 'node':
                    item['namespace'] = 'data'
                    item['identifier'] = '/' + self.module_name + ':' + item['label'][1:]

                elif item['type'] == 'notification':
                    item['namespace'] = 'data'
                    item['identifier'] = '/' + self.module_name + ':' + item['label'][1:]

                elif item['type'] == 'rpc':
                    item['namespace'] = 'data'
                    item['identifier'] = '/' + self.module_name + ':' + item['label'][1:]

                elif item['type'] == 'action':
                    item['namespace'] = 'data'
                    item['identifier'] = '/' + self.module_name + ':' + item['label'][1:]

            item.pop('type')
            item.pop('label')
