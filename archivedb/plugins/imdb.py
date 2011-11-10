import re

class TitleParser:
    year_re = r"(19\d{2}|20[01]\d)"

    sources = ("HDDVD(Rip)?", "BluRay(Rip)?", "HDTV(Rip)?", "DVD", \
               "NTSC", "PAL", "R[1-5]")
    vcodecs = ("x264", "XviD", "DIVX")
    acodecs = ("DTS\d?", "AC3\d?", "DD\d?", "FLAC\d?")
    resolutions = ("1080[pi]", "720[pi]", "480[pi]")
    misc = ("iNTERNAL", "COMPLETE", "Extras", "Criterion", \
            "(UN)?RATED", "[2-4]in1", "S?CE")

    keywords = sources + vcodecs + acodecs + resolutions + misc

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

        keywords_re = r"[^a-z](" + keywords_re + r")[^a-z]"

        #print(keywords_re)

        name_split = re.split(keywords_re, self.s)
        if len(name_split) > 0: self.title = name_split[0].strip()
        else: self.title = None

        return(self.title, self.year)
        #print((movie, years[-1]))
