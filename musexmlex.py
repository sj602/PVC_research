#!/usr/bin/env python

###############################################################################
# Information about the program
###############################################################################
__author__ = "Anthony D. Ricke"
__date__ = "22 Jul 2009"
__version__ = "0.1.0"
__credits__ = "Guido van Rossum, for the Python language"
__copyright__ = "Copyright (C) 2009  GE Healthcare"


###############################################################################
# Imports
# Modules needed by the script.
###############################################################################
import sys  # For system information
import optparse
import string
import xml.parsers.expat
import base64
import struct
import array
import os

# Globals
# The following are the element tags for the XML document
# WAVEFORM_ELEM = "Waveform"
# WAVETYPE_ELEM = "WaveformType"
# RHYTHM_TAG = "Rhythm"
# LEAD_DATA_ELEM = "LeadData"
# LEAD_ID_ELEM = "LeadID"
# WAVEFORM_DATA_ELEM = "WaveFormData"
# SAMPLE_BASE_ELEM = "SampleBase"
# LEAD_ADU_ELEM = "LeadAmplitudeUnitsPerBit"
# LEAD_UNIT_ELEM = "LeadAmplitudeUnits"

INDEPENDENT_LEADS = ("I", "II", "V1", "V2", "V3", "V4", "V5", "V6")

###############################################################################
# Classes
###############################################################################
class XmlElementParser:
    """Abstract base class for a XML Parsing State. It contains methods for
    restoring the previous state and for tracking the character data between
    tags."""

    def __init__(self, old_State=None):
        self.__old_State = old_State
        self.__data_Text = ""

    def restoreState(self, context):
        """This method restores the previous state in the XML parser."""
        if self.__old_State:
            context.setState(self.__old_State)

    def clearData(self):
        """This method clears the character data that was collected during parsing"""
        self.__data_Text = ""

    def getData(self):
        """This method returns the character data that was collected during
        parsing and it strips any leading or trailing whitespace"""
        return string.strip(self.__data_Text)

    def start_element(self, name, attrs, context):
        print("""abstract method, called at the start of an XML element""")
        sys.exit(0)

    def end_element(self, name, context):
        print("""abstract method, called at the end of an XML element""")
        sys.exit(0)

    def char_data(self, data, context):
        """This method accumulates any character data"""
        self.__data_Text = self.__data_Text + data


class IdleParser(XmlElementParser):
    """State for handling the Idle condition"""

    def __init__(self):
        XmlElementParser.__init__(self)

    def start_element(self, name, attrs, context):
        if name == WaveformElementParser.Tag:
            context.setState(WaveformElementParser(self))

    def end_element(self, name, context):
        self.clearData()


class WaveformElementParser(XmlElementParser):
    """State for handling the Waveform element"""

    Tag = "Waveform"

    def __init__(self, old_State):
        XmlElementParser.__init__(self, old_State)

    def start_element(self, name, attrs, context):
        self.clearData()
        if name == WaveformTypeElementParser.Tag:
            context.setState(WaveformTypeElementParser(self))
        elif name == LeadDataElementParser.Tag:
            context.setState(LeadDataElementParser(self))
        elif name == SampleBaseElementParser.Tag:
            context.setState(SampleBaseElementParser(self))

    def end_element(self, name, context):
        if name == self.Tag:
            self.restoreState(context)


class SampleBaseElementParser(XmlElementParser):
    """State for handling the SampleBase element"""

    Tag = "SampleBase"

    def __init__(self, old_State):
        XmlElementParser.__init__(self, old_State)

    def start_element(self, name, attrs, context):
        self.clearData()

    def end_element(self, name, context):
        if name == self.Tag:
            self.restoreState(context)
            if context.found_Rhythm:
                context.setSampleBase(self.getData())
                print("Sampling rate for rhythm is %s sps..." % (context.sample_Rate))


