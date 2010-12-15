# ls *.yang | xargs -n1 pyang -f depend > packages.txt
# python pkg.py packages.txt > packages.uml
# java -jar plantuml.jar packages.uml
# open img/packages.png

import sys

useslist = []
def main(*args):
	try:
		infile = open(sys.argv[1], 'r+')
	except IOError:
		print 'cannot open', sys.argv[1]
	except IndexError:
		print 'supply input file'
	else:
		filename = sys.argv[1]
		if filename.rfind('.') > 0:
			filename = filename[0:filename.rfind('.')]
		sys.stdout.write('@startuml img/%s.png \n' %filename)
		lines = infile.readlines()
		for line in lines:
		    # sys.stderr.write('checking line %s' %line)
		    pkg = line.split(":")
		    sys.stdout.write('package \"%s\" as %s \n' %(pkg[0], plantuml(pkg[0])))
		    sys.stdout.write('end package\n')
		    imports = pkg[1].split(" ")
		    for i in imports:
			if (i != "") and (i != "\n"):
			    useslist.append(plantuml(pkg[0]) + ' --+ ' +  plantuml(i.replace("\n", "")) + ".yang"   + '\n' )
		for u in useslist:
		    sys.stdout.write('%s \n' %u)
		sys.stdout.write('@enduml \n')


def plantuml(s):
        s = s.replace('-', '_')
        s = s.replace('/', '_')
        s = s.replace(':', '_')
        return s

 
if __name__ == '__main__':
    sys.exit(main(*sys.argv))
