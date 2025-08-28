"""sid plugin

Plugin used to generate or update .sid files.
Please refer to RFC 9595: YANG Schema Item iDentifier, [I-D.ietf-core-comi],
[I-D.ietf-core-yang-cbor], [I-D.ietf-core-yang-library],
and RFC 7951: JSON Encoding of Data Modeled with YANG,
for more information.

"""

import optparse
import sys
import collections
import re
import os
import errno
import json
import copy
from json import JSONDecodeError


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
                         help="Generate a .sid file based on "
                         "a previous .sid file."),
            optparse.make_option("--sid-check-file",
                         action="store",
                         type="string",
                         dest="check_sid_file",
                         help="Check the consistency between a .sid file "
                         "and the .yang file(s)."),
            optparse.make_option("--sid-list",
                         action="store_true",
                         dest="list_sid",
                         help="Print the list of SID."),
            optparse.make_option("--sid-finalize",
                         action="store_true",
                         dest="finalize_sid",
                         help="Mark current allocations as non-provisional."),
            optparse.make_option("--sid-registration-info",
                         action="store_true",
                         dest="sid_registration_info",
                         help="Print the information required by "
                         "the SID registry."),
            optparse.make_option("--sid-extra-range",
                         action="store",
                         type="string",
                         dest="extra_sid_range",
                         help="Add an extra SID range during "
                         "a .sid file update."),
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
            sys.stderr.write("Invalid option, only one process " +
                "on .sid file can be requested.\n")
            return

        fatal_error = False
        for _, etag, _ in ctx.errors:
            if not error.is_warning(error.err_level(etag)):
                fatal_error = True

        if fatal_error or ctx.errors and ctx.opts.check_sid_file is not None:
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
            sid_file.update = True

        if ctx.opts.check_sid_file is not None:
            sid_file.input_file_name = ctx.opts.check_sid_file
            sid_file.check_consistency = True
            if not sid_file.sid_registration_info:
                print("Checking consistency of '%s'"
                      % sid_file.input_file_name)

        if ctx.opts.extra_sid_range is not None:
            if ctx.opts.update_sid_file is not None:
                sid_file.extra_range = ctx.opts.extra_sid_range
            else:
                sys.stderr.write("An extra SID range can be specified " +
                    "only during a .sid file update.\n")
                return

        if ctx.opts.list_sid:
            sid_file.list_content = True

        if ctx.opts.finalize_sid:
            print("Will mark unstable allocations finalized")
            sid_file.check_consistency = False
            sid_file.is_consistent = False
            sid_file.finalize_sid  = True

        try:
            sid_file.process_sid_file(modules[0])

        except SidParsingError as e:
            sys.stderr.write("ERROR, %s\n" % e)
        except SidFileError as e:
            sys.stderr.write("ERROR in '%s', %s\n" %
                             (sid_file.input_file_name, e))
        except EnvironmentError as e:
            if e.errno == errno.ENOENT:
                sys.stderr.write("ERROR, file '%s' not found\n"
                                 % e.filename)
            else:
                sys.stderr.write("ERROR, in file '%s' " % e.filename)
        except JSONDecodeError as e:
            sys.stderr.write("ERROR in '%s', %s\n"
                             % (sid_file.input_file_name, e))
        except ValueError as e:
            sys.stderr.write("ERROR in '%s', invalid JSON content\n"
                             % sid_file.input_file_name)
        else:
            sys.exit(0)
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

--sid-generate-file

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

--sid-update-file

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

-- sid-check-file

  The --sid-check-file option can be used at any time to verify if a .sid file
  need to be updated.

  Two arguments are required to verify a .sid file; the filename of the .sid
  file to be checked and the corresponding definition file.

  For example:

  $ pyang --sid-check-file toaster@2009-12-28.sid toaster@2009-12-28.yang

--sid-list

  The --sid-list option can be used before any of the previous options to
  obtains the list of SIDs assigned or validated. For example:

  $ pyang --sid-list --sid-generate-file 20000:100 toaster@2009-11-20.yang

