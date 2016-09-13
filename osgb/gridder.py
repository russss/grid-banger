"""Parse and format OSGB grid reference strings

Toby Thurston -- 13 Sep 2016 
"""

import math
import re
import sys
from osgb.mapping import map_locker

__all__ = ['format_grid', 'parse_grid', 'sheet_list']

GRID_SQ_LETTERS               = 'VWXYZQRSTULMNOPFGHJKABCDE'
GRID_SIZE                     = int(math.sqrt(len(GRID_SQ_LETTERS)))
MINOR_GRID_SQ_SIZE            = 100000
MAJOR_GRID_SQ_SIZE            = GRID_SIZE * MINOR_GRID_SQ_SIZE
MAJOR_GRID_SQ_EASTING_OFFSET  = 2 * MAJOR_GRID_SQ_SIZE
MAJOR_GRID_SQ_NORTHING_OFFSET = 1 * MAJOR_GRID_SQ_SIZE
MAX_GRID_SIZE                 = MINOR_GRID_SQ_SIZE * len(GRID_SQ_LETTERS)


class GridderFailure(Exception):
    """Parent class for Gridder exceptions"""
    pass


class GridParseFailure(GridderFailure):
    """Parent class for parsing exceptions"""
    pass


class GridFormatFailure(GridderFailure):
    """Parent class for formatting exceptions"""
    pass


class GridGarbage(GridParseFailure):
    """Raised when no grid ref can be deduced from the string given.

    Attributes:
        input

    """
    def __init__(self,input):
        self.input = input

    def __str__(self):
        return "I can't read a grid reference from this -> {}".format(self.input)


class GridSheetMismatch(GridParseFailure):
    """Raised when grid ref given is not on sheet given

    Attributes:
        sheet
        easting
        northing

    """
    def __init__(self,sheet,easting, northing):
        self.sheet = sheet
        self.easting = easting
        self.northing = northing

    def __str__(self):
        return "Grid point ({},{}) is not on sheet {}".format(self.easting, self.northing, self.sheet)


class UndefinedSheet(GridParseFailure):
    """Raised when sheet given is not one we know

    Attributes:
        sheet

    """
    def __init__(self,sheet):
        self.sheet = sheet

    def __str__(self):
        return "Sheet {} is not known here.".format(self.sheet)


class FaultyForm(GridFormatFailure):
    """Raised when the form given to format_grid is unmatched.

    Attributes:
       form

    """
    def __init__(self, form):
        self.form = form

    def __str__(self):
        return "This form argument was not matched --> form='{}'".format(self.form)


class FarFarAway(GridFormatFailure):
    """Raised when grid reference is nowhere near GB.

    Attributes:
       northing
       easting
    """
    def __init__(self, easting, northing):
        self.easting = easting
        self.northing = northing

    def __str__(self):
        return "The spot with coordinates ({},{}) is too far from the OSGB grid".format(self.easting, self.northing)



def sheet_list(easting, northing, series='ABCHJ'):
    """Return a list of map sheets that show the (easting, northing) point given.

    The optional argument "series" controls which maps are included in the 
    list.  The default is to include maps from all defined series.

    >>> sheet_list(438710.908, 114792.248, series='AB')
    ['A:196', 'B:OL22E']

    Currently the series included are:

    A: OS Landranger 1:50000 maps
    B: OS Explorer 1:25000 maps (some of these are designated as `Outdoor Leisure' maps)
    C: OS Seventh Series One-Inch 1:63360 maps
    H: Harvey British Mountain maps - mainly at 1:40000
    J: Harvey Super Walker maps - mainly at 1:25000

    Note that the numbers returned for the Harvey maps have been invented
    for the purposes of this module.  They do not appear on the maps
    themselves; instead the maps have titles.  You can use the numbers
    returned as an index to the maps data to find the appropriate title.

    >>> sheet_list(314159, 271828)
    ['A:136', 'A:148', 'B:200E', 'B:214E', 'C:128']

    You can restrict the list to certain series.
    So if you only want Explorer maps use: series='B', and if you
    want only Explorers and Landrangers use: series='AB', and so on. 

    >>> sheet_list(651537, 313135, series='A')
    ['A:134']

    If the (easting, northing) pair is not covered by any map sheet you'll get 
    an empty list
    >>> sheet_list(0,0)
    []

    """

    sheets = list()
    for (k, m) in map_locker.items():
        if k[0] not in series:
            continue

        if m['bbox'][0][0] <= easting < m['bbox'][1][0]:
            if m['bbox'][0][1] <= northing < m['bbox'][1][1]:
                if 0 != _winding_number(easting, northing, m['polygon']):
                    sheets.append(k)

    return sorted(sheets)

