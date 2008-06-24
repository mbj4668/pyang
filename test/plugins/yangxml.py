# This pyang plugin generates a random XML instance document adhering
# to a YANG module.

from pyang import plugin
from pyang import types
import sys
from random import randint, random

def pyang_plugin_init():
    plugin.register_plugin(YANGXMLPlugin())

class YANGXMLPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        fmts['xml'] = self
    def emit(self, ctx, module, writef):
        emit_xml(module, writef)
    
def emit_xml(module, fd):
    # pick one top-level child
    if len(module.i_expanded_children) == 0:
        return
    c = pick(module.i_expanded_children)
    attrs = ' xmlns="%s"' % module.namespace.arg
    cn = c.__class__.__name__
    if cn == 'Choice':
        print >> sys.stderr, "Cannot handle choice on top-level"
        sys.exit(1)
    emit_stmt(c, fd, '', attrs, 1)

def emit_stmt(stmt, fd, ind, attrs='', n=None):
    if n == None and stmt.keyword in ['list', 'leaf-list']:
        lb = 0
        if stmt.min_elements != None:
            lb = int(stmt.min_elements.arg)
        ub = 3 # 3 is many
        if stmt.max_elements != None and stmt.max_elements.arg != 'unbounded':
            ub = int(stmt.max_elements.arg)
            if ub > 3:
                ub = 3
        if lb > ub:
            ub = lb
        n = randint(lb,ub)
    if stmt.keyword == 'container':
        emit_container(stmt, fd, ind, attrs)
    elif stmt.keyword == 'leaf':
        emit_leaf(stmt, fd, ind, attrs)
    elif stmt.keyword == 'leaf-list':
        emit_leaf_list(stmt, n, fd, ind, attrs)
    elif stmt.keyword == 'list':
        emit_list(stmt, n, fd, ind, attrs)
    elif stmt.keyword == 'choice':
        # pick one case
        c = pick(stmt.i_expanded_children)
        emit_stmt(c, fd, ind)
    elif stmt.keyword == 'case':
        for c in stmt.i_expanded_children:
            emit_stmt(c, fd, ind)
    elif stmt.keyword == 'anyxml':
        emit_anyxml(stmt, fd, ind)
        
def emit_leaf(stmt, fd, ind, attrs):
    do_print = True
    if ((stmt.mandatory != None) and (stmt.mandatory.arg == 'false') or
        (stmt.default != None) or (stmt.type.has_type('empty') != None)):
        if random() < 0.3:
            do_print = False
    if do_print == True:
        fd.write(ind + '<%s%s>' % (stmt.name, attrs))
        emit_type_val(stmt.type, fd)
        fd.write('</%s>\n' % stmt.name)

def emit_container(stmt, fd, ind, attrs):
    do_print = True
    if stmt.presence != None:
        if random() < 0.3:
            do_print = False
    if do_print == True:
        fd.write(ind + '<%s%s>\n' % (stmt.name, attrs))
        for c in stmt.i_expanded_children:
            emit_stmt(c, fd, ind + '  ')
        fd.write(ind + '</%s>\n' % stmt.name)

def emit_leaf_list(stmt, n, fd, ind, attrs):
    while (n > 0):
        fd.write(ind + '<%s%s>' % (stmt.name, attrs))
        emit_type_val(stmt.type, fd)
        fd.write('</%s>\n' % stmt.name)
        n = n - 1

def emit_list(stmt, n, fd, ind, attrs):
    while (n > 0):
        fd.write(ind + '<%s%s>\n' % (stmt.name, attrs))
        cs = stmt.i_expanded_children
        for k in stmt.i_key:
            fd.write(ind + '  <%s>' % k.name)
            emit_type_val(k.type, fd)
            fd.write('</%s>\n' % k.name)
        for c in stmt.i_expanded_children:
            if c not in stmt.i_key:
                emit_stmt(c, fd, ind + '  ')
        fd.write(ind + '</%s>\n' % stmt.name)
        n = n - 1

def emit_anyxml(stmt, fd, ind):
    fd.write(ind + '<%s><bar xmlns="">42</bar></%s>\n' % (stmt.name, stmt.name))
        
def emit_type_val(t, fd):
    if t.i_is_derived == False and t.i_typedef != None:
        return emit_type_val(t.i_typedef.type, fd)
    inttype = t.has_type(['int8','int16','int32','int64',
                          'uint8','uint16','uint32','uint64'])
    if t.enum != []:
        enum = pick(t.enum)
        fd.write(enum.name)
    elif t.has_type('empty') != None:
        pass
    elif t.range != None:
        (lo,hi) = pick(t.range.i_ranges)
        ts = types.yang_type_specs[inttype]
        if lo == 'min':
            lo = ts.min
        if hi == 'max':
            hi = ts.max
        if hi == None:
            hi = lo
        val = randint(lo,hi)
        fd.write(str(val))
    elif t.has_type('boolean') != None:
        val = pick(['true','false'])
        fd.write(val)
    elif inttype != None:
        ts = types.yang_type_specs[inttype]
        val = randint(ts.min, ts.max)
        fd.write(str(val))
    elif t.has_type('ipv4-address') != None:
        fd.write('10.0.0.1')
    else:
        if t.length != None:
            # pick a length
            (lo,hi) = pick(t.length.i_lengths)
            if hi == None:
                hi = lo
            lentgh = randint(lo,hi)
        if t.pattern != None:
            # oh boy
            pass
        fd.write('__foo__')

def pick(xs):
    r = randint(0,len(xs)-1)
    return xs[r]
