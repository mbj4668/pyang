* 2.4.0 - 2020-11-09

```
         #690 - stop uses expanding if import circular dependency exists
         #685 - report errors in sample-xml-skeleton
         #683 - fix sample-xml-skeleton unknown namespace crash
         #681 - newline fix in tree plugin
         #678 - deviate replace regression
         #673 - fix unreasonable the case node status
         #669 - type validator crashes on valid range restriction
         #665 - output status value in flatten plugin
         #661 - sort output for flatten plugin
         #660 - add module:prefix:node output for flatten plugin
         #657 - fix crash for concat function which has more than 3 params in xpath
```

* 2.3.2 - 2020-07-06

```
         #646 - config false deviation fix
         #587 - revert fix for #587; use xml schema regexp engine again
```

* 2.3.1 - 2020-06-29

```
         Update Version Number
```

* 2.3.0 - 2020-06-28

```
         add structure support (RFC8791)

         pr:639 - output all missing hello modules then exit
                  thanks to Remington Campbell
         pr:632 - add option --flatten-qualified-in-xpath --flatten-prefix-in-xpath to flatten plugin
                  thanks to @Huanghao1975
         pr:623 - add option to output keys in flatten plugin
                  thanks to Remington Campbell
         pr:585 - validation improvements
                  thanks to @mirolos
         pr:579 - add documentation of the 'edit' transform
                  thanks to William Lupton

         #638 - fix jstree crash with choice node and adjust action node style to the same with rpc
         #628 - fix unexpected keyword used within the augment statement
                thanks to Jie Zhang
         #626 - fix the incorrent counts of '..' in path
         #621 - correct check_update for implicit default check
                thanks to Paul Merlo
         #620 - the single and double quotes are inconsistent due to the spaces
         #615 - deviate add should be able to add default statement to leaf-list node
         #606 - fix 'current' node wrongly referenced to a 'deprecated' definition
         #603 - fix action statements wrongly defined within an action/rpc/notification node
         #602 - fix mandatory nodes directly under the default case
         #601 - fix wrongly reject substring function with 2arguments
         #599 - fix crash when input defined in anydata node
         #597 - fix the target node of augment statment being action node
         #596 - fix default value in leaf-list node marked with an if-feature statement
         #594 - validate the value of position in 'bit' statements
         #592 - check illegal range and length restrictions correctly
         #587 - fix regular expression '\w' cannot recognize underline('_')
         #564 - validate the value of min-elements and max-elements
         #583 - the default value in leaf node should not be marked with an if-feature statements
         #581 - move code out of package init
                thanks to @ptlm
         #219 - deviation replace/add config should check the target node's config
                thanks to Fred Gan
```

* 2.2.1 - 2020-03-06

```
         pr:576 - added all transforms to the release (specifically 'edit')
                  thanks to William Lupton

```

* 2.2 - 2020-03-05

```
         pr:557 - added new options for customizing error messages
                  thanks to @gribok
         pr:556 - extended parsing of deviation in hello
                  thanks to Remington Campbell
         pr:549 - align the --bbf option with the options that BBF uses
                  thanks to William Lupton
         pr:437 - added "edit" transform
                  thanks to William Lupton

         #572 - check that action/notification don't have keyless ancestor
                thanks to Fred Gan
         #564 - check that min-elements isn't larger than max-elements
                thanks to Fred Gan
         #563 - avoid crash i tree plugin when an augment path is invalid
         #552 - correct prefix validation in default values
         #547 - keep end-of-line comments in -f yang
                thanks to Fred Gan
         #543 - properly handle tab characters as 8 spaces
                thanks to Fred Gan
         #542 - handle spaces in PATH
                thanks to Rui Pires
         #538 - handle position values greater than 4294967295
                thanks to Fred Gan
         #537 - feature searched for in wrong module
         #536 - better handling of prefixes in xpath strings
         #501 - jtox plugin fails on yang 1.1 unprefixed paths in a leafref
                thanks to Fred Gan
         #475 - honor ABNF grammar for deviate delete substatements
                thanks to Fred Gan

         code cleanup
           thanks to Miroslav Los

```