class LeadUnitsPerBitElementParser(XmlElementParser):
    """State for handling the LeadAmplitudeUnitsPerBit element"""

    Tag = "LeadAmplitudeUnitsPerBit"

    def __init__(self, old_State):
        XmlElementParser.__init__(self, old_State)

    def start_element(self, name, attrs, context):
        self.clearData()

    def end_element(self, name, context):
        if name == self.Tag:
            self.restoreState(context)
            context.setAdu(float(string.strip(self.getData())))


class LeadUnitsElementParser(XmlElementParser):
    """State for handling the LeadAmplitudeUnits element"""

    Tag = "LeadAmplitudeUnits"

    def __init__(self, old_State):
        XmlElementParser.__init__(self, old_State)

    def start_element(self, name, attrs, context):
        self.clearData()

    def end_element(self, name, context):
        if name == self.Tag:
            self.restoreState(context)
            context.setUnits(string.strip(self.getData()))


class WaveformTypeElementParser(XmlElementParser):
    """State for handling the WaveformType element"""

    Tag = "WaveformType"

    def __init__(self, old_State):
        XmlElementParser.__init__(self, old_State)

    def start_element(self, name, attrs, context):
        self.clearData()

    def end_element(self, name, context):
        if name == self.Tag:
            self.restoreState(context)
            if string.find(self.getData(), "Rhythm") >= 0:
                context.setRhythmFound(1)
                print("ECG %s object found." % self.getData())
            else:
                context.setRhythmFound(0)


class LeadDataElementParser(XmlElementParser):
    """State for handling the LeadData element"""

    Tag = "LeadData"

    def __init__(self, old_State):
        XmlElementParser.__init__(self, old_State)

    def start_element(self, name, attrs, context):
        self.clearData()
        if name == LeadIdElementParser.Tag:
            context.setState(LeadIdElementParser(self))
        if name == WaveformDataElementParser.Tag:
            context.setState(WaveformDataElementParser(self))
        if name == LeadUnitsPerBitElementParser.Tag:
            context.setState(LeadUnitsPerBitElementParser(self))
        if name == LeadUnitsElementParser.Tag:
            context.setState(LeadUnitsElementParser(self))

    def end_element(self, name, context):
        if name == self.Tag:
            self.restoreState(context)


class LeadIdElementParser(XmlElementParser):
    """State for handling the LeadID element"""

    Tag = "LeadID"

    def __init__(self, old_State):
        XmlElementParser.__init__(self, old_State)

    def start_element(self, name, attrs, context):
        self.clearData()

    def end_element(self, name, context):
        if name == self.Tag:
            self.restoreState(context)
            if context.found_Rhythm:
                sys.stdout.write("   Lead %2s found..." % self.getData())
                context.addLeadId(self.getData())


class WaveformDataElementParser(XmlElementParser):
    """State for handling the WaveformData element"""

    Tag = "WaveFormData"

    def __init__(self, old_State):
        XmlElementParser.__init__(self, old_State)

    def start_element(self, name, attrs, context):
        self.clearData()

    def end_element(self, name, context):
        if name == self.Tag:
            self.restoreState(context)
            if context.found_Rhythm:
                print("   Adding data for lead %2s." % context.lead_Id)
                context.addWaveformData(self.getData())


