---
title: PYANG
section: 1
header: User Manual
footer: pyang-_VERSION_
date: _DATE_
---
# NAME
pyang - validate and convert YANG modules to various formats

# SYNOPSIS

**pyang** [-\-verbose] [-\-canonical] [-\-strict] [-\-lint] [-\-ietf]
      [-\-lax-quote-checks] [-\-lax-xpath-checks] [-\-features
      *features*] [-\-exclude-features *features*] [-\-max-status
      *maxstatus*] [-\-hello] [-\-implicit-hello-deviations]
      [-\-check-update-from *oldfile*]
      [-o *outfile*] [-t *transform*] [-f *format*] [-p *path*] [-W
      *warning*] [-E *error*] *file*...

**pyang** [-\-sid-list] -\-sid-generate-file {count |
    *entry-point:size*} *yang-filename*

**pyang** [-\-sid-list] -\-sid-update-file *sid-filename* *yang-filename*
      [-\-sid-extra-range count *entry-point:size*]

**pyang** [-\-sid-list] -\-sid-check-file *sid-filename* *yang-filename*

**pyang** -h | -\-help

**pyang** -v -\-version


One or more *file* parameters may be given on the command line. They
denote either YANG modules to be processed (in YANG or YIN syntax) or,
using the **-\-hello** switch, a server &lt;hello&gt; message
conforming to **RFC 6241** and
**RFC 6020**,
which completely defines the data model - supported YANG modules as
well as features and capabilities. In the latter case, only one *file*
parameter may be present.

If no files are given, **pyang** reads input
from stdin, which must be one module or a server &lt;hello&gt; message.

# DESCRIPTION

The **pyang** program is used to validate YANG modules (**RFC 6020** and
**RFC 7950**). It is also used to convert YANG modules into
equivalent YIN modules. From a valid module a hybrid DSDL
schema (**RFC 6110**) can be generated.

If no *format* is given, the specified modules are validated, and the
program exits with exit code 0 if all modules are valid.

# OPTIONS

**-h**, **-\-help**
:   Print a short help text and exit.

**-v**, **-\-version**
:   Print the version number and exit.

**-e**, **-\-list-errors**
:   Print a listing of all error codes and messages pyang might
    generate, and then exit.

**-\-print-error-code**
:   On errors, print the symbolic error code instead of the error message.

**-\-print-error-basename**
:   On errors, print only the base file name independent of its module
    path location.

**-Werror**
:   Treat warnings as errors.

**-Wnone**
:   Do not print any warnings.

**-W** _errorcode_
:   Treat _errorcode_ as a warning, even if **-Werror** is given.
    _errorcode_ must be a warning or a minor error.

    Use **-\-list-errors** to get a listing of all errors and warnings.

    The following example treats all warnings except the warning for
    unused imports as errors:

        $ pyang --Werror -W UNUSED_IMPORT

**-E** _errorcode_
:   Treat the warning _errorcode_ as an error.

    Use **-\-list-errors** to get a listing of all errors and warnings.

    The following example treats only the warning for unused import as an error:

        $ pyang --Werror -W UNUSED_IMPORT

**-\-ignore-error** _errorcode_
:   Ignore error _errorcode_.

    Use with care. Plugins that dont expect to be invoked if there are
    errors present may crash.

    Use **-\-list-errors** to get a listing of all errors and warnings.

    The following example ignores syntax errors in patterns:

        $ pyang --ignore-error PATTERN_ERROR

**-\-msg-template** _msg-template_
:   Print out error message in defined _msg-template_.

    Template used to display error messages. This is a python
    new-style format string used to format the message information
    with keys file, line, code, type, and msg.

    The following example create a msg template in defined pattern:

        $ pyang --msg-template={file} || {line} || {type} || {level}
            || {code} || {msg}

**-\-ignore-errors**
:   Ignore all errors. Use with care. Plugins that dont expect to be
    invoked if there are errors present may crash.

**-\-keep-comments**
:   This parameter has effect only if a plugin can handle comments.

**-\-canonical**
:   Validate the module(s) according to the canonical YANG order.

**-\-verify-revision-history**
:   Ensure that the revision history in the given module(s) is
    correct, by checking that it can find the old revisions of the
    module(s) in the YANG module search path.

**-\-strict**
:   Force strict YANG compliance. Currently this checks that the
    deref() function is not used in XPath expressions and leafrefs.

**-\-lint**
:   Validate the module(s) according to the generic YANG guideline as
    specified in **RFC 8407**. In addition, it checks that the
    module is in canonical order.

