"""
-*- coding:utf-8 -*-
Author: zhang yongquan
Email: zhyongquan@gmail.com
GitHub: https://github.com/zhyongquan

Modifications contributed by motthomasn <motthomasn@gmail.com>:
211123      Corrected self.name in axis.show()
            Corrected spelling of axises to axes
            added GROUPED_CURVE & GROUPED_MAP types to dcminfo.keywords and dcminfo.read
            Corrected type VAL_BLK to VALUE in calibration.show
            Changed calibration.show 3d plot cmap from rainbow to jet and added black edge colour. Personal preference
            Added grid lines calibration.show 2d plots
            Replaced line 263 self.calibrations[cal.name] = cal with self.addcalibration(cal)
            Added handling for shared axes at end of dcminfo.read
            Note: Axes are currently stored as cal objects, not axis objects
"""

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import re


class function:
    name = ""
    description = ""
    line_start = 0
    line_end = 0

    def __init__(self, name):
        self.name = name

    def tojason(self):
        return ""

    def show(self):
        return

    def __str__(self):
        str = "name={0}, description={1}".format(self.name, self.description) \
              + "\nline_start={0}, line_end={1}".format(self.line_start, self.line_end)
        return str


class calobject(function):
    type = ""
    unit = ""
    value = []

    def __init__(self, name):
        super().__init__(name)
        self.value = []  # clear value for new instance

    def getlabel(self, axis, name, unit):
        if len(name) > 0 and len(unit) > 0:
            return "{0}({1})".format(name, unit)
        elif len(name) > 0:
            return name
        elif len(unit) > 0:
            return "{0}({1})".format(axis, unit)
        else:
            return axis

    def __str__(self):
        str = super().__str__() \
              + "\ntype={0}, unit={1}".format(self.type, self.unit) \
              + "\nvalue=\n" + self.value.__str__()
        return str


class axis(calobject):

    def show(self):
        x = range(0, len(self.value) - 1, 1)
        plt.plot(x, self.value, marker='o')
        plt.title(self.name)
        plt.xlabel(self.getlabel("x", "", ""))
        plt.ylabel(self.getlabel("y", self.name, self.unit))
        # for i in range(0, len(self.value) - 1):
        #     plt.text(i, self.value[i], "{0},{1}".format(i, self.value[i]))
        plt.show()


class calibration(calobject):
    x = axis("")
    y = axis("")

    def __init__(self, name):
        super().__init__(name)
        self.x = axis("")
        self.y = axis("")

    def show(self):
        if self.type == "CURVE" or self.type == "GROUPED_CURVE" or self.type == "MAP" or self.type == "GROUPED_MAP" or self.type == "VALUE":
            if self.type == "CURVE" or self.type == "GROUPED_CURVE":
                plt.plot(self.x.value, self.value, marker='o')
                plt.title(self.name)
                plt.xlabel(self.getlabel("x", self.x.name, self.x.unit))
                plt.ylabel(self.getlabel("y", self.name, self.unit))
                plt.grid(b=True, which='major', axis='both')
                # for i in range(0, len(self.value)):
                #     plt.text(self.x.value[i], self.value[i], "{0},{1}".format(self.x.value[i], self.value[i]))
                plt.show()
            elif self.type == "MAP" or self.type == "GROUPED_MAP":
                X, Y = np.meshgrid(self.y.value, self.x.value)  # exchange for plot
                nx = len(self.x.value)
                ny = len(self.y.value)
                Z = np.zeros((nx, ny))
                for i in range(0, nx):
                    for j in range(0, ny):
                        Z[i, j] = self.value[j][i]
                fig = plt.figure()
                ax = Axes3D(fig)
                p = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap='jet', edgecolor='k')
                fig.colorbar(p)
                ax.set_title(self.name)
                ax.set_ylabel(self.getlabel("x", self.x.name, self.x.unit))  # exchange for plot
                ax.set_xlabel(self.getlabel("y", self.y.name, self.y.unit))  # exchange for plot
                ax.set_zlabel(self.getlabel("z", self.name, self.unit))
                plt.show()
            elif self.type == "VALUE":
                if not isDigit(self.value[0]):
                    return
                x = range(0, len(self.value) - 1, 1)
                plt.title(self.name)
                plt.plot(x, self.value, marker='o')
                plt.xlabel(self.getlabel("x", "", ""))
                plt.ylabel(self.getlabel("y", self.name, self.unit))
                # for i in range(0, len(self.value)):
                #     plt.text(i, self.value[i], "{0},{1}".format(i, self.value[i]))
                plt.show()

    def __str__(self):
        str = super().__str__()
        if len(self.x.value) > 0:
            str = str + "\naxis x\n" + self.x.__str__()
        if len(self.y.value) > 0:
            str = str + "\naxis y\n" + self.y.__str__()
        return str