class MuseXmlParser:
    """This class is the parsing context in the object-oriented State pattern."""

    def __init__(self):
        self.ecg_Data = dict()
        self.ecg_Leads = list()
        self.__state = IdleParser()
        self.found_Rhythm = 0
        self.sample_Rate = 0
        self.adu_Gain = 1
        self.units = ""

    def setState(self, s):
        self.__state = s

    def getState(self):
        return self.__state

    def setSampleBase(self, text):
        if self.found_Rhythm:
            self.sample_Rate = int(text)

    def setAdu(self, gain):
        self.adu_Gain = gain

    def setUnits(self, units):
        self.units = units

    def setRhythmFound(self, v):
        self.found_Rhythm = v

    def addLeadId(self, id):
        self.lead_Id = id

    def addWaveformData(self, text):
        self.ecg_Data[self.lead_Id] = base64.b64decode(text)
        self.ecg_Leads.append(self.lead_Id)

    def start_element(self, name, attrs):
        """This function trackes the start elements found in the XML file with a
        simple state machine"""
        self.__state.start_element(name, attrs, self)

    def end_element(self, name):
        self.__state.end_element(name, self)

    def char_data(self, data):
        self.__state.char_data(data, self)

    def makeZcg(self):
        """This function converts the data read from the XML file into a ZCG buffer
        suitable for storage in binary format."""
        # All of the leads should have the same number of samples
        n = len(self.ecg_Data[self.ecg_Leads[0]])
        # We have 2 bytes per ECG sample, so make our buffer size n * DATAMUX
        self.zcg = array.array("d")
        # Verify that all of the independent leads are accounted for...
        for lead in INDEPENDENT_LEADS:
            if lead not in self.ecg_Leads:
                print("Error! The XML file is missing data for lead ", lead)
                sys.exit(-1)

        # Append the data into our huge ZCG buffer in the correct order
        for t in range(0, n, 2):
            for lead in self.ecg_Leads:
                sample = struct.unpack(
                    "h", self.ecg_Data[lead][t] + self.ecg_Data[lead][t + 1]
                )
                self.zcg.append(sample[0])

    def writeCSV(self, file_Name):
        """This function writes the ZCG buffer to a CSV file. All 12 or 15 leads
        are generated."""
        std_Leads = set(INDEPENDENT_LEADS)
        header = (
            "I",
            "II",
            "III",
            "aVR",
            "aVL",
            "aVF",
            "V1",
            "V2",
            "V3",
            "V4",
            "V5",
            "V6",
        )
        extra_Leads = std_Leads.symmetric_difference(set(self.ecg_Leads))
        # print "EXTRA LEADS: ", extra_Leads

        fd = open(file_Name, "wt")
        if fd:
            # write the header information
            for lead in header:
                fd.write("%s, " % lead)
            # write any extra leads
            for lead in self.ecg_Leads:
                if lead in extra_Leads:
                    fd.write("%s, " % lead)
            fd.write("\n")

            samples = dict()

            for i in range(0, len(self.zcg), len(self.ecg_Leads)):
                # The values in the ZCG buffer are stored in the same order
                # as the ecg leads are themselves...
                k = 0
                for lead in self.ecg_Leads:
                    samples[lead] = self.zcg[i + k]
                    k = k + 1
                # Output each sample, calculated and uncalcuated
                fd.write("%d, " % int(samples["I"] * self.adu_Gain))
                fd.write("%d, " % int(samples["II"] * self.adu_Gain))
                # II - I = III
                fd.write("%d, " % int((samples["II"] - samples["I"]) * self.adu_Gain))
                # aVR = -(I + II)/2
                fd.write(
                    "%d, " % int((-(samples["I"] + samples["II"]) / 2) * self.adu_Gain)
                )
                # aVL = I - II/2
                fd.write(
                    "%d, " % int((samples["I"] - samples["II"] / 2) * self.adu_Gain)
                )
                # aVF = II - I/2
                fd.write(
                    "%d, " % int((samples["II"] - samples["I"] / 2) * self.adu_Gain)
                )
                # output the precordial leads
                fd.write("%d, " % int(samples["V1"] * self.adu_Gain))
                fd.write("%d, " % int(samples["V2"] * self.adu_Gain))
                fd.write("%d, " % int(samples["V3"] * self.adu_Gain))
                fd.write("%d, " % int(samples["V4"] * self.adu_Gain))
                fd.write("%d, " % int(samples["V5"] * self.adu_Gain))
                fd.write("%d, " % int(samples["V6"] * self.adu_Gain))
                # output any extra leads
                for lead in self.ecg_Leads:
                    if lead in extra_Leads:
                        fd.write("%d, " % int(samples[lead] * self.adu_Gain))
                fd.write("\n")
        print(
            '\nCSV file ("%s") is generated, with %d columns of ECG signals'
            % (file_Name, len(header) + len(extra_Leads))
        )
        print("ECG sampling rate is %d Hz." % self.sample_Rate)
        # with open("sr.txt", "a") as f:
        #     f.write("%s:" % args[0][args[0].index(".")-2:args[0].index(".")])
        #     f.write("%s" % self.sample_Rate)
        #     f.write("\n")
        print("ECG stored in units of %s." % self.units)