**-\-ietf**
:   Validate the module(s) like **-\-lint**, and in addition verifies
    that the namespace and module name follow the IETF conventions,
    and that the module has the correct license text and **RFC
    2119** / **RFC 8174** boilerplate text.

**-\-lax-quote-checks**
:   Lax checks of backslashes in double quoted strings in YANG version
    1 modules.  **RFC 6020** does not clearly define how to handle
    backslahes within double quoted strings, when the character after
    the backslash is not one of the characters listed in Section 6.1.3
    in **RFC 6020**.

    Earlier versions of pyang silently accepted such escape sequences,
    but the current version treats this as an error, just like it is
    defined in YANG 1.1 **RFC 7950**. Passing this flag to pyang
    makes pyang silently accept such escape sequences.

**-\-lax-xpath-checks**
:   Lax checks of XPath expressions. Specifically, do not generate an
    error if an XPath expression uses a variable or an unknown
    function.

**-L** **-\-hello**
:   Interpret the input file or standard input as a server &lt;hello&gt;
    message. In this case, no more than one _file_ parameter may be given.

**-\-implicit-hello-deviations**
:   Attempt to parse all deviations from a supplied &lt;hello&gt;
    message. Not all implementations provide deviations explicitly as
    modules. This flag enables more logic to attempt to derive all
    deviations from the message.

**-\-trim-yin**
:   In YIN input modules, remove leading and trailing whitespace from
    every line in the arguments of the following statements: contact,
    description, error-message, organization and reference. This way,
    the XML-indented argument texts look tidy after translating the
    module to the compact YANG syntax.

**-\-max-line-length** _maxlen_
:   Give a warning if any line is longer than _maxlen_. The value 0
    means no check (default).

**-\-max-identifier-length** _maxlen_
:   Give a error if any identifier is longer than_maxlen_.

**-t** **-\-transform** _transform_
:   Transform the module(s) after parsing them but before outputting
    them. Multiple transformations can be given, and will be performed
    in the order that they were specified. The supported
    transformations are listed in TRANSFORMATIONS below.

**-f** **-\-format** _format_
:   Convert the module(s) into _format_. Some translators require a
    single module, and some can translate multiple modules at one
    time. If no _outfile_ file is specified, the result is printed on
    stdout. The supported formats are listed in OUTPUT FORMATS below.

**-o** **-\-output** _outfile_
:   Write the output to the file _outfile_ instead of stdout.

**-F** **-\-features** _features_
:   _features_ is a string of the form
    _modulename_:[_feature_(,_feature_)*]

    This option is used to prune the data model by removing all nodes
    that are defined with a \"if-feature\" that is not listed as
    _feature_. This option affects all output formats.

    This option can be given multiple times, and may also be combined
    with **-\-hello**. The **-\-features** option overrides any
    supported features for a module that are taken from the hello
    file.

    If this option is not given, nothing is pruned, i.e., it works as
    if all features were explicitly listed.

    The **-\-exclude-features** option can be used for excluding a list
    of named features.  **-\-features** and **-\-exclude-features** cant
    both be specified for a given module.

    For example, to view the tree output for a module with all
    if-featured nodes removed, do:

        $ pyang -f tree --features mymod: mymod.yang

**-X** **-\-exclude-features** _features_
:   _features_ is a string of the form
    _modulename_:[_feature_(,_feature_)*]

    This option is used to prune the data model by removing all nodes
    that are defined with a \"if-feature\" that is listed as
    _feature_. This option affects all output formats.

    This option can be given multiple times. It cant be combined with
    **-\-hello**.

    The **-\-features** option can be used for including all features
    or a list of named features.  **-\-features** and
    **-\-exclude-features** cant both be specified for a given module.

    For example, to view the tree output for a module with if-featured
    nodes for the specified feature removed, do:

        $ pyang -f tree --exclude-features mymod:myfeat mymod.yang

**-\-max-status** _maxstatus_
:   _maxstatus_ is one of:_current_,_deprecated_, or _obsolete_.

    This option is used to prune the data model by removing all nodes
    that are defined with a \"status\" that is less than the given
    _maxstatus_. This option affects all output formats.

**-\-deviation-module** _file_
:   This option is used to apply the deviations defined in
    _file_. This option affects all output formats.

    This option can be given multiple times.

    For example, to view the tree output for a module with some
    deviations applied, do:

        $ pyang -f tree --deviation-module mymod-devs.yang mymod.yang

