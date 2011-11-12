import re

class TitleParser:
    year_re = r"(19\d{2}|20[01]\d)"

    sources = ("HD.?DVD(Rip)?", "Blu.?Ray(Rip)?", "[SH]DTV(Rip)?", "DVD(Rip)?",
               "BD(Rip)?", "VCD(Rip)?", "NTSC", "PAL", "R[1-5]")
    vcodecs = ("x264", "XviD", "DIVX", "AVC(.?HD)?", "VC.?1", "H.?264")
    acodecs = ("DTS\d?", "DTS.?HD\d?", "TrueHD\d?", "AC3\d?",
                "DD\d?", "FLAC\d?", "AAC\d?")
    resolutions = ("(1080|720|480)[pi]",)
    extensions = ("avi", "mkv", "mov", "mp4", "ogm")
    languages = ("(TRUE)?FRENCH", "GERMAN", "SPANISH", "CHINESE")
    misc = ("iNTERNAL", "COMPLETE", "Extras", "Criterion",
            "(UN)?RATED", "[2-4]in1", "[SCE]{2,3}", "MULTI")

    keywords = sources + vcodecs + acodecs + resolutions + \
                languages + extensions + misc

    def __init__(self, s):
        self.s = s
        self.title = None
        self.year = None

        self.parse()

    def get_title(self):
        return(self.title)

    def get_year(self):
        return(self.year)

    def _find_year(self):
        year_re = r"[^a-z]" + TitleParser.year_re + r"[^a-z]"
        years = re.findall(year_re, self.s)

        if len(years) > 0: self.year = int(years[-1])

    def parse(self):
        self._find_year()
        if self.year is not None: keywords_re = "|".join(
                                        __class__.keywords + (str(self.year),))
        else: keywords_re = "|".join(__class__.keywords + (__class__.year_re,))

        keywords_re = r"[^a-z](" + keywords_re + r")([^a-z]|$)"

        #print(keywords_re)

        name_split = re.split(keywords_re, self.s, re.I)
        if len(name_split) > 0: self.title = name_split[0].strip()
        else: self.title = None

        return(self.title, self.year)
        #print((movie, years[-1]))