###############################################################################
# Functions
###############################################################################
# 3 handler functions for the expat parser
def start_element(name, attrs):
    g_Parser.start_element(name, attrs)
    # print 'Start element:', name, attrs


def end_element(name):
    g_Parser.end_element(name)
    # print 'End element:', name


def char_data(data):
    g_Parser.char_data(data)


###############################################################################
# Main program
#
# The main script follows. The if __name__ business is necessary for the
# contents of a file to be used both as a module or as a program. It is
# also necessary if you use the 'pydoc' command to generate program
# documentation.
###############################################################################
if __name__ == "__main__":

    # defines for help
    VERSION = (
        "%%prog %s\nAn utility to extract an ECG rhythm strip from a MUSE(R) XML file\n%s"
        % (__version__, __copyright__)
    )
    USAGE = "%prog [-h|-w|-c] xml_ecg_file.xml"
    DESCRIPTION = """
This is an utility to extract an ECG rhythm strip from a MUSE(R) XML file. Copyright (C)
2009  Anthony D. Ricke. This program comes with ABSOLUTELY NO WARRANTY; for
details type `python musexmlex.py -w'. This is free software, and you are
welcome to redistribute it under certain conditions; type `python musexmlex.py
-c' for details.                                                                DISCLAIMER:
                                                                                
------------------------------------------------------------------------------
THIS IS NOT A MEDICAL DEVICE, NOR IS IT A GE HEALTHCARE PRODUCT. NEITHER THIS
TOOL, NOR ITS OUTPUT, CAN IT BE USED TO MAKE MEDICAL DIAGNOSIS OR TREATMENT.
------------------------------------------------------------------------------
"""

    # parse the options
    parser = optparse.OptionParser(
        usage=USAGE, version=VERSION, description=DESCRIPTION
    )
    parser.add_option(
        "-w",
        action="store_true",
        dest="disp_warranty",
        help="This option displays the warranty information for this open source program",
    )
    parser.add_option(
        "-c",
        action="store_true",
        dest="disp_GPL",
        help="This option displays the GNU General Public License, with its terms and conditions.",
    )
    (options, args) = parser.parse_args()

    if options.disp_warranty:
        print(WARRANTY)
        sys.exit(0)

    if options.disp_GPL:
        print(GNU_GPL)
        sys.exit(0)

    if len(args) != 1:
        parser.error("Invalid number of command-line parameters")

    g_Parser = MuseXmlParser()

    p = xml.parsers.expat.ParserCreate()

    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data

    print('Parsing XML file "%s"' % args[0])
    # Read the XML file and parse it
    p.ParseFile(open(args[0], "rb"))

    # convert the data into a ZCG buffer
    g_Parser.makeZcg()

    base_Name = os.path.splitext(os.path.basename(args[0]))[0]

    # Write the data to a .CSV file
    g_Parser.writeCSV(base_Name + ".csv")

    print(
        """
------------------------------------------------------------------------------
THIS IS NOT A MEDICAL DEVICE, NOR IS IT A GE HEALTHCARE PRODUCT. NEITHER THIS
TOOL, NOR ITS OUTPUT, CAN IT BE USED TO MAKE MEDICAL DIAGNOSIS OR TREATMENT.

                          NOT FOR PATIENT USE
                          
------------------------------------------------------------------------------
"""
    )

