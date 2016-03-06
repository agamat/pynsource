# generate delphi

import os
from parsing.keywords import delphikeywords
from gen_base import ReportGenerator, CmdLineGenerator
from common.messages import DELPHI_UNIT_FILE_TEMPLATE

def unique(s):
    """ Return a list of the elements in list s in arbitrary order, but without duplicates """
    n = len(s)
    if n == 0:
         return []
    u = {}
    try:
         for x in s:
            u[x] = 1
    except TypeError:
         del u   # move onto the next record
    else:
          return u.keys()

    raise "uniqueness algorithm failed .. type more of it in please - see http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560"

class PySourceAsDelphi(ReportGenerator):
    def __init__(self, outdir=None):
        ReportGenerator.__init__(self)
        self.outdir = outdir
        self.fp = None

    def _DumpClassFooter(self):
        self.result +=  "\n\n"

        self.result +=  "implementation\n\n"

        self.DumpImplementationMethods()

        self.result +=  "\nend.\n\n"

        if self.fp:
            self.fp.write(self.result)
            self.fp.close()
            self.fp = None
            self.result = ''

    def _DumpModuleMethods(self):
        self.result += '(*\n'
        ReportGenerator._DumpModuleMethods(self)
        self.result += '*)\n\n'

    def _OpenNextFile(self):
        filepath = os.path.join(self.outdir, self.aclass) + '.pas'
        self.fp = open(filepath, 'w')


    def _NiceNameToPreventCompilerErrors(self, attrname):
        """
        Prevent compiler errors on the java side by checking and modifying attribute name
        """
        # only emit the rhs of a multi part name e.g. undo.UndoItem will appear only as UndoItem
        if attrname.find('.') <> -1:
            attrname = attrname.split('.')[-1] # take the last

        # Prevent compiler errors on the Delphi side by avoiding the generating of delphi keywords as attribute names
        if attrname.lower() in delphikeywords:   # delphi is case insensitive, so convert everything to lowercase for comparisons
            attrname = '_' + attrname

        return attrname

    def _DumpAttribute(self, attrobj):
        """
        Figure out what type the attribute is only in those cases where
        we are later going to assign to these variables using .Create() in the constructor.
        The rest we make Variants.
        """
        compositescreated = self._GetCompositeCreatedClassesFor(attrobj.attrname)
        if compositescreated:
            compositecreated = compositescreated[0]
        else:
            compositecreated = None

        # Extra processing on the attribute name, to avoid delphi compiler errors
        attrname = self._NiceNameToPreventCompilerErrors(attrobj.attrname)

        self.result +=  "    "
        if self.staticmessage:
            self.result +=  "class var"

        if compositecreated:
            vartype = compositecreated
        else:
            vartype = 'Variant'
        self.result +=  "%s : %s;\n"%(attrname, vartype)

        """ generate more complex stuff in the implementation section..."""
        #if compositecreated and self.embedcompositeswithattributelist:
        #    self.result +=  "    public %s %s %s = new %s();\n" % (self.staticmessage, compositecreated, attrname, compositecreated)
        #else:
        #    self.result +=  "%s : Variant;\n"%attrname

    def _DumpCompositeExtraFooter(self):
        pass

    def _DumpClassNameAndGeneralisations(self):
        if self.verbose:
            print '  Generating Delphi class', self.aclass
        self._OpenNextFile()

        self.result += "// Generated by PyNSource http://www.andypatterns.com/index.php/products/pynsource/ \n\n"

        self.result += "unit unit_%s;\n\n" % self.aclass
        self.result += "interface\n\n"

        uses = unique(self.GetUses())
        if uses:
            self.result += "uses\n    "
            self.result += ", ".join(uses)
            self.result += ";\n\n"

        self.result +=  'type\n\n'
        self.result +=  '%s = class' % self.aclass
        if self.classentry.classesinheritsfrom:
            self.result +=  '(%s)' % self._NiceNameToPreventCompilerErrors(self.classentry.classesinheritsfrom[0])
        self.result +=  '\n'
        self.result +=  'public\n'

    def _DumpMethods(self):
        if self.classentry.attrs:   # if there were any atributes...
            self.result +=  "\n"  # a little bit of a separator between attributes and methods.

        for adef in self.classentry.defs:
            if adef == '__init__':
                self.result +=  "    constructor Create;\n"
            else:
                #self.result +=  "    function %s(): void; virtual;\n" % adef
                self.result +=  "    procedure %s(); virtual;\n" % adef

        self.result +=  "end;\n"   # end of class

    def DumpImplementationMethods(self):
        for adef in self.classentry.defs:
            if adef == '__init__':
                self.result +=  "constructor %s.Create;\n" % self.aclass  # replace __init__ with the word 'Create'
            else:
                #self.result +=  "function %s.%s(): void;\n" % (self.aclass, adef)
                self.result +=  "procedure %s.%s();\n" % (self.aclass, adef)
            self.result +=  "begin\n"
            if adef == '__init__':
                self.CreateCompositeAttributeClassCreationAndAssignmentInImplementation()
            self.result +=  "end;\n\n"

    def CreateCompositeAttributeClassCreationAndAssignmentInImplementation(self):
        # Only do those attributes that are composite and need to create an instance of something
        for attrobj in self.classentry.attrs:
            compositescreated = self._GetCompositeCreatedClassesFor(attrobj.attrname)
            if compositescreated and self.embedcompositeswithattributelist: # latter variable always seems to be true! Never reset!?
                compositecreated = compositescreated[0]
                self.result +=  "    %s := %s.Create();\n" % (attrobj.attrname, compositecreated)

    def GetUses(self):
        result = []
        for attrobj in self.classentry.attrs:
            compositescreated = self._GetCompositeCreatedClassesFor(attrobj.attrname)
            if compositescreated and self.embedcompositeswithattributelist: # latter variable always seems to be true! Never reset!?
                compositecreated = compositescreated[0]
                result.append(compositecreated)

        # Also use any inherited class modules.
        if self.classentry.classesinheritsfrom:
            result.append(self._NiceNameToPreventCompilerErrors(self.classentry.classesinheritsfrom[0]))

        return [ 'unit_'+u for u in result ]

    def _Line(self):
        pass

class CmdLinePythonToDelphi(CmdLineGenerator):

    def _GenerateAuxilliaryClasses(self):
        # Delphi version omits the class 'object' and 'variant' since these already are pre-defined in Delphi.
        classestocreate = ('unittest', 'list', 'dict')  # should add more classes
        for aclass in classestocreate:
            fp = open(os.path.join(self.outpath, 'unit_'+aclass+'.pas'), 'w')
            fp.write(self.GenerateSourceFileForAuxClass(aclass))
            fp.close()

    def GenerateSourceFileForAuxClass(self, aclass):
       return DELPHI_UNIT_FILE_TEMPLATE%(aclass, aclass)

    def _CreateParser(self):
        self.p = PySourceAsDelphi(self.outpath)



"""
  // Example Delphi source file:

  unit test000123;

  interface

  uses
    SysUtils, Windows, Messages, Classes, Graphics, Controls,
    Forms, Dialogs;

  type
    TDefault1 = class (TObject)
    private
      field0012: Variant;
    public
      class var field0123434: Variant;
      procedure Member1;
      class procedure Member2;
    end;


  procedure Register;

  implementation

  procedure Register;
  begin
  end;

  {
  ********************************** TDefault1 ***********************************
  }
  procedure TDefault1.Member1;
  begin
  end;

  class procedure TDefault1.Member2;
  begin
  end;


  end.

"""
