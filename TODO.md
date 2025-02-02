# TODO

* add validation of instance-identifier defaults

* move all plugin API functions to plugin.py

* give a warning if the default case does not have any default leafs

## Optimizations

* lazy read imported modules.  do not validate the module on import,
  but do it when something is used.  even better would be to lazy
  validate.  hmm, maybe separate the side-effect free validation
  functions from the functions that have side-effect (like expand).
