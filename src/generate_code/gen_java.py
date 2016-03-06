# generate java

import os
from parsing.keywords import javakeywords
from gen_base import ReportGenerator, CmdLineGenerator

class PySourceAsJava(ReportGenerator):
    def __init__(self, outdir=None):
        ReportGenerator.__init__(self)
        self.outdir = outdir
        self.fp = None

    def _DumpClassFooter(self):
        self.result +=  "}\n"

        if self.fp:
            self.fp.write(self.result)
            self.fp.close()
            self.fp = None
            self.result = ''

    def _DumpModuleMethods(self):
        self.result += '/*\n'
        ReportGenerator._DumpModuleMethods(self)
        self.result += '*/\n'

    def _OpenNextFile(self):
        filepath = os.path.join(self.outdir, self.aclass) + '.java'
        self.fp = open(filepath, 'w')


    def _NiceNameToPreventCompilerErrors(self, attrname):
        """
        Prevent compiler errors on the java side by checking and modifying attribute name
        """
        # only emit the rhs of a multi part name e.g. undo.UndoItem will appear only as UndoItem
        if attrname.find('.') <> -1:
            attrname = attrname.split('.')[-1] # take the last
        # Prevent compiler errors on the java side by avoiding the generating of java keywords as attribute names
        if attrname in javakeywords:
            attrname = '_' + attrname
        return attrname

    def _DumpAttribute(self, attrobj):
        compositescreated = self._GetCompositeCreatedClassesFor(attrobj.attrname)
        if compositescreated:
            compositecreated = compositescreated[0]
        else:
            compositecreated = None

        # Extra processing on the attribute name, to avoid java compiler errors
        attrname = self._NiceNameToPreventCompilerErrors(attrobj.attrname)

        if compositecreated and self.embedcompositeswithattributelist:
            self.result +=  "    public %s %s %s = new %s();\n" % (self.staticmessage, compositecreated, attrname, compositecreated)
        else:
            #self.result +=  "    public %s void %s;\n" % (self.staticmessage, attrobj.attrname)
            #self.result +=  "    public %s int %s;\n" % (self.staticmessage, attrname)
            self.result +=  "    public %s variant %s;\n" % (self.staticmessage, attrname)

        """
        import java.util.Vector;

        private java.util.Vector lnkClass4;

        private Vector lnkClass4;
        """

    def _DumpCompositeExtraFooter(self):
        pass

    def _DumpClassNameAndGeneralisations(self):
        if self.verbose:
            print '  Generating Java class', self.aclass
        self._OpenNextFile()

        self.result += "// Generated by PyNSource http://www.andypatterns.com/index.php/products/pynsource/ \n\n"

        self.result +=  'public class %s ' % self.aclass
        if self.classentry.classesinheritsfrom:
            self.result +=  'extends %s ' % self._NiceNameToPreventCompilerErrors(self.classentry.classesinheritsfrom[0])
        self.result +=  '{\n'

    def _DumpMethods(self):
        for adef in self.classentry.defs:
            self.result +=  "    public void %s() {\n    }\n" % adef

    def _Line(self):
        pass


class CmdLinePythonToJava(CmdLineGenerator):

    def _GenerateAuxilliaryClasses(self):
        classestocreate = ('variant', 'unittest', 'list', 'object', 'dict')  # should add more classes and add them to a jar file to avoid namespace pollution.
        for aclass in classestocreate:
            fp = open(os.path.join(self.outpath, aclass+'.java'), 'w')
            fp.write(self.GenerateSourceFileForAuxClass(aclass))
            fp.close()

    def GenerateSourceFileForAuxClass(self, aclass):
       return '\npublic class %s {\n}\n'%aclass

    def _CreateParser(self):
        self.p = PySourceAsJava(self.outpath)