* 2.1.1 - 2020-01-03

```
         #532 - warn if config true xpath refers to config false node
         #522 - find prefixes in xpath expressions in groupings
         #518 - broken xpath check
         #514 - re-added sample-xml-skeleton plugin (accidentally removed)
         #495 - "when" xpath context node was not correctly set in "uses"
```

* 2.1 - 2019-10-20

```
         added a plugin to generate SID files (see draft-ietf-core-sid)
           thanks to @lemikev
         fixed canonical stmt order in 'identity'
         handle anydata in jsonxsl plugin

         #511 - mk_path_list() now handles "input" and "output" correctly
                thanks to Joe Gladston
         #509 - allow refine of default to leaf-list in 1.1
         #505 - --yang-canonical duplicates require-instance
```

* 2.0.2 - 2019-08-21

```
         pr:497 - fixed crash when parsing an xpath union with three or
                  more terms
                  thanks to Stuart Bayley

         #503 - fixed crash in add_prefix() function
         #496 - fixed bug in xpath parser when a function had more
                than one argument.  this bug lead to false warnings
                that imported modules were not used, when they in fact
                were used in xpath expressions.
```

* 2.0.1 - 2019-06-11

```
         pr:492 - ensure the ietf-netconf namespace isn't added multiple times
                  in json2xml
         #493 - fixed crash with --keep-comments where comments were present
                between a statement keyword and the argument
         #491 - fixed incorrect prototype for XPath "concat" function
```

*   2.0 - 2019-05-29

```
         pyang now has a proper XPath 1.0 parser, which means that it will
           detect more XPath errors, and produce warnings for XPath expressions
           that for example refer to unknown nodes
         for python coders: non backwards compatible change in the
           pyang.xpath module.  the function xpath.tokens() has been
           replaced by pyang.xpath_lexer.scan(), but it also return
           tokens in a new format
         for python coders: non backwards compatible change in
           statements.add_xpath_function().  this function now takes
           three parameters, instead of just one
         pyang -f yang now keeps comments by default.  use
           the parameter --yang-remove-comments to remove them
         updated the IETF plugin to check RFC 8407 guidelines
         updated the IETF plugin to check for the license text and
           RFC 2119/8174 boilerplate text

         pr:489 - avoid sample-xml-skeleton crash for submodules
                  thanks to William Lupton
         pr:484 - fixes #483, #487, check_update can now be used
                  to check compatibility on multiple modules with one time
                  model context initialization; fixed error message for
                  added presence containers
                  thanks to Yan Gorelik
         pr:471 - fixes #468, #469, check_update now handles submodule better,
                  and checks ranges
                  thanks to Paul Merlo
         pr:464 - added __str__() and __repr__() methods to Statement
                  thanks to William Lupton
         pr:463 - more memory usage reductions
                  thanks to Glenn Matthews
         pr:461 - fixes #458, unique stmt inside global grouping causes
                  dsdl parsing error
                  thanks to Norbert Varkonyi
         pr:377 - added statement utility functions, e.g. more options to
                  mk_path_str() to construct paths with various formats
                  thanks to Remington Campbell

         #490 - handle refinement of if-feature
         #486 - validate xpath syntax in groupings
         #485 - ensure all identifiers in error messages are within quotes
         #482 - groupings are now printed correctly in -f tree, when
                --tree-no-expand-uses is used.
         #481 - nodes that are not implemented due to false "if-feature"
                statements are now properly pruned.
         #465 - plugin.pre_validate_ctx is now called at correct time
                for python coders: previously modules were validated as
                they were added to the context; now there are validated
                when ctx.validate() is called.
         #306 - support plugins available as .pyc files
         #183 - canonical checks lead to false 'circular definition' error
```

* 1.7.8 - 2019-01-21

```
         for python coders: reverted method signature change for
         Repository.get_module_from_handle().  it now has the same
         signature as in 1.7.5.

         fixed bug in check_update when there were more than one
         augment for the same target node.
```

* 1.7.7 - 2019-01-17

```
         fixed a bug in -f yang formatting
```