--sid-finalize

  New allocations when during development of a protocol are marked as
  "provisional", unless --sid-finalize is specified, then they are marked with
  a status given by the module-revision of the YANG module.

  When --sid-finalize is specified, any items marked provisional are also
  marked with the module-revision.

  Otherwise, any new allocations are marked "unstable"

  $ pyang --sid-list --sid-generate-file 20000:100 --sid-finalize toaster@2009-11-20.yang""" # noqa E501
+ """

--sid-extra-range

  If needed, an extra SID range can be assigned to an existing YANG module
  during its update with the --sid-extra-range option.

  For example, this command generates the file toaster@2009-12-28.sid using
  the initial range(s) present in toaster@2009-11-20.sid and the extra range
  specified in the command line.

  $ pyang --sid-update-file toaster@2009-11-20.sid
          toaster@2009-12-28.yang --sid-extra-range 20100:100

--sid-extra-range-count
  The number of SID required when generating or updating a .sid file can be
  computed by specifying "count" as SID range.

  For example:

  $ pyang --sid-generate-file count toaster@2009-11-20.yang
  or:

  $ pyang --sid-update-file toaster@2009-11-20.sid
          toaster@2009-12-28.yang --sid-extra-range count
""")

############################################################
class SidFileError(Exception):
    pass

class SidParsingError(Exception):
    """raised by plugins to fail the emit() function"""

############################################################
class SidFile:
    IETF_SID_FILE = 'ietf-sid-file:sid-file'
    SID_FILE_STATUSES = ('published', 'unpublished')

    def __init__(self):
        self.sid_file_created = False
        self.is_consistent = True
        self.check_consistency = False
        self.list_content = False
        self.finalize_sid = False
        self.sid_registration_info = False
        self.input_file_name = None
        self.range = None
        self.extra_range = None
        self.count = False
        self.node_highest = 0
        self.content = {}
        self.module_name = ''
        self.module_revision = ''
        self.output_file_name = ''
        self.update = False

    def process_sid_file(self, module):
        self.module_name = module.i_modulename
        self.module_revision = util.get_latest_revision(module)
        if self.module_revision != 'unknown':
            self.output_file_name = \
                    f"{self.module_name}@{self.module_revision}.sid"
        else:
            self.output_file_name = f"{self.module_name}.sid"

        if self.range is not None:
            if self.range == 'count':
                self.count = True
            else:
                self.set_sid_range(self.range)

        if self.input_file_name is not None:
            if not self.input_file_name.endswith(".sid"):
                raise SidParsingError("File '%s' is not a .sid file"
                                      % self.input_file_name)

            with open(self.input_file_name) as f:
                cont = json.load(f)

            sid_cont = cont.get(self.IETF_SID_FILE, None)
            if sid_cont is None or len(cont) != 1:
                raise SidFileError("File %s is not a valid .sid file"
                                   % self.input_file_name)

            self.content = SidFile.str_to_uint64(sid_cont)

            # Upgrades can be removed after a reasonable transition period.
            self.upgrade_sid_file_format()
            self.validate_key_and_value()
            self.validate_overlapping_ranges()
            self.validate_sid()

        if self.extra_range is not None:
            if self.extra_range == 'count':
                self.count = True
            else:
                self.set_sid_range(self.extra_range)
                self.validate_overlapping_ranges()

        self.set_module_information()
        self.collect_module_items(module)
        self.build_dependencies(module)

        if self.range == 'count':
            number_of_unassigned_yang_items = \
                    self.number_of_unassigned_yang_items()
            print("\nThis YANG module requires %d SIDs."
                  % number_of_unassigned_yang_items)
            return

        if self.extra_range == 'count':
            number_of_sids_allocated = self.number_of_sids_allocated()
            number_of_sids_used = self.number_of_sids_used()
            number_of_sids_available = \
                    number_of_sids_allocated - number_of_sids_used
            number_of_unassigned_yang_items = \
                    self.number_of_unassigned_yang_items()

            print("\nNumber of SIDs allocated to this module: %d"
                  % number_of_sids_allocated)
            print("Number of SIDs required by this version: %d"
                  % (number_of_sids_used + number_of_unassigned_yang_items))
            if number_of_unassigned_yang_items > number_of_sids_available:
                print("\nAn extra range of at least " +
                      f"{number_of_unassigned_yang_items - number_of_sids_available} " + # noqa: E501
                      "SIDs is required to perform this update.")
            else:
                print("\nThe update of the .sid file can be performed using "
                      "the currently available SIDs.")
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
                print("\nThe .sid file needs to be updated.")
        else:
            if self.is_consistent:
                print("No .sid file generated, the current .sid file " +
                      "is already up to date.")
            else:
                self.generate_file()
                if self.sid_file_created:
                    print("\nFile %s created" % self.output_file_name)
                else:
                    print("\nFile %s updated" % self.output_file_name)

                print("Number of SIDs available : %d"
                      % self.number_of_sids_allocated())
                print("Number of SIDs used : %d" % self.number_of_sids_used())


    ########################################################
    def set_sid_range(self, srange):
        match = re.match(r'^(\d+):(\d+)$', srange)
        if not match:
            raise SidParsingError("invalid range in argument, must be " +
                "'<entry-point>:<size>'.")
        components = match.groups()

        aranges = self.content.get('assignment-range')
        if aranges is None:
            self.content['assignment-range'] = aranges = []
        aranges.append(collections.OrderedDict(
            [('entry-point', int(components[0])),
             ('size', int(components[1]))]))

    ########################################################
    # Set the 'module-name' and/or 'module-revision' in the .sid file
    # if they differ
    def set_module_information(self):
        if self.module_name != self.content.get('module-name'):
            self.content['module-name'] = self.module_name
            if self.check_consistency:
                print("ERROR, Mismatch between the module name defined "
                      "in the .sid file and the .yang file.")
                self.is_consistent = False

        if self.module_revision != self.content.get('module-revision'):
            self.content['module-revision'] = self.module_revision
            if self.check_consistency:
                print("ERROR, Mismatch between the module revision defined "
                      "in the .sid file and the .yang file.")
                self.is_consistent = False

    ########################################################
    # Verify the tag and data type of each .sid file JSON object
    def validate_key_and_value(self):
        module_name_absent = True

        for key in self.content:
            if key == 'module-name':
                # Further validation will be done during searching the module
                module_name_absent = False

            elif key == 'module-revision':
                if not isinstance(self.content[key], str):
                    raise SidFileError("key 'module-revision', " +
                        "invalid value")
                if not re.match("[0-9]{4}-[0-9]{2}-[0-9]{2}",
                                self.content[key]):
                    raise SidFileError("key 'module-revision', " +
                        "invalid format")

            elif key == 'sid-file-version':
                if not isinstance(self.content[key], int):
                    raise SidFileError("key 'sid-file-version', " +
                        "invalid value.")

                if self.content[key] < 0 or self.content[key] >= 2**32:
                    raise SidFileError("key 'sid-file-version " +
                        "out of valid range (uint32)")

            elif key == 'sid-file-status':
                if self.content[key] not in self.SID_FILE_STATUSES:
                    raise SidFileError("key 'sid-file-status' " +
                                       "has invalid enum value")

            elif key == 'description':
                if not isinstance(self.content[key], str):
                    raise SidFileError("key 'description', invalid value.")

            elif key == 'dependency-revision':
                if not isinstance(self.content[key], list):
                    raise SidFileError("key 'dependency-revision', " +
                                       "invalid value")
                self.validate_dep_revisions(self.content[key])

            elif key == 'assignment-range':
                if not isinstance(self.content[key], list):
                    raise SidFileError("key 'assignment-range', " +
                                       "invalid  value.")
                self.validate_ranges(self.content[key])

            elif key == 'item':
                if not isinstance(self.content[key], list):
                    raise SidFileError("key 'item', invalid value.")
                self.validate_items(self.content[key])

            else:
                raise SidFileError("invalid field '%s'." % key)

        if module_name_absent:
            raise SidFileError("mandatory field 'module-name' not present")


    @staticmethod
    def validate_dep_revisions(revisions):
        for dep_rev in revisions:
            mod_name = dep_rev.get('module-name', None)
            if mod_name is None:
                raise SidFileError("mandatory field 'module-name' " +
                    "of 'dependency-revision' not present")

            mod_rev = dep_rev.get('module-revision', None)
            if mod_rev is None:
                raise SidFileError("mandatory field 'module-revision' " +
                    "of 'dependency-revision' not present")

            if len(dep_rev) != 2:
                raise SidFileError("unknown key in 'dependency-revision' list")


    @staticmethod
    def validate_ranges(ranges):
        for arange in ranges:
            entry_point_absent = True
            size_absent = True

            for key in arange:
                if key == 'entry-point':
                    entry_point_absent = False
                    if not isinstance(arange[key], util.int_types):
                        raise SidFileError("invalid 'entry-point' value '%s'."
                                           % arange[key])

                elif key == 'size':
                    size_absent = False
                    if not isinstance(arange[key], util.int_types):
                        raise SidFileError("invalid 'size' value '%s'."
                                           % arange[key])

                else:
                    raise SidFileError("invalid key '%s'." % key)

            if entry_point_absent:
                raise SidFileError("mandatory field 'entry-point' not present")

            if size_absent:
                raise SidFileError("mandatory field 'size' not present")

    item_namespaces = ('module', 'identity', 'feature', 'data')
    item_statuses = ('unstable', 'stable', 'obsolete')

    def validate_items(self, items):
        for item in items:
            namespace_absent = True
            identifier_absent = True
            sid_absent = True

            for key in item:
                if key == 'namespace':
                    namespace_absent = False
                    if item[key] not in self.item_namespaces:
                        raise SidFileError("invalid 'namespace' value '%s'."
                                           % item[key])

                elif key == 'identifier':
                    identifier_absent = False
                    if not isinstance(item[key], str):
                        raise SidFileError("invalid 'identifier' value '%s'."
                                           % item[key])

                elif key == 'sid':
                    sid_absent = False
                    if not isinstance(item[key], util.int_types):
                        raise SidFileError("invalid 'sid' value '%s'."
                                           % item[key])

                elif key == 'status':
                    if not item[key] in self.item_statuses:
                        raise SidFileError("invalid 'status' value '%s'."
                                           % item[key])

                else:
                    raise SidFileError("invalid key '%s'." % key)

            if namespace_absent:
                raise SidFileError("mandatory field 'namespace' not present")

            if identifier_absent:
                raise SidFileError("mandatory field 'identifier' not present")

            if sid_absent:
                raise SidFileError("mandatory field 'sid' not present")

    ########################################################
    # Verify if each range defined in the .sid file is distinct
    def validate_overlapping_ranges(self):
        assignment_ranges = self.content.get('assignment-range')
        if not assignment_ranges:
            return
        used = []

        for arange in assignment_ranges:
            low = arange['entry-point']
            high = low + arange['size']

            for used_low, used_high in used:
                if used_low <= low < used_high or low <= used_low < high:
                    raise SidFileError("overlapping ranges are not allowed.")
            used.append((low, high))

    ########################################################
    # Verify if each SID listed in items is in range and is not duplicate.
    def validate_sid(self):
        if self.content['item'] is not None:
            self.content['item'].sort(key=lambda item: item['sid'])
        last_sid = -1
        for item in self.content['item']:
            sid = item['sid']
            if self.out_of_ranges(sid):
                raise SidFileError("'sid' %d not within 'assignment-range'"
                                   % sid)
            if sid == last_sid:
                raise SidFileError("duplicated 'sid' value %d " % sid)
            last_sid = sid

    def out_of_ranges(self, sid):
        for arange in self.content.get('assignment-range') or []:
            if arange['entry-point'] <= sid and \
                    sid < arange['entry-point'] + arange['size']:
                return False
        return True

    # Groups of keywords with same handling in some method below,
    # named after a representative
    leaf_keywords = ('leaf', 'leaf-list', 'anyxml', 'anydata')
    container_keywords = ('container', 'list')
    module_container_keywords = ('container', 'list',
                                 ('ietf-yang-structure-ext', 'structure'))
    choice_keywords = ('choice', 'case')
    inrpc_keywords = ('input', 'output')
    module_keywords = ('module', 'container', 'list', 'notification',
                       'rpc', 'action')

    @staticmethod
    def has_yang_data_extension(statement):
        try:
            return statement.i_extension.arg == 'yang-data'
        except AttributeError:
            return False

    ########################################################
    # Collection of items defined in .yang file(s)
    def collect_module_items(self, module):
        if 'item' not in self.content:
            self.content['item'] = []

        for item in self.content['item']:
            # Set to 'd' deleted, updated to 'o' if present in .yang file
            item['lifecycle'] = 'd'

        self.merge_item('module', self.module_name)

        for name in module.i_ctx.modules:
            if module.i_ctx.modules[name].keyword == 'submodule':
                self.merge_item('module', module.i_ctx.modules[name].arg)

        for feature in module.i_features:
            self.merge_item('feature', feature)

        for statement in module.i_children:
            if statement.keyword in self.leaf_keywords:
                self.merge_item('data', self.get_path(statement))

            elif (statement.keyword in self.module_container_keywords or 
                  statement.keyword in self.choice_keywords):
                self.merge_item('data', self.get_path(statement))
                self.collect_inner_data_nodes(statement.i_children)

            elif statement.keyword == 'rpc':
                self.merge_item('data',
                                "/%s:%s" % (self.module_name, statement.arg))
                for substmt in statement.i_children:
                    if substmt.keyword in self.inrpc_keywords:
                        # RFC 9595, Appendix B require to create SID for all
                        # rpc input and output schema nodes
                        # (this is needed during schema augmentation)
                        self.merge_item('data', self.get_path(substmt))
                        self.collect_inner_data_nodes(substmt.i_children)

            elif statement.keyword == 'notification':
                self.merge_item('data',
                                "/%s:%s" % (self.module_name, statement.arg))
                self.collect_inner_data_nodes(statement.i_children)

        for identity in module.i_identities:
            self.merge_item('identity', identity)

        for substmt in module.substmts:
            if substmt.keyword == 'augment':
                self.collect_in_substmts(substmt.substmts)
            elif self.has_yang_data_extension(substmt):
                self.collect_in_substmts(substmt.substmts)
            elif substmt.keyword == \
                    ('ietf-yang-structure-ext', 'augment-structure'):
                self.collect_in_substmts(substmt.substmts)

    def collect_inner_data_nodes(self, statements, prefix=""):
        for statement in statements:
            if statement.keyword in self.leaf_keywords:
                self.merge_item('data', self.get_path(statement, prefix))

            elif (statement.keyword in self.container_keywords or
                  statement.keyword in self.choice_keywords):
                self.merge_item('data', self.get_path(statement, prefix))
                self.collect_inner_data_nodes(statement.i_children, prefix)

            elif statement.keyword == 'action':
                self.merge_item('data', self.get_path(statement, prefix))
                for substmt in statement.i_children:
                    if substmt.keyword in self.inrpc_keywords:
                        # RFC 9595, Appendix B require to create SID for all
                        # action input and output schema nodes
                        # (this is needed during schema augmentation)
                        self.merge_item('data', self.get_path(substmt))
                        self.collect_inner_data_nodes(substmt.i_children,
                                                      prefix)

            elif statement.keyword == 'notification':
                self.merge_item('data', self.get_path(statement, prefix))
                self.collect_inner_data_nodes(statement.i_children, prefix)

    def collect_in_substmts(self, substmts):
        for statement in substmts:
            if statement.keyword in self.leaf_keywords:
                self.merge_item('data', self.get_path(statement))

            elif (statement.keyword in self.container_keywords or
                  statement.keyword in self.choice_keywords):
                self.merge_item('data', self.get_path(statement))
                self.collect_in_substmts(statement.substmts)

            elif statement.keyword == 'uses':
                prefix = self.get_path(statement.parent)
                self.collect_inner_data_nodes(statement.i_grouping.i_children,
                                              prefix)

    def get_path(self, statement, prefix=""):
        path = ""

        #breakpoint()

        while statement.i_module is not None:
            if (statement.keyword != 'grouping'
                    and not self.has_yang_data_extension(statement)):
                # Locate the data node parent
                parent = statement.parent
                while parent.i_module is not None:
                    if (parent.keyword in self.module_keywords or
                            parent.keyword ==
                            ('ietf-yang-structure-ext', 'structure') or
                            parent.keyword ==
                            ('ietf-yang-structure-ext', 'augment-structure')):
                        break
                    parent = parent.parent

                if (prefix != "" or
                        (parent.i_module is not None and
                         parent.i_module == statement.i_module) or
                        (statement.keyword == 'case' and 
                         statement.i_module == statement.parent.i_module) or
                        (statement.parent.keyword == 'case' and 
                         statement.i_module == statement.parent.i_module)):
                    path = "/" + statement.arg + path
                else:
                    path = "/" + statement.i_module.arg + ":" + statement.arg \
                            + path

            statement = statement.parent

        return prefix + path

    def merge_item(self, namespace, identifier):
        for item in self.content['item']:
            if (namespace == item['namespace'] and
                    identifier == item['identifier']):
                item['lifecycle'] = 'o' # Item already assigned
                return
        self.content['item'].append(collections.OrderedDict(
            [('namespace', namespace), ('identifier', identifier),
             ('status', 'unstable'),
             ('sid', -1), ('lifecycle', 'n')]))
        self.is_consistent = False

    ########################################################
    # Create list of dependent module with optional revision
    def build_dependencies(self, module):
        imports = module.search('import')

        if 'dependency-revision' not in self.content and len(imports) > 0:
            self.content['dependency-revision'] = []

        for import_stmt in imports:
            dep = collections.OrderedDict()
            module_name = import_stmt.arg
            dep['module-name'] = module_name
            rev_stmt = import_stmt.search_one('revision-date')
            revision = rev_stmt.arg if rev_stmt is not None else None
            if revision is None:
                entries = list(filter(
                    lambda name_rev: name_rev[0] == module_name,
                    module.i_ctx.modules))

                if len(entries) == 1 and entries[0][1] == 'unknown':
                    pass
                else:
                    latest = ''
                    for ent in entries:
                        if ent[1] == 'unknown':
                            continue
                        if ent[1] > latest:
                            latest = ent[1]

                    if latest == '':
                        # We could not have 2 or more modules with same named
                        # and no revision
                        raise SidFileError('unreachable')
                    ##assert re.match('[0-9]{4}-[0-9]{2}-[0-9]{2}', latest)

                    revision = latest
                    print(f"WARNING: Module '{module_name}' imported " +
                        f"without revision, using latest revision {latest}")

            if revision is None and module_name in module.i_ctx.revs:
                latest = ''
                for r in module.i_ctx.revs[module_name]:
                    if r[0] == 'unknown':
                        continue
                    if r[0] > latest:
                        latest = r[0]

                if latest == '':
                    raise Exception(f'The .sid file requires the imported ' +
                    'modules to have revision statement. No module ' +
                    '"{module_name}" with revision statement found.')

                revision = latest
                print(f"WARNING: Module '{module_name}' imported without " +
                    f"revision, using latest revision {latest}")

            if revision is None:
                raise SidFileError(f"Missing revision for module " +
                    f"'{module_name}' for mandatory sid-file field " +
                    "'ietf-sid-file:sid-file/dependency-revision/module-revision'.") # noqa: E501

            dep['module-revision'] = revision
            self.content['dependency-revision'].append(dep)

    ########################################################
    # Sort the items list by 'namespace' and 'identifier'
    def sort_items(self):
        self.content['item'].sort(key=lambda item: item['identifier'])
        self.content['item'].sort(key=lambda item: item['namespace'],
                                  reverse=True)

    ########################################################
    # Identifier assignment
    def assign_sid(self):
        items = self.content['item']
        unassigned = [item for item in items if item['sid'] == -1]
        if not unassigned:
            return
        used = sorted(item['sid'] for item in items if item['sid'] != -1)
        needed = len(unassigned)
        source = self.gen_sids(used)

        for item in unassigned:
            try:
                item['sid'] = next(source)
                item['status'] = 'unstable'
            except StopIteration:
                raise SidParsingError(
                    "The current SID range(s) are exhausted, %d extra SID(s) "
                    "are required, use the --sid-extra-range option to add "
                    "a SID range to this YANG module." % needed)
            needed -= 1

    def sid_used(self, sid):
        for item in self.content['item']:
            if item['sid'] == sid:
                return True
        return False

    def gen_sids(self, used):
        ranges = sorted((arange['entry-point'], arange['size'])
                    for arange in self.content.get('assignment-range') or [])
        used_idx = 0
        used_len = len(used)
        for sid, size in ranges:
            high = sid + size
            while sid < high:
                # find next upper bound of unused sids above sid
                while used_idx < used_len:
                    stop = used[used_idx]
                    if stop < sid:
                        used_idx += 1
                    else:
                        if stop == sid:
                            # go past the used sid, recheck sid < high
                            sid += 1
                        elif stop > high:
                            # next used is above current range
                            stop = high
                        break
                else:
                    # no more used sids
                    stop = high

                while sid < stop:
                    yield sid
                    sid += 1

    ########################################################
    def list_all_items(self):
        definition_removed = False

        print("\nSID        Assigned to")
        print("---------  --------------------------------------------------")
        items = self.content['item']
        if items is not None:
            items.sort(key=lambda item: item['sid'])
        for item in items:
            status = ""
            if item['lifecycle'] == 'n' and not self.sid_file_created:
                status = " (New)"
            if item['lifecycle'] == 'd' and item['namespace'] != 'module':
                status = " (Remove)"
                definition_removed = True

            print("%-9s  %s %s%s"
                % (item['sid'], item['namespace'], item['identifier'], status))

        if definition_removed:
            print(
                "\nWARNING, obsolete definitions should be defined " +
                "as 'deprecated' or 'obsolete'.")

    ########################################################
    def list_deleted_items(self):
        definition_removed = False
        for item in self.content['item']:
            if item['lifecycle'] == 'd':
                print("WARNING, item '%s' was deleted form the .yang files."
                      % item['identifier'])
                definition_removed = True

        if definition_removed:
            print("Obsolete definitions MUST NOT be removed "
                  "from YANG modules, see RFC 6020 section 10.\n"
                  "These definition(s) should be reintroduced "
                  "with a 'deprecated' or 'obsolete' status.")

    ########################################################
    def generate_file(self):
        for item in self.content['item']:
            del item['lifecycle']

        # Ordered sid file content ('ietf-sid-file:sid-file' dictionary)
        sid_cont = collections.OrderedDict()
        sid_cont['module-name'] = self.content['module-name']
        if self.content['module-revision'] != 'unknown':
            sid_cont['module-revision'] = self.content['module-revision']
        if self.update:
            curr = self.content.get('sid-file-version', 0)
            sid_cont['sid-file-version'] = curr + 1
        if not self.finalize_sid:
            sid_cont['sid-file-status'] = 'unpublished'
        descr = self.content.get('description', None)
        if descr:
            sid_cont['description'] = descr
        dep_revision = self.content.get('dependency-revision', [])
        if dep_revision:
            sid_cont['dependency-revision'] = dep_revision
        ranges = self.content.get('assignment-range', [])
        if ranges:
            sid_cont['assignment-range'] = copy.deepcopy(ranges)
            for range in sid_cont['assignment-range']:
                # According to RFC 7951, uint64 values are represented
                # as JSON strings for interoperability
                range['entry-point'] = str(range['entry-point'])
                range['size'] = str(range['size'])

        items = self.content.get('item', [])
        if items:
            sid_cont['item'] = copy.deepcopy(items)
            sid_cont['item'].sort(key=lambda item: item['sid'])

            for item in sid_cont['item']:
                # According to RFC 7951, uint64 values are represented
                # as JSON strings for interoperability
                item['sid'] = str(item['sid'])

        if self.finalize_sid and items:
            print("Finalizing unstable allocations to %s"
                  % (self.module_revision))
            for item in sid_cont['item']:
                if item['status'] == 'unstable':
                    print("  finalized %s" % (item['identifier']))
                    # status 'stable' is default enum
                    del item['status']

        with open(self.output_file_name, 'w') as outfile:
            outfile.truncate(0)
            json.dump({self.IETF_SID_FILE: sid_cont}, outfile, indent=2)

    ########################################################
    def number_of_sids_allocated(self):
        size = 0
        for arange in self.content.get('assignment-range') or []:
            size += arange['size']
        return size

    def number_of_unassigned_yang_items(self):
        return len([0 for item in self.content['item'] if item['sid'] == -1])

    def number_of_sids_used(self):
        return len([0 for item in self.content['item'] if item['sid'] != -1])

    def number_of_sids_used_in_range(self, entry_point, size):
        low = entry_point
        high = low + size
        return len([0 for item in self.content['item']
                if low <= item['sid'] < high])

    ########################################################
    def print_registration_information(self, module):
        ranges = []
        submodules = []
        info = {
            'module_name' : self.module_name,
            'module_revision' : self.module_revision,
            'yang_file' : '%s@%s.yang'
                    % (self.module_name, self.module_revision),
            'ranges' : ranges,
            'submodules' : submodules,
        }

        for arange in self.content('assignment-range') or []:
            ranges.append({
                'entry_point' : arange['entry-point'],
                'size' : arange['size'],
                'used' : self.number_of_sids_used_in_range(
                    arange['entry-point'], arange['size'])
            })

        for name in module.i_ctx.modules:
            submodule = module.i_ctx.modules[name]
            if submodule.keyword == 'submodule':
                submodules.append('%s@%s.yang'
                                % (submodule.arg, submodule.i_latest_revision))

        print(json.dumps(info, indent=2))

    ########################################################
    # Perform the conversion to the .sid file fromat
    # introduced by [I-D.ietf-core-sid] version 3.
    # This method can be removed after the proper transition period.

    node_keywords = ('node', 'notification', 'rpc', 'action')

    def upgrade_sid_file_format(self):
        items = self.content.get('item')
        if not items:
            return

        for item in items:
            type_ = item.pop('type', None)
            label = item.pop('label', None)
            if not type_:
                pass
            elif type_ in ('Module', 'Submodule'):
                item['namespace'] = 'module'
                item['identifier'] = label

            elif type_ == 'feature':
                item['namespace'] = type_
                item['identifier'] = label

            elif type_ == 'identity':
                item['namespace'] = type_
                item['identifier'] = label.rsplit('/', 1)[-1]

            elif type_ in self.node_keywords:
                item['namespace'] = 'data'
                item['identifier'] = '/' + self.module_name + ':' + label[1:]

    @staticmethod
    def str_to_uint64(sid_cont: dict) -> dict:
        ranges = sid_cont.get('assignment-range', [])
        for range in ranges:
            if 'entry-point' not in range:
                raise SidFileError("mandatory key 'entry-point' not present")
            if 'size' not in range:
                raise SidFileError("mandatory field 'size' not present")

            range['entry-point'] = int(range['entry-point'])
            range['size'] = int(range['size'])

        items = sid_cont.get('item', [])
        for item in items:
            if 'sid' not in item:
                raise SidFileError("mandatory field 'sid' not present")
            item['sid'] = int(item['sid'])

        return sid_cont