class dcminfo:
    file_content = "KONSERVIERUNG_FORMAT 2.0"
    comment_indicator = '*'
    string_delimiter = '"'
    functions = {}
    calibrations = {}
    axes = {}
    calobjects = {"functions": functions, 
                  "calibrations": calibrations, 
                  "axes": axes}
    line_count = 0
    regex = r"(\"[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*\")|(?:[^\\ \t]+)"
    keywords = {"FESTWERT": "VALUE", 
                "KENNLINIE": "CURVE",
                "GRUPPENKENNLINIE": "GROUPED_CURVE",
                "KENNFELD": "MAP",
                "GRUPPENKENNFELD": "GROUPED_MAP",
                "STUETZSTELLENVERTEILUNG": "SHARED_AXIS"}

    def __init__(self):
        self.functions = {}
        self.calibrations = {}
        self.axes = {}
        self.calobjects = {"function": self.functions, 
                           "calibration": self.calibrations, 
                           "axis": self.axes}
        return

    def addfunction(self, fun):
        # if not fun.name in self.functions.keys():
        self.functions[fun.name] = fun

    def addcalibration(self, cal):
        # if not cal.name in self.calibrations.keys():
        self.calibrations[cal.name] = cal

    def addaxis(self, ax):
        # if not ax.name in self.axes.keys():
        self.axes[ax.name] = ax
        # for cal in self.calibrations:
        #     if cal.x.name == ax.name:
        #         cal.x = ax
        #     if cal.y.name == ax.name:
        #         cal.y = ax

    def getcalobject(self, type, name):
        if type in self.calobjects.keys() and name in self.calobjects[type].keys():
            return self.calobjects[type][name]
        else:
            return None

    def split(self, line):
        matches = re.finditer(self.regex, line, re.MULTILINE)
        txt = {}
        for matchNum, match in enumerate(matches, start=1):
            txt[matchNum] = match.group().strip('"')
        return txt

    def read(self, dcmfile):
        self.functions.clear()
        self.calibrations.clear()
        self.axes.clear()
        line_count = 0
        with open(dcmfile, 'r') as file:
            # first line: Description Header
            line = file.readline()
            line_count = 1
            cal = calibration("")
            y_value = []
            while True:
                line = file.readline()
                line_count = line_count + 1
                if not line:
                    break
                line = line.strip()
                if len(line) == 0 or line.startswith(self.comment_indicator):
                    continue
                else:
                    txt = self.split(line)
                    if txt[1] == "FKT":
                        # function
                        fun = function(txt[2])
                        fun.description = txt[4]
                        fun.line_start = line_count
                        fun.line_end = line_count
                        self.addfunction(fun)
                    elif txt[1] in self.keywords.keys():
                        # calibration block
                        cal = calibration(txt[2])
                        cal.type = self.keywords[txt[1]]
                        cal.line_start = line_count
                    elif txt[1] == "LANGNAME":
                        cal.description = txt[2]
                    elif txt[1] == "FUNKTION":
                        cal.fun = txt[2]
                    elif txt[1] == "EINHEIT_X":
                        cal.x.unit = txt[2]
                    elif txt[1] == "EINHEIT_Y":
                        cal.y.unit = txt[2]
                    elif txt[1] == "EINHEIT_W":
                        cal.unit = txt[2]
                    elif txt[1] == "ST/X":
                        for i in range(2, len(txt) + 1):
                            cal.x.value.append(float(txt[i]))
                    elif txt[1] == "ST/Y":
                        cal.y.value.append(float(txt[2]))
                        if len(y_value) > 0:
                            cal.value.append(y_value)
                            y_value = []
                    elif txt[1] == "WERT":
                        if cal.type == "VALUE":
                            cal.value.append(float(txt[2]))
                        elif ( cal.type == "CURVE" ) | ( cal.type == "GROUPED_CURVE" ):
                            for i in range(2, len(txt) + 1):
                                cal.value.append(float(txt[i]))
                        elif ( cal.type == "MAP" ) | ( cal.type == "GROUPED_MAP" ):
                            for i in range(2, len(txt) + 1):
                                y_value.append(float(txt[i]))
                    elif txt[1] == "END":
                        if len(y_value) > 0:
                            cal.value.append(y_value)
                            y_value = []
                        cal.line_end = line_count
                        if cal.type == "SHARED_AXIS":
                            self.addaxis(cal)
                        else:
                            self.addcalibration(cal)

            print("find functions:{0}, calibrations:{1}, axes:{2}".format(len(self.functions), len(self.calibrations),
                                                                            len(self.axes)))
            self.line_count = line_count


def isDigit(x):
    try:
        float(x)
        return True
    except ValueError:
        return False