# is $pt left of $a--$b?
def _is_left(x, y, a, b):
    return ( (b[0] - a[0]) * (y - a[1]) - (x - a[0]) * (b[1] - a[1]) )

# adapted from http://geomalgorithms.com/a03-_inclusion.html
def _winding_number(x, y, poly):
    w = 0
    for i in range(len(poly)-1):
        if poly[i][1] <= y:
            if poly[i+1][1] > y and _is_left(x, y, poly[i], poly[i+1]) > 0:
                w += 1
        else:
            if poly[i+1][1] <= y and _is_left(x, y, poly[i], poly[i+1]) < 0:
                w -= 1
    return w


def format_grid(easting, northing=None, form='SS EEE NNN', maps=None):
    """Formats an (easting, northing) pair into traditional grid reference.

    This routine formats an (easting, northing) pair into a traditional
    grid reference with two letters and two sets of three numbers, like this
    `SU 387 147'.  

    >>> format_grid(438710.908, 114792.248)
    'SU 387 147'

    If you want the individual components, apply split() to it.

    >>> format_grid(438710.908, 114792.248).split()
    ['SU', '387', '147']

    The format grid routine takes three optional keyword arguments to control the
    form of grid reference returned.  This should be a hash reference with
    one or more of the keys shown below (with the default values).

    >>> format_grid(438710.908, 114792.248, form='SS EEE NNN')
    'SU 387 147'
    >>> format_grid(438710.908, 114792.248, form='SS EEEEE NNNNN')
    'SU 38710 14792'

    Note that rather than being rounded, the easting and northing are truncated
    (as the OS system demands), so the grid reference refers to the lower left
    corner of the relevant square.  The system is described below the legend on
    all OS Landranger maps.

    An optional keyword argument "form" controls the format of the grid reference.  

    >>> format_grid(438710.908, 114792.248, form='SS')
    'SU'
    >>> format_grid(438710.908, 114792.248, form='SSEN')
    'SU31'
    >>> format_grid(438710.908, 114792.248, form='SSEENN')
    'SU3814'
    >>> format_grid(438710.908, 114792.248, form='SSEEENNN')
    'SU387147'
    >>> format_grid(438710.908, 114792.248, form='SSEEEENNNN')
    'SU38711479'
    >>> format_grid(438710.908, 114792.248, form='SSEEEEENNNNN')
    'SU3871014792'
    >>> format_grid(438710.908, 114792.248, form='SS EN')
    'SU 31'
    >>> format_grid(438710.908, 114792.248, form='SS EE NN')
    'SU 38 14'
    >>> format_grid(438710.908, 114792.248, form='SS EEE NNN')
    'SU 387 147'
    >>> format_grid(438710.908, 114792.248, form='SS EEEE NNNN')
    'SU 3871 1479'
    >>> format_grid(400010.908, 114792.248, form='SS EEEEE NNNNN')
    'SU 00010 14792'

    You can't leave out the SS, you can't have N before E, and there must be
    the same number of Es and Ns.

    There are two other special formats:

    >>> format_grid(438710.908, 114792.248, form='TRAD')
    'SU 387 147'
    >>> format_grid(438710.908, 114792.248, form='GPS')
    'SU 38710 14792'

    The format can be given as upper case or lower case or a mixture.  
    
    >>> format_grid(438710.908, 114792.248, form='trad')
    'SU 387 147'

    but in general the form argument must match "SS E* N*" (spaces optional)

    >>> format_grid(432800,250000, form='TT')
    Traceback (most recent call last):
    ...
    FaultyForm: This form argument was not matched --> form='TT'

    >>> format_grid(314159, 271828, form='SS')
    'SO'
    >>> format_grid(0, 0, form='SS')
    'SV'
    >>> format_grid(432800,1250000, form='SS')
    'HP'

    The arguments can be negative...

    >>> format_grid(-5,-5, form='SS')
    'WE'

    But must not be too far away from the grid...

    >>> format_grid(-1e12,-5)
    Traceback (most recent call last):
    ...
    FarFarAway: The spot with coordinates (-1000000000000.0,-5) is too far from the OSGB grid


    """
    if northing is None:
        (easting, northing) = easting
    
    e = easting + MAJOR_GRID_SQ_EASTING_OFFSET
    n = northing + MAJOR_GRID_SQ_NORTHING_OFFSET

    if 0 <= e <  MAX_GRID_SIZE and 0 <= n < MAX_GRID_SIZE:
        major_index = int(e/MAJOR_GRID_SQ_SIZE) + GRID_SIZE * int(n/MAJOR_GRID_SQ_SIZE)
        e = e % MAJOR_GRID_SQ_SIZE
        n = n % MAJOR_GRID_SQ_SIZE
        minor_index = int(e/MINOR_GRID_SQ_SIZE) + GRID_SIZE * int(n/MINOR_GRID_SQ_SIZE)
        sq = GRID_SQ_LETTERS[major_index] + GRID_SQ_LETTERS[minor_index]

    else:
        raise FarFarAway(easting, northing)

    e = int(easting  % MINOR_GRID_SQ_SIZE)
    n = int(northing % MINOR_GRID_SQ_SIZE)

    # special cases
    ff = form.upper()
    if ff == 'TRAD':
        ff = 'SS EEE NNN'
    elif ff == 'GPS':
        ff = 'SS EEEEE NNNNN'
    elif ff == 'SS':
        return sq

    m = re.match(r'S{1,2}(\s*)(E{1,5})(\s*)(N{1,5})', ff)
    if m is None:
        raise FaultyForm(form)

    (space_a, e_spec, space_b, n_spec) = m.group(1,2,3,4)
    e = int(e/10**(5-len(e_spec)))
    n = int(n/10**(5-len(n_spec)))

    return sq + space_a + '{0:0{1}d}'.format(e, len(e_spec)) + space_b + '{0:0{1}d}'.format(n, len(n_spec))

