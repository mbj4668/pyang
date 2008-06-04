debug = False

def dbg(str):
    if debug:
        print "** %s" % str

def set_debug(v):
    global debug
    debug = v