**-p** **-\-path** _path_
:   _path_ is a colon (:) separated list of directories to search for
    imported modules. This option may be given multiple times.

    By default, all directories (except \".\") found in the path are
    recursively scanned for modules. This behavior can be disabled by
    giving the option **-\-no-path-recurse**.

    The following directories are always added to the search path:

    1.  current directory
    2.  **$YANG\_MODPATH**
    3.  **$HOME**/yang/modules
    4.  **$YANG\_INSTALL**/yang/modules OR if **$YANG\_INSTALL** is unset
        &lt;the default installation directory&gt;/yang/modules
        (on Unix systems: /usr/share/yang/modules)

**-\-no-path-recurse**
:   If this parameter is given, directories in the search path are not
    recursively scanned for modules.

**-\-plugindir** _plugindir_
:   Load all YANG plugins found in the directory _plugindir_. This
    option may be given multiple times.

    List of directories to search for pyang plugins. The following
    directories are always added to the search path:

    1.  pyang/plugins from where pyang is installed
    2.  **$PYANG\_PLUGINPATH**

**-\-check-update-from** _oldfile_
:   Checks that a new revision of a module follows the update rules
    given in **RFC 6020** and **RFC 7950**. _oldfile_ is the old
    module and _file_ is the new version of the module.

    If the old module imports or includes any modules or submodules,
    it is important that the the old versions of these modules and
    submodules are found. By default, the directory where _oldfile_ is
    found is used as the only directory in the search path for old
    modules. Use the option

**-\-check-update-from-path**
:   to control this path.

**-P** **-\-check-update-from-path** _oldpath_
:   _oldpath_ is a colon (:) separated list of directories to search for
    imported modules. This option may be given multiple times.

**-D** **-\-check-update-from-deviation-module** _olddeviation_
:   _olddeviation_ is an old deviation module of the old module
    _oldfile_. This option may be given multiple times. For example,
    to check updates of a module with some deviations applied, do:

        $ pyang --check-update-from-deviation-module oldmod-devs.yang \
            --check-update-from oldmod.yang \
            --deviation-module newmod-devs.yang newmod.yang

_file..._
:   These are the names of the files containing the modules to be
    validated, or the module to be converted.

# TRANSFORMATIONS

Installed **pyang** transformations are (like output formats) plugins
and therefore may define their own options, or add new transformations
to the **-t** option. These options and transformations are listed in
**pyang -h**.

*edit*
:   Modify the supplied module(s) in various ways. This transform will
    usually be used with the *yang* output format.

# EDIT TRANSFORM

The *edit* transform modifies the supplied module(s) in various ways.
It can, for example, replace top-level *description* statements,
update *include* statements and manage *revision* statements.  Unless
otherwise noted below, it only modifies *existing* statements.

Each *edit* transform string (non-date) option value is either a plain
string (which is taken literally) or a *+*-separated list of
directives (whose expansions are concatenated with double-linebreak
separators, i.e., each directive results in one or more paragraphs).

Each directive is either of the form *@filename* (which is replaced
with the contents of the file; there is no search path; trailing
whitespace is discarded) or of the form *%keyword*. Any unrecognized
directives are treated as plain strings. The following *%*-directives
are currently supported:

- *%SUMMARY* : This expands to a \"summary\" of the original argument
  value. It's intended for use with top-level *description* statements
  that typically consist of a hand-crafted summary followed by
  copyrights, license and other boiler-plate text. The summary is the
  text up to but not including the first line that (ignoring leading
  and trailing whitespace) starts with the word *Copyright* followed
  by a space.

- *%SUBST/old/new* : This expands to the original argument value with
  all instances of *old* replaced with *new*.  There is no provision
  for replacing characters that contain forward slashes, and there is
  no terminating slash.

- *%DELETE* : This clears the output buffer and suppresses a check
   that would normally prevent overwriting an existing value (unless
   that value is the literal string **TBD**).

In the examples given below, it's assumed that there are *CONTACT*,
*CONTEXT*, *LICENSE*, *ORGANIZATION*, *REFERENCE* and *REVISION* files
in a top-level project directory (which in this case is the parent of
the directory in which **pyang** is being run). These examples
illustrate how the *edit* transform might be used with the *yang*
output format to prepare YANG files for publication.

Edit transform specific options:

**-\-edit-yang-version** *version*
:   Set the YANG version (i.e., the *yang-version* statement's
    argument) to *version*. This does nothing if the YANG module
    doesn't already have a *yang-version* statement.

    Example: **-\-edit-yang-version 1.1**.

**-\-edit-namespace** *namespace*
:   Set the YANG namespace (i.e., the *namespace* statement's
    argument) to *namespace*. This does nothing if the YANG module
    doesn't already have a *namespace* statement.

    Example: **-\-edit-namespace %SUBST/acme-pacific-org/apo**

**-\-edit-update-import-dates**
:   Update any *import* (or *include*) *revision-date* statements to
    match imported (or included) modules and submodules. If there
    isn't already a *revision-date* statement, it will be added.

**-\-edit-delete-import-dates**
:   Delete any *import* (or *include*) *revision-date* statements.

**-\-edit-organization** *organization*
:   Set the organization (i.e., the *organization* statement's
    argument) to *organization*. This does nothing if the YANG module
    doesn't already have an *organization* statement.

    Example: **-\-edit-organization @../ORGANIZATION**

**-\-edit-contact** *contact*
:   Set the contact info (i.e., the *contact* statement's argument) to
    *contact*. This does nothing if the YANG module doesn't already
    have a *contact* statement.

    Example: **-\-edit-contact @../CONTACT**

**-\-edit-description** *description*
:   Set the top-level description (i.e., the top-level *description*
    statement's argument) to *description*. This does nothing if the
    YANG module doesn't already have a *description* statement.

    Example: **-\-edit-description %SUMMARY+@../LICENSE+@../CONTEXT**

**-\-edit-delete-revisions-after** *prevdate*
:   Delete any *revision* statements after (i.e., that are more recent
    than) the supplied *yyyy-mm-dd* revision date. A typical use case
    is to supply the date of the previous release: any revisions since
    then will be internal (e.g., developers often feel that they should
    add revision statements for git commits) and are not wanted in the
    next released version.

    Example: **-\-edit-delete-revisions-after 2019-03-15**

**-\-edit-revision-date** *date*
:   Set the most recent revision date to the supplied *yyyy-mm-dd*
    revision date. This does nothing if the YANG module doesn't
    already have at least one *revision* statement. If necessary, a
    new *revision* statement will be inserted before any (remaining)
    existing revisions.

    Example: **-\-edit-revision-date 2020-03-15**

**-\-edit-revision-description** *description*
:   Set the most recent revision description to *description*.

    Example: **-\-edit-revision-description=%DELETE+@../REVISION**

**-\-edit-revision-reference** *reference*
:   Set the most recent revision reference to *reference*.

    Example: **-\-edit-revision-reference=%DELETE+@../REFERENCE**

# OUTPUT FORMATS

Installed **pyang** plugins may define their own options, or add new
formats to the **-f** option.  These options and formats are listed in
**pyang -h**.

*capability*
:   Capability URIs for each module of the data model.

*depend*
:   Makefile dependency rule for the module.

*dsdl*
:   Hybrid DSDL schema, see **RFC 6110**.

*identifiers*
:   All identifiers in the module.

*jsonxsl*
:   XSLT stylesheet for transforming XML instance documents to JSON.

*jstree*
:   HTML/JavaScript tree navigator.

*jtox*
:   Driver file for transforming JSON instance documents to XML.

*name*
:   Module name, and the name of the main module for a submodule.

*omni*
:   An applescript file that draws a diagram in **OmniGraffle**.

*sample-xml-skeleton*
:   Skeleton of a sample XML instance document.

*tree*
:   Tree structure of the module.

*flatten*
:   Print the schema nodes in CSV form.

*uml*
:   UML file that can be read by **plantuml** to generate UML diagrams.

*yang*
:   Normal YANG syntax.

*yin*
:   The XML syntax of YANG.

# LINT CHECKER

The *lint* option validates that the module follows the generic
conventions and rules given in **RFC 8407**.  In
addition, it checks that the module is in canonical order.

Options for the *lint* checker:

**-\-lint-namespace-prefix** *prefix*
:   Validate that the module's namespace is of the form:
    \"&lt;prefix&gt;&lt;modulename&gt;\".

**-\-lint-modulename-prefix** *prefix*
:   Validate that the module's name starts with *prefix*.

**-\-lint-ensure-hyphenated-names**
:   Validate that all identifiers use hyphenated style, i.e.,
    no uppercase letters or underscores.

# YANG SCHEMA ITEM IDENTIFIERS (SID)

YANG Schema Item iDentifiers (SID) are globally unique unsigned
integers used to identify YANG items. SIDs are used instead of names
to save space in constrained applications such as COREconf. This
plugin is used to automatically generate and updated .sid files used
to persist and distribute SID assignments.

Options for generating, updating and checking .sid files:

**-\-sid-generate-file**
:   This option is used to generate a new .sid file from a YANG module.

    Two arguments are required to generate a .sid file; the SID range
    assigned to the YANG module and its definition file. The SID range
    specified is a sub-range within a range obtained from a registrar
    or a sub-range within the experimental range (i.e., 60000 to
    99999). The SID range consists of the first SID of the range,
    followed by a colon, followed by the number of SID allocated to
    the YANG module. The filename consists of the module name,
    followed by an @ symbol, followed by the module revision, followed
    by the \".yang\" extension.

    This example shows how to generate the file *toaster@2009-11-20.sid*.

        $ pyang --sid-generate-file 20000:100 toaster@2009-11-20.yang

**-\-sid-update-file**
:   Each time new items are added to a YANG module by the introduction
    of a new revision of this module, its included sub-modules or
    imported modules, the associated .sid file need to be
    updated. This is done by using the **-\-sid-update-file** option.

    Two arguments are required to generate a .sid file for an updated
    YANG module; the previous .sid file generated for the YANG module
    and the definition file of the updated module. Both filenames
    follow the usual naming conversion consisting of the module name,
    followed by an @ symbol, followed by the module revision, followed
    by the extension.

    This example shows how to generate the file
    *toaster@2009-12-28.sid* based on the SIDs already present in
    *toaster@2009-11-20.sid*.

        $ pyang --sid-update-file toaster@2009-11-20.sid \
            toaster@2009-12-28.yang

**-\-sid-check-file**
:   The **-\-sid-check-file** option can be used at any time to verify
    if a .sid file need to be updated.

    Two arguments are required to verify a .sid file; the filename of
    the .sid file to be checked and the corresponding definition file.

     For example:

        $ pyang --sid-check-file toaster@2009-12-28.sid \
            toaster@2009-12-28.yang

**-\-sid-list**
:   The **-\-sid-list** option can be used before any of the previous
    options to obtains the list of SIDs assigned or validated. For
    example:

        $ pyang --sid-list --sid-generate-file 20000:100 \
            toaster@2009-11-20.yang

**-\-sid-extra-range**
:   If needed, an extra SID range can be assigned to an existing YANG module
    during its update with the **-\-sid-extra-range** option.

    For example, this command generates the file
    *toaster@2009-12-28.sid* using the initial range(s) present in
    *toaster@2009-11-20.sid* and the extra range specified in the
    command line.

        $ pyang --sid-update-file toaster@2009-11-20.sid \
            toaster@2009-12-28.yang --sid-extra-range 20100:100

*count*
:   The number of SID required when generating or updating a .sid file can
    be computed by specifying \"*count*\" as SID range.

    For example:

        $ pyang --sid-generate-file count \
            toaster@2009-11-20.yang

    or:

        $ pyang --sid-update-file toaster@2009-11-20.sid \
            toaster@2009-12-28.yang --sid-extra-range count

# CAPABILITY OUTPUT>

The *capability* output prints a capability URL for each module of the
input data model, taking into account features and deviations, as
described in section 5.6.4 of **RFC 6020**.

Options for the *capability* output format:

**-\-capability-entity**
:   Write ampersands in the output as XML entities (\"&amp;amp;\").

# DEPEND OUTPUT

The *depend* output generates a Makefile dependency rule for files
based on a YANG module.  This is useful if files are generated from
the module.  For example, suppose a .c file is generated from each
YANG module.  If the YANG module imports other modules, or includes
submodules, the .c file needs to be regenerated if any of the imported
or included modules change.  Such a dependency rule can be generated
like this:

    $ pyang -f depend --depend-target mymod.c \
        --depend-extension .yang mymod.yang
    mymod.c : ietf-yang-types.yang my-types.yang

Options for the *depend* output format:

**-\-depend-target**
:   Makefile rule target.  Default is the module name.

**-\-depend-extension**
:   YANG module file name extension.  Default is no extension.

**-\-depend-no-submodules**
:    Do not generate dependencies for included submodules.

**-\-depend-from-submodules**
:    Generate dependencies taken from all included submodules.

**-\-depend-recurse**
:    Recurse into imported modules and generate dependencies
     for their imported modules etc.

**-\-depend-include-path**
:    Include file path in the prerequisites.  Note that if no
     **-\-depend-extension** has been given, the prerequisite is the
     filename as found, i.e., ending in \".yang\" or \".yin\".

**-\-depend-ignore-module**
:    Name of YANG module or submodule to ignore in the prerequisites.
     This option can be given multiple times.

# DSDL Output

The *dsdl* output takes a data model consisting of one or more YANG
modules and generates a hybrid DSDL schema as described in **RFC
6110**. The hybrid schema is primarily intended as an interim product
used by **yang2dsdl**(1).

The *dsdl* plugin also supports
metadata annotations, if they are defined and used as described in
**RFC 7952**.

Options for the *dsdl* output format:

**-\-dsdl-no-documentation**
:    Do not print Dublin Core metadata terms

**-\-dsdl-record-defs**
:   Record translations of all top-level typedefs and groupings in the
    output schema, even if they are not used. This is useful for
    translating library modules.

# JSONXSL OUTPUT

The *jsonxsl* output generates an XSLT 1.0 stylesheet that can be used
for transforming an XML instance document into JSON text as specified
in **RFC 7951**. The XML document must be a valid instance of the data
model which is specified as one or more input YANG modules on the
command line (or via a &lt;hello&gt; message, see the **-\-hello**
option).

The *jsonxsl* plugin also converts metadata annotations, if they are
defined and used as described in **RFC 7952**.

The data tree(s) must be wrapped at least in either &lt;nc:data&gt; or
&lt;nc:config&gt; element, where \"nc\" is the namespace prefix for the
standard NETCONF URI \"urn:ietf:params:xml:ns:netconf:base:1.0\", or the
XML instance document has to be a complete NETCONF RPC request/reply
or notification. Translation of RPCs and notifications defined by the
data model is also supported.

The generated stylesheet accepts the following parameters that modify
its behaviour:

- *compact*: setting this parameter to 1 results in a compact
   representation of the JSON text, i.e., without any whitespace. The
   default is 0 which means that the JSON output is pretty-printed.

- *ind-step*: indentation step, i.e., the number of spaces to use for
  each level. The default value is 2 spaces. Note that this setting is
  only useful for pretty-printed output (compact=0).

The stylesheet also includes the file *jsonxsl-templates.xsl* which is
a part of **pyang** distribution.

# JSTREE OUTPUT

The *jstree* output grenerates an HTML/JavaScript page that presents a
tree-navigator to the given YANG module(s).

jstree output specific option:

**-\-jstree-no-path**
:   Do not include paths in the output.  This option makes the page
    less wide.

# JTOX OUTPUT

The *jtox* output generates a driver file which can be used as one of
the inputs to **json2xml** for transforming a JSON document to XML as
specified in **RFC 7951**.

The *jtox* output itself is a JSON document containing a concise
representation of the data model which is specified as one or more
input YANG modules on the command line (or via a &lt;hello&gt;
message, see the **-\-hello** option).

See **json2xml** manual page for more information.

# OMNI OUTPUT

The plugin generates an applescript file that draws a diagram in
OmniGraffle.  Requires OmniGraffle 6.  Usage:

     $ pyang -f omni foo.yang -o foo.scpt
     $ osascript foo.scpt

omni output specific option:

**-\-omni-path** *path*
:    Subtree to print.  The *path* is a slash (\"/\") separated path to
     a subtree to print.  For example \"/nacm/groups\".

# NAME OUTPUT

The *name* output prints the name of each module in the input data
model. For submodules, it also shows the name of the main module to
which the submodule belongs.

name output specific option:

**-\-name-print-revision**
:   Print the name and revision in name@revision format.

# SAMPLE-XML-SKELETON OUTPUT

The *sample-xml-skeleton* output generates an XML instance document
with sample elements for all nodes in the data model, according to the
following rules:

- An element is present for every leaf, container or anyxml.

- At least one element is present for every leaf-list or
  list. The number of entries in the sample is min(1,

- For a choice node, sample element(s) are present for
  each case.

- Leaf, leaf-list and anyxml elements are empty (but see
  the **-\-sample-xml-skeleton-defaults** option
  below).

Note that the output document will most likely be invalid and needs
manual editing.

Options specific to the *sample-xml-skeleton* output format:

**-\-sample-xml-skeleton-annotations**
:   Add XML comments to the sample documents with hints about expected
    contents, for example types of leaf nodes, permitted number of
    list entries etc.

**-\-sample-xml-skeleton-defaults**
:   Add leaf elements with defined defaults to the output with their
    default value. Without this option, the default elements are
    omitted.

**-\-sample-xml-skeleton-doctype=**_type_
:   Type of the sample XML document. Supported values for *type* are
    **data** (default) and **config**. This option determines the document
    element of the output XML document (&lt;data&gt; or &lt;config&gt;
    in the NETCONF namespace) and also affects the contents: for
    **config**, only data nodes representing configuration are included.

**-\-sample-xml-skeleton-path=**_path_
:   Subtree of the sample XML document to generate, including all
    ancestor elements.  The *path* is a slash (\"/\") separated list of
    data node names that specifies the path to a subtree to print. For
    example \"/nacm/rule-list/rule/rpc-name\".

# TREE OUTPUT

The *tree* output prints the resulting schema tree from one or more
modules.  Use **pyang -\-tree-help** to print a description on the
symbols used by this format.

Tree output specific options:

**-\-tree-help**
:   Print help on symbols used in the tree output and exit.

**-\-tree-depth** *depth*
:   Levels of the tree to print.

**-\-tree-path** *path*
:   Subtree to print.  The *path* is a slash (\"/\") separated path to a
    subtree to print.  For example \"/nacm/groups\".  All ancestors and
    the selected subtree are printed.

**-\-tree-print-groupings**
:   Print the top-level groupings defined in the module.

**-\-tree-print-structures**
:   Print the ietf-yang-structure-ext:structure structures defined in
    the module.

**-\-tree-print-yang-data**
:    Print the ietf-restconf:yang-data structures defined in the
     module.

**-\-tree-line-length** *maxlen*
:    Try to break lines so they are no longer than *maxlen*.  This is
     a best effort algorithm.

**-\-tree-module-name-prefix** *maxlen*
:    Use the module name (instead of the prefix) to prefix
     parameters and types.

# FLATTEN OUTPUT

The *flatten* output flattens provided
YANG module and outputs the schema nodes and some of their
properties in CSV format.

Flatten output specific options:

**-\-flatten-no-header**
:   Do not emit the CSV header.

**-\-flatten-keyword**
:   Output the keyword.
    This will resolve as container, leaf, etc.

**-\-flatten-type**
:   Output the top-level type.
    This will resolve to a module-prefixed type.

**-\-flatten-primitive-type**
:   Output the primitive type.
    This resolves to a YANG type such as uint64.

**-\-flatten-flag**
:   Output flag property.
    Derives a flag - for instance rw/ro for config, or x for RPC.

**-\-flatten-description**
:   Output the description.

**-\-flatten-keys**
:   Output whether the XPath is identified as a key.
    *key* or null will be output per XPath.

**-\-flatten-keys-in-xpath**
:   Output the XPath with keys in path.

**-\-flatten-prefix-in-xpath**
:   Output the XPath with prefixes instead of modules.

**-\-flatten-qualified-in-xpath**
:    Output the qualified XPath i.e., /module1:root/module1:node/module2:node/...

**-\-flatten-qualified-module-and-prefix-path**
:   Output an XPath with both module and prefix i.e., /module1:prefix1:root/...
    This is NOT a colloquial syntax of XPath. Emitted separately.

**-\-flatten-deviated**
:   Flatten all data keywords instead of only data definition keywords.

**-\-flatten-filter-keyword** *keyword*
:   Filter output to only desired keywords.  Keywords specified are
    what will be displayed in output.  Can be specified more than
    once.

**-\-flatten-filter-primitive** *primitive_type*
:   Filter output to only desired primitive types.  Primitives
    specified are what will be displayed in output.  Can be specified
    more than once.

**-\-flatten-filter-flag** *choice*
:   Filter output to flag.

    - *rw* for configuration data.

    - *ro* for non-configuration data, output parameters to rpcs and
            actions, and notification parameters.

    - *w* for input parameters to rpcs and actions.

    - *u* for uses of a grouping.

    - *x* for rpcs and actions.

    - *n* for notifications.

**-\-flatten-csv-dialect** *dialect*
:   CSV dialect for output.
    *dialect* is one of **excel**, **excel-tab**, or **unix**.

**-\-flatten-ignore-no-primitive**
:   Ignore error if primitive is missing.

**-\-flatten-status**
:   Output the status statement value.

**-\-flatten-resolve-leafref**
:   Output the XPath of the leafref target.

# UML OUTPUT

The *uml* output prints an output that can be used as input-file to
**plantuml** (http://plantuml.sourceforge.net) in order to
generate a UML diagram.  Note that it requires **graphviz**
(http://www.graphviz.org/).

For large diagrams you may need to increase the Java heap-size
by the -XmxSIZEm option, to java.  For example: **java
      -Xmx1024m -jar plantuml.jar ....**

Options for the *UML* output format:

**-\-uml-classes-only**
:   Generate UML with classes only, no attributes

**-\-uml-split-pages=**_layout_
:   Generate UML output split into pages, NxN, example 2x2.
    One .png file per page will be rendered.

**-\-uml-output-directory=**_directory_
:   Put the generated .png files(s) in the specified output directory.
    Default is \"img/\"

**-\-uml-title=**_title_
:   Set the title of the generated UML diagram, (default is
    YANG module name).

**-\-uml-header=**_header_
:   Set the header of the generated UML diagram.

**-\-uml-footer=**_footer_
:   Set the footer of the generated UML diagram.

**-\-uml-long-identifers**
:   Use complete YANG schema identifiers for UML class names.

**-\-uml-no=**_arglist_
:   Render the diagram with groupings inlined.

**-\-uml-inline-augments**
:   Render the diagram with augments inlined.

**-\-uml-max-enums=*number***
:    Maximum of enum items rendered.

**-\-uml-filter-file=*file***
:   NOT IMPLEMENTED: Only paths in the filter file will be included in
    the diagram. A default filter file is generated by option
    -\-filter.

# YANG OUTPUT

Options for the *yang* output format:

**-\-yang-canonical**
:   Generate all statements in the canonical order.

**-\-yang-remove-unused-imports**
:   Remove unused import statements from the output.

**-\-yang-remove-comments**
:   Remove all comments from the output.

**-\-yang-line-length** *len*
:   Try to format each line with a maximum line length of *len*.  Does
    not reformat long lines within strings.

# YIN OUTPUT

Options for the *yin* output format:

**-\-yin-canonical**
:   Generate all statements in the canonical order.

**-\-yin-pretty-strings**
:   Pretty print strings, i.e., print with extra whitespace in the
    string.  This is not strictly correct, since the whitespace is
    significant within the strings in XML, but the output is more
    readable.

# YANG XPATH EXTENSIONS

This section describes XPath functions that can be used in
\"must\", \"when\", or \"path\" expressions in YANG modules, in
addition to the core XPath 1.0 functions.

**pyang** can be instructed to reject the usage
of these functions with the parameter
**-\-strict**.

**Function:** *node-set* **deref**(*node-set*)
:   The **deref** function follows the reference
    defined by the first node in document order in the argument
    node-set, and returns the nodes it refers to.

    If the first argument node is an **instance-identifier**,
    the function returns a node-set that contains the single node that
    the instance identifier refers to, if it exists.  If no such node
    exists, an empty node-set is returned.

    If the first argument node is a **leafref**, the function
    returns a node-set that contains the nodes that the leafref refers
    to.

    If the first argument node is of any other type, an empty node-set
    is returned.

    The following example shows how a leafref can be written with
    and without the **deref** function:

        /* without deref */

        leaf my-ip {
          type leafref {
            path "/server/ip";
          }
        }
        leaf my-port {
          type leafref {
            path "/server[ip = current()/../my-ip]/port";
          }
        }

        /* with deref */

        leaf my-ip {
          type leafref {
            path "/server/ip";
          }
        }
        leaf my-port {
          type leafref {
            path "deref(../my-ip)/../port";
          }
        }

# EXAMPLES

The following example validates the standard YANG modules with
derived types:

    $ pyang ietf-yang-types.yang ietf-inet-types.yang

The following example converts the ietf-yang-types module into YIN:

    $ pyang -f yin -o ietf-yang-types.yin ietf-yang-types.yang

The following example converts the ietf-netconf-monitoring module into
a UML diagram:

    $ pyang -f uml ietf-netconf-monitoring.yang > \
        ietf-netconf-monitoring.uml
    $ java -jar plantuml.jar ietf-netconf-monitoring.uml
    $ open img/ietf-netconf-monitoring.png

# ENVIRONMENT VARIABLES

**pyang** searches for referred modules in the colon (:) separated
path defined by the environment variable **\$YANG_MODPATH** and in the
directory **\$YANG_INSTALL**/yang/modules.

**pyang** searches for plugins in the colon (:) separated path
defined by the environment variable
**\$PYANG_PLUGINDIR**.

# BUGS

The XPath arguments for the *must* and *when* statements are checked
only for basic syntax errors.

# AUTHORS

See the file CONTRIBUTORS at https://github.com/mbj4668/pyang.
