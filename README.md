## News ##
**2014-11-18 - Version 1.5 released**

  * A new plugin 'check-update' has been added. It can be used to check if a new revision of a module follows the update rules from RFC 6020.

  * A new plugin 'omni' has been added.  It generates an OmniGraffle script file from a model.

  * ... and various other enhancements and bug fixes.

**2013-11-11 - Version 1.4.1 released**
  * Exactly as 1.4, but fixed to that it works with Python 3.

**2013-10-24 - Version 1.4 released**
  * lots of bugfixes

**2013-01-31 - Version 1.3 released**
  * New plugins: hypertree, jstree, jsonxsl, jtox
  * lots of bugfixes

**2011-07-27 - Version 1.2 released**

**2011-02-16 - Version 1.1 released**

  * A new UML plugin has been added. It is used to generate UML diagrams for visualization of YANG data models.  See [UMLOutput](UMLOutput.md) for an example.
  * The DSDL plugin is updated to [RFC 6110](http://www.rfc-editor.org/rfc/rfc6110.txt)
  * ... and various bug fixes.


---


## Overview ##

YANG ([RFC 6020](http://www.rfc-editor.org/rfc/rfc6020.txt)) is a data modeling language for NETCONF ([RFC 4741](http://www.rfc-editor.org/rfc/rfc4741.txt)), developed by the IETF [NETMOD](http://www.ietf.org/html.charters/netmod-charter.html) WG.

pyang is a YANG validator, transformator and code generator, written in python. It can be used to validate YANG modules for correctness, to transform YANG modules into other formats, and to generate code from the modules.

### Compatibility ###

pyang is compatible with the following IETF RFCs:

  * [RFC 6020](http://www.rfc-editor.org/rfc/rfc6020.txt)
  * [RFC 6087](http://www.rfc-editor.org/rfc/rfc6087.txt)
  * [RFC 6110](http://www.rfc-editor.org/rfc/rfc6110.txt)
  * [RFC 6643](http://www.rfc-editor.org/rfc/rfc6110.txt)

## Features ##

  * Validate YANG modules.
  * Convert YANG modules to YIN, and YIN to YANG.
  * Translates YANG data models to DSDL schemas, which can be used to and validate instance documents (NETCONF PDUs and data store content). See [DSDL Mapping Tutorial](http://www.yang-central.org/twiki/bin/view/Main/DSDLMappingTutorial) for an example.
  * Translates YANG data models to XSD.
  * Generate UML diagrams from YANG models. See [UMLOutput](UMLOutput.md) for an example.
  * Generate compact tree representation of YANG models for quick visualization. See [TreeOutput](TreeOutput.md) for an example.
  * Plugin framework for simple development of other outputs, such as code generation.


---


## Documentation ##

See [Documentation](Documentation.md).