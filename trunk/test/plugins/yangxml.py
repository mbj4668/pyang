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
    emit_obj(c, fd, '', attrs, 1)

def emit_obj(obj, fd, ind, attrs='', n=None):
    cn = obj.__class__.__name__
    if n == None and cn in ['List', 'LeafList']:
        lb = 0
        if obj.min_elements != None:
            lb = int(obj.min_elements.arg)
        ub = 3 # 3 is many
        if obj.max_elements != None and obj.max_elements.arg != 'unbounded':
            ub = int(obj.max_elements.arg)
            if ub > 3:
                ub = 3
        if lb > ub:
            ub = lb
        n = randint(lb,ub)
    if cn == 'Container':
        emit_container(obj, fd, ind, attrs)
    elif cn == 'Leaf':
        emit_leaf(obj, fd, ind, attrs)
    elif cn == 'LeafList':
        emit_leaf_list(obj, n, fd, ind, attrs)
    elif cn == 'List':
        emit_list(obj, n, fd, ind, attrs)
    elif cn == 'Choice':
        # pick one case
        c = pick(obj.i_expanded_children)
        emit_obj(c, fd, ind)
    elif cn == 'Case':
        for c in obj.i_expanded_children:
            emit_obj(c, fd, ind)
        
def emit_leaf(obj, fd, ind, attrs):
    do_print = True
    if ((obj.mandatory != None) and (obj.mandatory.arg == 'false') or
        (obj.default != None) or (obj.type.has_type('empty') != None)):
        if random() < 0.3:
            do_print = False
    if do_print == True:
        fd.write(ind + '<%s%s>' % (obj.name, attrs))
        emit_type_val(obj.type, fd)
        fd.write('</%s>\n' % obj.name)

def emit_container(obj, fd, ind, attrs):
    do_print = True
    if obj.presence != None:
        if random() < 0.3:
            do_print = False
    if do_print == True:
        fd.write(ind + '<%s%s>\n' % (obj.name, attrs))
        for c in obj.i_expanded_children:
            emit_obj(c, fd, ind + '  ')
        fd.write(ind + '</%s>\n' % obj.name)

def emit_leaf_list(obj, n, fd, ind, attrs):
    while (n > 0):
        fd.write(ind + '<%s%s>' % (obj.name, attrs))
        emit_type_val(obj.type, fd)
        fd.write('</%s>\n' % obj.name)
        n = n - 1

def emit_list(obj, n, fd, ind, attrs):
    while (n > 0):
        fd.write(ind + '<%s%s>\n' % (obj.name, attrs))
        cs = obj.i_expanded_children
        for k in obj.i_key:
            fd.write(ind + '  <%s>' % k.name)
            emit_type_val(k.type, fd)
            fd.write('</%s>\n' % k.name)
        for c in obj.i_expanded_children:
            if c not in obj.i_key:
                emit_obj(c, fd, ind + '  ')
        fd.write(ind + '</%s>\n' % obj.name)
        n = n - 1
        
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