* 1.7.6 - 2019-01-17

```
         fixed grammar; do not allow "must" in "choice"
         added --yang-line-length to try to format lines with max length
         various fixes to -f yang for consistency in the output
         -f yang now keeps concatenated strings from the input and use them
           in the output (properly indented)

         pr:403 - fix json config validation error message
                  thanks to Ganesh Nalawade
         pr:417 - added --check-update-from-deviation-module
                  thanks to Jonathan Yang
         pr:420 - emit module name for augmented nodes in tree format
                  thanks to Mark Farrell
         pr:424 - update check-update-from option according to RFC 7950
                  thanks to Miroslav Kovac
         pr:434 - unique statement now checked for nodes inside choice in dsdl
                  thanks to Norbert Varkonyi
         pr:435 - added new "transform" generic plugin type and -t option
                  thanks to William Lupton
         pr:439 - print files read with --verbose
                  thanks to William Lupton
         pr:444 - do not treat flymake temp files as plugins
                  thanks to Martin Volf
         pr:454 - fix pyang.bat for windows
                  thanks to Jozef Janitor

         #397 - fix crash in sample-xml-skeleton format
         #418 - properly handle identityref defaults in sample-xml-skeleton
         #450 - allow choice of containers in rc:yang-data
```

* 1.7.5 - 2018-04-25

```
         the tree output is now aligned with RFC 8340
         remove trailing whitespace from double quoted strings
         -f yang formatting fixes
         added proper validation of revision date
         handle comments properly when --yang-canonical is given
         leaf-list with sample-xml-skeleton would crash

         pr:351 - mk_path_str now handles prefixes in choice/case
                  thanks to Glenn Matthews
         pr:354 - store original pattern string in typespec
                  thanks to immibis
         pr:382 - reduce memory usage
                  thanks to Glenn Matthews
         pr:385 - close open files
                  thanks to Robin Jarry
         pr:386 - document --name-print-revision
                  thanks to Joe Clark

         #369 - fix install dependency to lxml
         #374 - don't warn for identifers starting with [xX][mM][lL] in 1.1
         #375 - --keep-comments now handle long block comments
         #379 - detect incorrect identities in the default statement
         #380 - --lint-ensure-hyphenated-name bug fix
         #383 - correctly identify chocie and anyxml as mandatory nodes
                thanks to Glenn Matthews
```

* 1.7.4 - 2018-02-23

```
         the tree output is now aligned with
           draft-ietf-netmod-yang-tree-diagrams-05
         added --tree-no-expand-uses to not expang groupings in uses
         added --max-status to prune old definitions
         added yang2dsdl -x to try to translate 1.1 modules
         added yang2dsdl -c to use current definitions only
         added target get-data-reply to yang2dsdl
         check that a current/deprecated node does not reference a node
           with "lesser" status.
         added 'identifiers' plugin
         the yang output plugin no longer quotes enums, unless required
           b/c the argument contains a character that needs quotes

         pr:319 - added --name-print-revision option,
                  thanks to Joe Clarke
         pr:321 - added --lint-ensure-hyphenated-names option,
                  thanks to Reshad Rahman
         pr:331 - avoid misinterpreting malformed filenames,
                  thanks to Glenn Matthews

         #309 - legal if-feature expressions gave error in python3
         #324 - better handling of min/max
         #329 - hexadecimal and octal formats now accepted as default value
                for integer types
         #358 - translator dsdl bug with groupings fixed
         #360 - bug when xsltproc failing with "undefined namespace prefix"
                for identityref when prefix defined in tag of text fixed
```

* 1.7.3 - 2017-06-27

```
         #318 - handle multiple rc:yang-data statements.
                this bug caused validation of ietf-restconf, or any
                module that imported ietf-restconf, to fail.
```

* 1.7.2 - 2017-06-14