def parse_grid(*grid_elements, figs=3):
    """Parse a grid reference from a range of inputs.

    The parse_grid routine extracts a (easting, northing) pair from a
    string, or a list of arguments, representing a grid reference.  The pair
    returned are in units of metres from the false origin of the grid.

    The arguments should be in one of the following three forms

    •   A single string representing a grid reference

        >>> parse_grid("TA 123 678")
        (512300, 467800)

        >>> parse_grid("TA 12345 67890")
        (512345, 467890)

        You can also refer to 100km, 10km, 1km, or even 10m squares:

        >>> parse_grid('TA')
        (500000, 400000)

        >>> parse_grid('TA15')
        (510000, 450000)

        >>> parse_grid('TA 12 56')
        (512000, 456000)

        >>> parse_grid('TA 1234 5678')
        (512340, 456780)

        The spaces are optional in all cases.

        >>> parse_grid("TA123678")
        (512300, 467800)

        >>> parse_grid("TA1234567890")
        (512345, 467890)

        Here are some more extreme examples:

        St Marys lifeboat station
        >>> parse_grid('SV9055710820')
        (90557, 10820)

        Lerwick lifeboat station
        >>> parse_grid('HU4795841283')
        (447958, 1141283)

        At sea, off the Scillies
        >>> parse_grid('WE950950')
        (-5000, -5000)

        Note in the last one that we are "off" the grid proper.  This lets you work
        with "pseudo-grid-references" like these:
        
        St Peter Port the Channel Islands
        >>> parse_grid('XD 61191 50692')
        (361191, -49308)
        
        Rockall 
        >>> parse_grid('MC 03581 16564')
        (-296419, 916564)


     •  A two or three element list representing a grid reference

        >>> parse_grid('TA', 0, 0)
        (500000, 400000)
        >>> parse_grid('TA', 123, 678)
        (512300, 467800)
        >>> parse_grid('TA', 12345, 67890)
        (512345, 467890)
        >>> parse_grid('TA', '123 678')
        (512300, 467800)
        >>> parse_grid('TA', '12345 67890')
        (512345, 467890)
        >>> parse_grid('TA', '1234567890')
        (512345, 467890)

        Or even just two numbers (primarily included for testing purposes)
        >>> parse_grid(314159, 271828)
        (314159, 271828)

        If you are processing grid references from some external data source
        beware that if you use a list with bare numbers you may lose any leading
        zeros for grid references close to the SW corner of a grid square.  This
        can lead to some ambiguity.  Either make the numbers into strings to
        preserve the leading digits or supply a hash of options as a fourth
        argument with the `figs' option to define how many figures are supposed
        to be in each easting and northing.  Like this:

        >>> parse_grid('TA', 123, 8)
        (512300, 400800)
        >>> parse_grid('TA', 123, 81, figs=5)
        (500123, 400081)

        The default setting of figs is 3, which assumes you are using
        hectometres as in a traditional grid reference. The maximum is 5
        and the minimum is the length of the longer of easting or northing.

    •   A string or a list representing a map and a local grid reference, 
        corresponding to the following examples:

        Caesar's Camp
        >>> parse_grid('176/224711')
        (522400, 171100)

        >>> parse_grid('176,224,711')
        (522400, 171100)

        Charlbury Station
        >>> parse_grid('A:164/352194')
        (435200, 219400)

        map Chesters Bridge
        >>> parse_grid('B:OL43E/914701')
        (391400, 570100)

        map Chesters Bridge
        >>> parse_grid('B:OL43E 914 701')
        (391400, 570100)

        map 2-arg Chesters Bridge
        >>> parse_grid('B:OL43E','914701')
        (391400, 570100)

        map 3-arg Chesters Bridge
        >>> parse_grid('B:OL43E',914,701)
        (391400, 570100)

        Carfax
        >>> parse_grid(164,513,62)
        (451300, 206200)

        map with dual name
        >>> parse_grid('B:119/OL3/480103')
        (448000, 110300)

        inset on B:309
        >>> parse_grid('B:309S.a 26432 34013')
        (226432, 534013)

        3-arg, dual name
        >>> parse_grid('B:368/OL47W', 723, 112)
        (272300, 711200)

   A map sheet with a grid ref that does not actually coincide will raise a 
   GridSheetMismatch error

        >>> parse_grid('176/924011')
        Traceback (most recent call last):
        ...
        GridSheetMismatch: Grid point (592400,201100) is not on sheet A:176
   
   A map sheet that does not exist will raise an UndefinedSheet error

        >>> parse_grid('B:999/924011')
        Traceback (most recent call last):
        ...
        UndefinedSheet: Sheet B:999 is not known here.


    If there's no matching input then a GridGarbage error is raised.
        >>> parse_grid('Somewhere in London')
        Traceback (most recent call last):
        ...
        GridGarbage: I can't read a grid reference from this -> Somewhere in London


    """

    easting = 0
    northing = 0

    if len(grid_elements) == 3:
        sq, ee, nn = grid_elements
        figs = min(5,max(figs, len(str(ee)), len(str(nn))))
        s = '{0} {1:0{3}d} {2:0{3}d}'.format(sq, int(ee), int(nn), figs)
    else:
        s = ' '.join(str(x) for x in grid_elements)

    # normal case : TQ 123 456 etc
    offsets = _get_grid_square_offsets(s)
    if offsets is not None:
        if len(s) == 2: # ie s must have been a valid square
            return offsets

        en_tuple = _get_eastings_northings(s)
        if en_tuple is not None:
            return (en_tuple[0]+offsets[0], en_tuple[1]+offsets[1])
    
    # just a pair of numbers
    if len(grid_elements) == 2:
        if _is_number(grid_elements[0]):
            if _is_number(grid_elements[1]):
                return tuple(grid_elements)

    # sheet id instead of grid sq
    m = re.match(r'([A-Z0-9:./]+)\D+(\d+\D*\d+)$', s, re.IGNORECASE)
    if m is not None:

        sheet, numbers = m.group(1,2)

        # allow Landranger sheets with no prefix
        if 'A:' + sheet in map_locker:
            sheet = 'A:' + sheet

        if sheet in map_locker:
            map = map_locker[sheet] 
            ll_corner = map['bbox'][0]  
            (e, n) = _get_eastings_northings(numbers)
            easting  = ll_corner[0] + (e - ll_corner[0]) % MINOR_GRID_SQ_SIZE
            northing = ll_corner[1] + (n - ll_corner[1]) % MINOR_GRID_SQ_SIZE
            if 0 == _winding_number(easting, northing, map['polygon']):
                raise GridSheetMismatch(sheet,easting,northing)

            return (easting, northing)
        else:
            raise UndefinedSheet(sheet)

    raise GridGarbage(s)

