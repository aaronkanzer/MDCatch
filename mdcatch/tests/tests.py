# **************************************************************************
# *
# * Authors:     Grigory Sharov (gsharov@mrc-lmb.cam.ac.uk) [1]
# *
# * [1] MRC Laboratory of Molecular Biology, MRC-LMB
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'gsharov@mrc-lmb.cam.ac.uk'
# *
# **************************************************************************

import os
from glob import glob
import tempfile
import unittest

from ..config import *
from ..utils.misc import getUsername
from ..parser import Parser
from ..utils.feixml import parseXml


class TestParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cwd = os.path.dirname(__file__) + "/testdata"

    def test_run(self):
        fns = glob(os.path.join(self.cwd, "*"))
        fns = [os.path.abspath(x) for x in fns]

        model = Parser()
        # Test EPU cases
        for fn in fns:
            if fn.endswith("mdoc"):
                continue
            else:
                model.software = "EPU"
            self._runParser(model, self.cwd, os.path.abspath(fn))

        # Test SerialEM cases
        for fn in fns:
            if fn.endswith("xml"):
                continue
            else:
                model.software = "SerialEM"
            self._runParser(model, self.cwd, os.path.abspath(fn))

    def _runParser(self, model, mdPath, mdFn):
        """ Run the parser and return model acqDict. """
        model.pipeline = DEF_PIPELINE
        model.mdPath = mdPath
        model.fn = mdFn

        model.user = getUsername()
        model.acqDict['User'] = model.user

        print("\n\nInput params: ", sorted(model.__dict__.items()))
        print("\nFiles found: %s\n" % mdFn)

        model.parseMetadata(mdFn)

        model.calcDose()
        model.guessDataDir(testmode=True)
        model.acqDict['PtclSize'] = DEF_PARTICLE_SIZE
        model.calcBox()

        print("\nFinal parameters:\n")
        for k, v in sorted(model.acqDict.items()):
            print(k, v)


EPU_XML_PHASE_PLATE = """<MicroscopeImage xmlns="http://schemas.datacontract.org/2004/07/Fei.SharedObjects" xmlns:i="http://www.w3.org/2001/XMLSchema-instance"><CustomData xmlns:a="http://schemas.microsoft.com/2003/10/Serialization/Arrays"><a:KeyValueOfstringanyType><a:Key>PhasePlateUsed</a:Key><a:Value i:type="b:boolean" xmlns:b="http://www.w3.org/2001/XMLSchema">true</a:Value></a:KeyValueOfstringanyType><a:KeyValueOfstringanyType><a:Key>PhasePlateApertureName</a:Key><a:Value i:type="b:string" xmlns:b="http://www.w3.org/2001/XMLSchema">Ph P4</a:Value></a:KeyValueOfstringanyType><a:KeyValueOfstringanyType><a:Key>PhasePlatePosition</a:Key><a:Value i:type="b:int" xmlns:b="http://www.w3.org/2001/XMLSchema">3</a:Value></a:KeyValueOfstringanyType></CustomData></MicroscopeImage>"""


class TestFeiXml(unittest.TestCase):
    def test_phase_plate_without_objective_aperture(self):
        """ Older EPU versions write the phase plate keys but no Aperture[OBJ].Name. """
        with tempfile.TemporaryDirectory() as tmpdir:
            fn = os.path.join(tmpdir, "FoilHole_1_Data_2_3_20200101_000000.xml")
            with open(fn, "w") as f:
                f.write(EPU_XML_PHASE_PLATE)
            acqDict = parseXml(fn)

        self.assertEqual(acqDict['PhasePlateUsed'], 'true')
        self.assertEqual(acqDict['PhasePlateNumber'], 'P4')
        self.assertEqual(acqDict['PhasePlatePosition'], '3')
