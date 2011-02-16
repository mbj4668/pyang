Use this to generate a UML package structure of several YANG files
ls *.yang | xargs -n1 pyang -f depend > packages.txt
uml-pkg --title=TITLE --inputfile=packages.txt > packages.uml
java -jar plantuml.jar packages.uml
open img/packages.png
