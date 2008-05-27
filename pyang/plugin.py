class PyangPlugin(object):
    """abstract base class for pyang plugins

    A pyang plugin is a module found in the plugins directory of the
    pyang installation, or in the dynamic pluginpath.

    Such a module must export a function 'pyang_plugin_init()', which
    may call pyang.main.register_plugin() with an instance of a class
    derived from this class as argument.
    """
    def add_output_format(self, fmts):
        """override this method to add an output format.  fmts is a dict
        which maps the format name string to a plugin instance.
        """
        return
    def add_opts(self, optparser):
        """override this method to add command line options.  Add the
        plugin related options as an option group.
        """
        return
    def setup_ctx(self, ctx):
        """override this method to modify the Context before any
        files are read"""
        return
    def emit(self, ctx, module, writef):
        """override this method to perform the output conversion.
        writef is a function that takes one string to print as argument.
        """
        return
    

    