```
         added support for external plugins, using setuptools entry_points
         added a warning for unsafe escape sequences in double quoted
           strings.
         added --lax-quote-checks to turn of the warning for unsafe
           escape sequences.
         added restconf plugin
         added --tree-print-yang-data
         print anydata/anyxml better in tree diagrams
         grammar fix; "must" not allowed in "case"

         pr:248 replace newlines in typestrings with spaces in UML,
                thanks to William Lupton
         pr:281 added --jstree-path, thanks to Ralph Schmieder
         pr:289 added plugins for bbf, ieee, and mef, thanks to
                Mahesh Jethanandani
         pr:312 ignore actions when generating sample XML, thanks to
                William Lupton
         pr:313 corrected --tree-help output, thanks to lifeunleaded

         #278 - handle unprefixed leafref paths in jsonxsl.py
         #284 - removed broken error message for 'when' on key leafs
         #285 - handle illegal integer strings
         #297 - corrected translation of empty container with extension
                statement in DSDL
         #300 - handle unknown extensions in deviation
         #301 - fix bug w/ refine of leafref leaf
         #310 - when using the windows command prompt, "pyang" was not
                found, thanks to Mallikarjunarao Kosuri
```

* 1.7.1 - 2016-11-02

```
         added support for RFC 7952, metadata annotations
         added --tree-max-length option

         #126 - correctly validate implicitly added YIN files
         #218 - do not copy if-feature to augment children
         #225 - improve default implicit YANG_MODPATH discovery
         #232 - bit default fix
         #259 - handle multiple bases in identityref
         #261 - detect mandatory and default after refine
         #262 - fixed chorthand case expansion
         #263 - don't validate nodes that are not-supported
         #265 - an identity is not derived from itself
         #267 - generate error if config property is added in deviation
         #271 - do not warn about submodule revision mismatch
         #272 - incorrect handling of unprefixed paths in leafrefs in
                groupings
         #276 - detect enumeration/bits/identityref w/o enum/bit/base
         #277 - handle shorthand choice correctly
```

* 1.7 - 2016-06-16

```
         added support for YANG 1.1
         added command line flag --ignore-error, thanks to Nick Weeds
         added option --tree-print-groupings to the 'tree' plugin
         removed the 'hypertree' and 'xmi' plugins

         #180,#191,#221 - YIN and YANG modules now support utf-8 encoded
           characters
         #190 - the options --lint and --ietf now checks for mandatory
           top-level nodes
         #200 - unique statements w/o prefixes now work in yang2dsdl
         #201 - the options --lint and --ietf now verifies that a
           module's revision is newer or the same as the most recent
           submodule's revision
         #206 - detect bad augment from submodule
         #208 - yang2dsdl now correctly handle must statements in nested
           groupings
         #234 - handling of XPath operator bug fix
```

* 1.6 - 2015-10-06

```
         removed the deprecated, incomplete and erroneous XSD plugin - use
           the DSDL plugin instead.
         added new plugin: 'lint' to check if a module follow
           the generic guidelines defined in RFC 6087.  the 'ietf' plugin
           still exists, but is rewritten to use the new 'lint' plugin.
         added new plugin: 'name' to print a module's name, thanks to
           Giles Heron.
         by default, pyang now scans the YANG module path recursively,
           i.e., it searches for YANG modules also in subdirectories to the
           directories in the load path.  this behavior can be disabled with
           --no-path-recurse.
         the directory 'modules' now has two subdirectories 'iana' and
           'ietf', where all current IANA and IETF modules are located.
         a bash completions file has been added etc/bash_completion.d

         #76 - some grammar tests for various deviate statements
         #114 - deviation module in capability plugin
         #115 - deviation of shorthand case
         #121 - added --depend-recurse
         #122 - handle CRLF in max-line-len checks; also do not count
                single LF
         #123 - check that modules are encoded in utf-8
         #130 - validate position value
         #133 - python 3 syntax fix
         #141 - remove call to cmp()
         #156 - i_config unset in some shorthand cases
         #158 - handle defaults in binary
         #160 - pprint fails when printing a statement without an argument
                thanks to Nick Weeds.
         #164 - updated comment in plugin.py to reflect reality

         fix bug with adding a unique statement via a deviation, thanks
           to Denys Knertser.

         do not reorder data definition statements in --yang-canonical

         names in nested choices are now checked for uniqueness

         remove warning about multiple top-level nodes in lint plugin.
           thanks to Pravin Gohite.

         implement try/except block for plugin directory listing,
           thanks to Ebben Aries
```

