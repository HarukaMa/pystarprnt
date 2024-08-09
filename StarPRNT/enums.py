#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
from enum import Enum, auto


class Model(Enum):
    Unknown = auto()
    mPOP = auto()
    SM_L200 = auto()
    SM_L300 = auto()
    SM_S_T = auto()
    mC_Print3_G1 = auto()
    mC_Print2 = auto()
    TSP100 = auto()
    mC_Label3 = auto()
    mC_Print3_G2 = auto()

class UTF8Font(Enum):
    Japanese = auto()
    SimplifiedChinese = auto()
    TraditionalChinese = auto()
    Korean = auto()

class ImageAlignment(Enum):
    Left = auto()
    Center = auto()
    Right = auto()

class PrintSpeed(Enum):
    Fast = auto()
    Normal = auto()
    Slow = auto()

class PrintDensity(Enum):
    Standard = auto()
    Plus1 = auto()
    Plus2 = auto()
    Plus3 = auto()
    Plus4 = auto()
    Minus1 = auto()
    Minus2 = auto()
    Minus3 = auto()
    Low = auto()
    Medium = auto()
    High = auto()
    Special = auto()

class ReducedH(Enum):
    Disabled = auto()
    Enabled = auto()

class ReducedV(Enum):
    Disabled = auto()
    Half = auto()
    ThreeQuarters = auto()

class Font(Enum):
    A = auto()
    B = auto()
    C = auto()