def _is_number(s):
    """Is this a number I see before me?

    >>> _is_number(3.141529)
    True

    >>> _is_number("")
    False

    >>> _is_number("TA")
    False

    """

    try:
        float(s)
        return True
    except ValueError:
        return False


def _get_grid_square_offsets(sq):
    """Get (e,n) for ll corner of a grid square

    >>> _get_grid_square_offsets('SV')
    (0, 0)

    >>> _get_grid_square_offsets('TQ 345 452')
    (500000, 100000)

    """

    if len(sq) < 2:
        return None

    a = GRID_SQ_LETTERS.find(sq[0].upper())
    if a < 0:
        return None

    b = GRID_SQ_LETTERS.find(sq[1].upper())
    if b < 0:
        return None

    (Y, X) = divmod(a, GRID_SIZE)
    (y, x) = divmod(b, GRID_SIZE)

    return (
        MAJOR_GRID_SQ_SIZE * X - MAJOR_GRID_SQ_EASTING_OFFSET  + MINOR_GRID_SQ_SIZE * x,
        MAJOR_GRID_SQ_SIZE * Y - MAJOR_GRID_SQ_NORTHING_OFFSET + MINOR_GRID_SQ_SIZE * y
    )

def _get_eastings_northings(s):
    """Extract easting and northing from GR string.

    >>> _get_eastings_northings(' 12345 67890')
    (12345, 67890)
    >>> _get_eastings_northings(' 234 567')
    (23400, 56700)
    """
    t = re.findall(r'(\d+)',s)
    if len(t) == 2:
        (e,n) = t
    elif len(t) == 1:
        gr = t[0]
        f = len(gr)
        if f in [2,4,6,8,10]:
            f = int(f/2)
            e,n = (gr[:f], gr[f:])
        else:
            return None
    else:
        return None

    figs = min(5,max(len(e), len(n)))
    return( int(e)*10**(5-figs), int(n)*10**(5-figs) )


if __name__ == "__main__":
    import doctest
    doctest.testmod()