* 1.5 - 2014-11-18

```
         added new plugin: 'capability' to print the capability string for
           a module
         added new plugin: 'check-update' which can be used to compare
           two revisions of a module and check if the update rules defined
           in RFC 6020 are followed
         added new plugin: 'omni' to generate OmniGraffle output
         added new plugin: 'sample-xml-skeleton' to generate a sample xml
           instance skeleton document adhering to a YANG model
         added command line flag --features to prune the data model
           by removing unsupported features
         added command line flag --deviation-module to modify the data model
           by applying devaitions from a separate module
         added command line flag --verbose (-V)
         added command line flag --ignore-errors
         added command line flag --keep-comments (can be used by plugins)
         added doc/tutorial
         added support for YANG meta data as defined in
           draft-lhotka-netmod-yang-metadata
         jstree: added command line flag --jstree-no-path
         tree: when --depth is used, indicate pruned subtrees with '...'
         tree: print leafref targets
         yang: print comments if --keep-comments are given

         #97 - check for circular leafref paths
         #99 - missing version attribute in 'xmi' output
         #100 - check for prefixes in qname literals in XPath expressions
         #101 - enum fixes in 'uml' output
         #103 - type empty now handled in 'dsdl' output
```

* 1.4.1 - 2013-11-11

```
         #96 - 1.4 doesn't work with Pyhton 3
```

* 1.4 - 2013-10-24

```
         added option --lax-xpath-checks
         deprecated the xsd output plugin
         tree: now prints augmented nodes
         tree: now prints rpcs nad notifications defined in submodules
         tree: new syntax for presence containers
         tree: mark lists with '*'
         allow 'must' under 'anyxml'
         fixed unique check for keys
         reject leaf-list of type empty

         #83 - reject identifiers that start with "[xX][mM][lL]"
         #89 - dsdl: handle % in strings
         #90 - do not crash on null key statements
         #92 - dsdl: handle conditional uses
         #93 - dsdl: fixed problem  with anyxml
         #94 - dsdl: mandatory choice inside a grouping
```

* 1.3 - 2013-01-31

```
         added new plugins: hypertree and jstree
         added new plugins: jsonxsl and jtox
         added command line flags -W and -E to treat warnings as errors
         xsd: added command line flag --xsd-global-complex-types
         tree: added command line flasgs  --tree-depth and
               --tree-path to prune the printed tree

         #58 - detect when a leaf restricts a type so that the type's
               default value becomes illegal
         #59 - given an error if a list's unique statement references
               leafs which have different config flags
         #60 - xpath tokenizer bug fix
         #62 - dsdl: handle empty default values
         #63 - dsdl: handle empty containers and lists.
         #66 - dsdl: interleave module grammars
         #68 - dsdl: schematron rule for instance identifier.
         #73 - dsdl: fixed bug when a submodule used an extension from
               an imported  module
         #74 - dsdl: correctly handle empty choice and case nodes
         #79 - dsdl: now treats identity derivation as irreflexive and
               transitive
         allow choice in case
         fixed bug when checking the canonical order for length and pattern
            (any orded was accepted)
         dsdl: proper handling of instance-identifiers
         pyang now works with python 3, as well as old 2.x
         yang output plugin quote fix for strings ending in newline
         smiv2: allow smiv2:oid under identity
         smiv2: fixes in oid regexp
         smiv2: RFC 6643 compatible
         ... and numerous other minor fixes
```

* 1.2 - 2011-07-27

```
        added edit-config target to yang2dsls

        if a submodule A includes submodule B, which includes
          submodule C, definitions in C are visible in A, even if A does
          not include C.  this bug has been fixed.

        make sure additional must statements in refine are added; not
          replacing existing ones.
        fixed bug when checking for '..' in relative leafrefs
        variuos augment bug fixes in yang2dsdl
        some xsd output fixes
        removed the --xsd-no-include option.  the xsd ouput never generates
          inlcude anymore
```

* 1.1 - 2011-02-16

```
        DSDL output compatible with RFC 6110

        added uml output format

        inherit the config property correctly with augment
        added check to verify that a leafref type had a path substatement
        removed bashisms from yang2dsdl script
        fixed setup.py script
        fixed optional marker bug in tree output
        generate an error if a submodule's name is not the same
          correct (typically this means that it is not the same as
          the filename)
        made yang2dsdl POSIX.2 compatible
        reorganized command-line parameters in yand2dsdl
        fixed bug wit input modules not on module path
        added examples for DSDL Mapping Tutorial
```

* 1.0 - 2010-10-07

```
        compatible with RFC 6020

        added yang2dsdl(1) program
        added tree output format
        added depend output format

        too many bugfixes to list them all
```

* 0.9.3 - 2008-12-07

```
        compatible with draft-ietf-netmod-yang-02
        rewrote validation code.  got rid of all the specialized classes
        handle circular defintions
        removed command-line option --level.  print warnings and errors
          instead
        added command-line option -Werror to treat warning as errors
        added command-line option -Wnone to suppress warning
        handle auto-assignment of enum values and bit positions
        allow plugins to register grammar for extensions
        added a plugin for the 'yang-smi' SMIv2 module
        rewrote yin_parser - now handles extensions properly
        added bin/yang2html which can be used to syntax coloring of yang
          modules
        new algorithm for finding standard YANG modules (see pyang(1))
```

* 0.9.2 - 2008-10-13

```
        handle prefixed references to local groupings
        make use of path argument given to pyang
        handle multiple patterns
        allow refinements in any order
        fixed bug where a grouping defined in a submodule was not
          detected (if the submodule was included more than once)
        fixed length and range validation bug across mutiple YANG modules.
        allow 'must' and 'config' in 'choice'
        allow 'must' in 'case'
        added some initial text describing code layout to README

        XSD: report some XSD error conditions that used to cause XSD
          translation to silently fail to stderr
        XSD: added --xsd-break-pattern command line option
          (thanks to Juergen Schoenwaelder)
        XSD: added --xsd-no-lecture command line option
        XSD: fixed XSD output bug in some rare cases involving typedef chains

        DSDL: corrected handling of multiple length alternatives
        DSDL: added TODO
        DSDL: added support for multiple patterns in string restrictions
        DSDL: added xmlns declaration for the data model NS
        DSDL: $this in must-stmt is now replaced with current()
          rather than '.'
        DSDL: local top-level named patterns now don't start with '__'
        DSDL: added XSLT stylesheet that separates DSRL

        known issue: augmenting the input parameters of an rpc that is
          declared without any input parameters does not work
        known issue: an error is not reported if the same node is added
          twice via an augment
        known issue: chained derivation of types doesn't work properly
          in the DSDL translator
```

* 0.9.1 - 2008-07-08

```
        rewrote yang parser
        added yin parser
        added dsdl output
        added yang output
        more internal restructuring
```

* 0.9.0b - 2008-05-19

```
        first release of restructured code
```

* 02.2 - 2008-02-21

```
        fixed some xsd output bugs
        fixed bug in refinmenet, where a valid refinmened would
          generate a duplicate node definition error
        fixed range/length check bug
        verify that a list in a grouping which is used from config
          has keys
        internal preparation for major restructure of the code
```

* 02.1 - 2008-02-06

```
        draft-bjorklund-netconf-yang-02 compliant.
```
   
* 01.3 - 2008-02-01

```
        draft-bjorklund-netconf-yang-01 compliant.
```

* 00.2 - 2008-01-15

```
        fixed grouping translation in XSD output
        generate YIN appinfo by default in XSD output
        added validation of identifiers
        handle min/max in length and range expressions
        handle must in leaf refinement
        handle yin-element in extensions
        handle bits types in XSD generation
        xs:key generation fix in XSD output by John Dickinson
```

* 00.1 - 2007-11-14

```
        Initial version, draft-bjorklund-netconf-yang-00 compliant.
```
