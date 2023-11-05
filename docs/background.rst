OSGB - Background and extended description
==========================================

These notes are part of :py:mod:`osgb`, a Python implementation of
latitude and longitude co-ordinate conversion for England, Wales, and
Scotland based on formulae and data published by the Ordnance Survey of
Great Britain.

These modules will convert accurately between an OSGB national grid
reference, and coordinates given in latitude and longitude using the
WGS84 model.  This means that you can take latitude and longitude
readings from your GPS receiver, (or read them from Wikipedia, or Google
Earth, or your car's sat-nav), and use this module to convert them to an
accurate British National grid reference for use with one of the
Ordnance Survey's paper maps.  And *vice versa*, of course.

These notes explain some of the background and implementation details
that might help you get the most out of them.

The algorithms and theory for these conversion routines are all from *A Guide
to Coordinate Systems in Great Britain* published by the OSGB, April 1999
(Revised 2018) and available from the `Ordnance Survey website
<https://www.ordnancesurvey.co.uk/>`_.  (You will have to hunt about for it, as
they keep moving it, but try their search function).  You may also like to read
some of the other introductory material there.  Should you be hoping to adapt
this code to your own custom Mercator projection, you will find the paper
called *Surveying with the National GPS Network*, especially useful.

Coordinates and ellipsoid models
--------------------------------

This section explains the fundamental problems of mapping a spherical
earth onto a flat piece of paper (or computer screen).  A basic
understanding of this material will help you use these routines more
effectively.  It will also provide you with a good store of ammunition
if you ever get into an argument with someone from the Flat Earth
Society.

It is a direct consequence of Newton's law of universal gravitation (and
in particular the bit that states that the gravitational attraction
between two objects varies inversely as the square of the distance
between them) that all planets are roughly spherical;  if they were any
other shape gravity would tend to pull them into a sphere.  On the other
hand, most useful surfaces for displaying large scale maps (such as
pieces of paper or screens) are flat.  Therefore the fundamental problem
in making a map of the earth is that the curved surface being mapped
must be distorted at least slightly in order to get it to fit onto a
flat map.

This module sets out to solve the corresponding problem of converting
latitude and longitude coordinates (designed for a spherical surface) to
and from a rectangular grid (for a flat surface).  A spherical
projection is a fairly simple but tedious bit of trigonometry, but the
problem is complicated by the fact that the earth is not quite a sphere.
Because our planet spins about a vertical axis, it tends to bulge out
slightly in the middle, so it is more of an oblate spheroid (or
ellipsoid) than a sphere.  This makes the arithmetic even more tedious,
but the real problem is that the earth is not a regular ellipsoid
either; it is an irregular lump that closely resembles an ellipsoid and
which is constantly (if slowly) being rearranged by plate tectonics.  So
the best we can do is to pick an imaginary regular ellipsoid that
provides a good fit for the region of the earth that we are interested
in mapping.

An ellipsoid model is defined by a series of numbers:  the major and
minor semi-axes of the solid, and a ratio between them called the
flattening. There are four ellipsoid models that are relevant to the UK:


OSGB36
    The OSGB36 ellipsoid is a revision of work begun by George Airy the
    Astronomer Royal in 1830, when the OS first undertook to make a series of
    maps that covered the entire country.  It provides a good fit for most of
    the British Isles.

EDM50
    The European standard ellipsoid is a compromise to get a good fit for most
    of Western Europe.  This is not used by these modules.

WGS84
    As part of the development of the GPS network by the American military in
    the 1980s a new world-wide ellipsoid called WGS84 was defined.  This fits
    most populated regions of the world reasonably well. (Technically the
    ellipsoid is called GRS80, and WGS84 refers to the whole World Geodetic
    System that is based on it, plus some very nerdy modifications, but for the
    purposes of this module it's just a label).

ETRS89
    The European Terrestrial Reference System is also based on GRS80, and for
    our purposes is identical to WGS84.  The technical difference is that in
    the ETRS89 system assumes that the Eurasian tectonic plate is the
    reference, whereas WGS84 assumes that the American plate is the reference.
    But this makes no practical difference whatsoever for the use of these
    modules.

The latitude and longitude marked on OS maps printed before 2015 are given in
the OSGB36 model.  The latitude and longitude you read from your GPS device, or
from Wikipedia, or Google Earth are in the WGS84 model.  So in the OSGB36
model, the point with latitude 51.4778 and longitude zero is on the prime
meridian line in the courtyard of the Royal Observatory in Greenwich, but the
point with the same coordinates in the WGS84 model is about 120 metres away to
the south-east, in the park.

In these modules the shape used for the projection of latitude and
longitude onto the grid is WGS84 unless you specifically set it to use
OSGB36.

The British National Grid and OSTN02 / OSTN15
---------------------------------------------

A Mercator grid projection like the British National Grid is defined by
the five parameters defined as constants at the top of the module.

- True point of origin Latitude and Longitude = 49N, 2W

- False origin easting and northing = 400000, -100000

- Convergence factor = 0.9996012717

One consequence of the True Point of Origin of the British Grid being
set to 49N, 2W is that all the vertical grid lines are parallel
to the 2W meridian; you can see this on the appropriate OS maps (for
example Landranger sheet 184), or on the PDF picture supplied with this
package in the ``examples`` folder.  The effect of moving the False Point
of Origin to the far south west is to make all grid references positive.

Strictly speaking, grid references are given as the distance in metres
from the False Point of Origin, with the easting always given before the
northing.  For everyday use however, the OSGB suggest that grid
references need only to be given within the local 100km square as this
makes the numbers smaller.  For this purpose they divide Britain into a
series of 100km squares, each identified by a pair of letters:  TQ, SU,
ND, etc.  The grid of the big squares actually used is something like
this::

                                HP
                                HU
                             HY
                    NA NB NC ND
                    NF NG NH NJ NK
                    NL NM NN NO NP
                       NR NS NT NU
                       NW NX NY NZ OV
                          SC SD SE TA
                          SH SJ SK TF TG
                       SM SN SO SP TL TM
                       SR SS ST SU TQ TR
                    SV SW SX SY SZ TV

SW covers most of Cornwall, TQ London, HU the Shetlands, and there is one
tiny corner of a beach in Yorkshire that is in OV.  The system has the
neat feature that N and S are directly above each other, so that most Sx
squares are in the south and most Nx squares are in the north.  The
system logically extends far out in all directions; so square XA lies
south of SV and ME to the west of NA and so on.  But it becomes less
useful the further you go from the central meridian of 2W.

Within each of the large squares, we only need five-digit coordinates --- from
(0,0) to (99999,99999) --- to refer to a given square metre.  But general use
rarely demands such  precision, so the OSGB recommendation  is to use units of
100m (hectometres) so that we only need three digits for each easting and
northing --- (000,000) to (999,999).  If we combine the easting and northing we
get the familiar traditional six figure grid reference.  Each of these grid
references is repeated in each of the large 100km squares but this does not
usually matter for local use with a particular map.  Where it does matter, the
OS suggest that the six figure reference is prefixed with the identifier of the
large grid square to give a 'full national grid reference', such as TQ330800.
This system is described in the notes in the corner of every Landranger
1:50,000 scale map.

This system was originally devised for use on top of the OSGB36 model of
latitude and longitude, so the prime meridian used and the coordinates
of the true point of origin are all defined in that system.  However as
part of standardizing on an international GPS system, the OS have
redefined the grid as a rubber sheet transformation from WGS84.
There is no intrinsic merit to using one model or another, but there's
an obvious need to be consistent about which one you choose, and with
the growing ubiquity of GPS systems, it makes sense to standardize on
WGS84.

The grid remains the primary reference system for use with maps, but
the OS has always also printed a latitude and longitude 'graticule' around the
edges of the large scale sheets.  Traditionally these coordinates have been
given in the OSGB36 model, but since 2015 the OS has been printing revised
editions of Explorer and Landranger sheets with WGS84 coordinates instead.
The legend of my recently purchased copy of Explorer 311 has this paragraph under the
heading 'The National Grid Reference System'.

    Base map constructed on Transverse Mercator Projection, Airy Ellipsoid,
    OSGB (1936) Datum.  Vertical datum mean sea level. The latitude, longitude
    graticule overlay is on the ETRS89 datum and is compatible with the WGS84
    datum used by satellite navigation devices.

If your map does not have the last sentence you can assume that it shows OSGB36
latitude and longitude.  Of course, this change makes no difference to the grid
itself.

The differences between the OSGB36 and WGS84 models are only important if you
are working at a fairly small scale.  The average differences on the ground
vary from about -67 metres to + 124 meters depending on where you are in the
country::

    Square                 Easting difference           Northing difference
    --------------------   -------------------------    ------------------
                 HP                        109                          66
              HT HU                    100 106                      59  62
        HW HX HY                73  83  93                  51  48  47
     NA NB NC ND            61  65  81  89              40  39  38  40
     NF NG NH NJ NK         57  68  79  92  99          30  29  28  26  26
     NL NM NN NO            56  66  79  91              18  17  15  15
        NR NS NT NU             66  77  92 100               3   2   1   0
        NW NX NY NZ             70  77  92 103              -9  -8 -10 -13
           SC SD SE TA              77  93 104 112             -19 -22 -23 -24
           SH SJ SK TF TG           79  91 103 114 124         -35 -34 -35 -38 -40
        SM SN SO SP TL TM       72  80  90 101 113 122     -49 -47 -46 -46 -46 -47
           SS ST SU TQ TR           80  90 101 113 121         -57 -56 -57 -57 -59
        SW SX SY SZ TV          71  79  90 100 113         -67 -64 -62 -62 -62


The chart above shows the mean difference in each grid square.  A
positive easting difference means the WGS84 Lat/Lon is to the east of
OSGB36; a positive northing difference means it is to the north of
OSGB36.  At a scale of 1:50,000, 124 meters is 2.48 mm, and at 1:25,000
it is 4.96 mm, so the difference is readily visible if you compare new
and old editions of the same map sheet.

The transformation from WGS84 to OSGB36 published in 2002 was called OSTN02 and
consisted of a large data set that defined a three dimensional shift for each
square kilometre of the country.  This dataset was revised (apparently to give
a better fit) in 2015 and the revised dataset is called OSTN15.

To get from WGS84 latitude and longitude to the grid, you project from the
WGS84 ellipsoid to a pseudo-grid and then look up the relevant shifts from
OSTN15 and adjust the easting and northing accordingly to get coordinates in
the OSGB grid.  Going the other way is slightly more complicated as you have to
use an iterative approach to find the latitude and longitude that would give
you your grid coordinates.

It is also possible to use a three-dimensional shift and rotation called
a Helmert transformation to get an approximate conversion.  This
approach is used automatically by these modules for locations that are
undefined in OSTN15.

Modern GPS receivers can all display coordinates in the OS grid system.  You
just need to set the display units to be 'British National Grid' or whatever
similar name is used on your unit.  Most units display the coordinates as two
groups of five digits and a grid square identifier.  The units are metres
within the grid square.  You can do the same on your smart phone with an app,
such as “OS Locate” from the OSGB.  However you should note that your phone or
your consumer GPS unit will **not** have a copy of the whole of OSTN15 in it.
To show you an OSGB grid reference, your device will be using either a Helmert
transformation, or an even more approximate Molodenksy transformation to
translate from the WGS84 coordinates it is getting from the satellites.  Grid
references that you read from most consumer devices will +/- 5m at best.

Note that the OSGB (and therefore this module) does not cover the whole
of the British Isles, nor even the whole of the UK, in particular it
covers neither the Channel Islands nor Northern Ireland.  The coverage
that is included is essentially the same as the coverage provided by the
OSGB "Landranger" 1:50000 series maps.  The coverage of the OSTN02 data
set was slightly smaller, as the OS did not originally define the model for any
points more than about 2km off shore.  The main difference in OSTN15 is that
coverage is extended to the whole rectangle from grid point (0,0) to (700000,1250000),
although the accuracy far offshore should not be relied on more than about +/- 5m.

Implementation of OSTN shift data
---------------------------------

The OSTN15 is the definitive transformation from WGS84 coordinates to
the British National Grid.  It is published as a large text file giving
a set of corrections for each square kilometre of the country.  The OS
also publish an algorithm to use it which is described on their website.
Essentially you take WGS84 latitude and longitude coordinates and
project them into an (easting, northing) pair of coordinates for the
flat surface of your grid. You then look up the corrections for the four
corners of the relevant kilometre square and interpolate the exact
corrections needed for your spot in the square.  Adding these exact
corrections gives you an (easting, northing) pair in the British grid.

The distributed data also includes a vertical height correction as part
of the OSGM15 geoid module, but this is not used in this module, so it
is omitted from the module in order to save space.

The table of data supplied by the Ordnance Survey contains 876951 rows with
entries for each km intersection between (0,0) and (700000, 1250000).
It is included in compressed binary form with normalized numbers
as data files that are loaded at run time.

Accuracy, uncertainty, and speed
--------------------------------

This section explores the limits of accuracy and precision you can
expect from this software.

Accuracy of readings from GPS devices
.....................................

If you are converting readings taken from your own handheld GPS device, the
readings themselves will not be very accurate.  To convince yourself of this,
try taking your GPS on the same walk on different days and comparing the track:
you will see that the tracks do not coincide.  If you have two units take them
both and compare the tracks:  you will see that they do not coincide.

The accuracy of the readings you get will be affected by cloud cover,
tree cover, the exact positions of the satellites relative to you (which
are constantly changing as the earth rotates), how close you are to
sources of interference, like buildings or electricity installations,
not to mention the ambient temperature and the state of your
rechargeable batteries.

To get really accurate readings you have to invest in some serious
professional or military grade surveying equipment.

How big is 0.000001 of a degree?
................................

In the British Isles the distance along a meridian between two points
that are one degree of latitude apart is about 110 km or just under 70
miles. This is the distance as the crow flies from, say, Swindon to
Walsall.  So a tenth of a degree is about 11 km or 7 miles, a hundredth
is just over 1km, 0.001 is about 110m, 0.0001 about 11m and 0.00001 just
over 1 m.

If you think in minutes and seconds, then one minute is
about 1840 m (and it's no coincidence that this happens to be
approximately the same as 1 nautical mile).  One second is a bit over
30m, 0.1 seconds is about 3 m, and 0.0001 second is about 3mm::

         Degrees              Minutes             Seconds  * LATITUDE *
               1 = 110 km         1 = 1.8 km        1 = 30 m
             0.1 =  11 km       0.1 = 180 m       0.1 =  3 m
            0.01 = 1.1 km      0.01 =  18 m      0.01 = 30 cm
           0.001 = 110 m      0.001 =   2 m     0.001 =  3 cm
          0.0001 =  11 m     0.0001 = 20 cm    0.0001 =  3 mm
         0.00001 = 1.1 m    0.00001 =  2 cm
        0.000001 = 11 cm   0.000001 =  2 mm
       0.0000001 =  1 cm

Degrees of latitude get very slightly longer as you go further north but
not by much.  In contrast degrees of longitude, which represent the same
length on the ground as latitude at the equator, get significantly
smaller in northern latitudes.  In southern England one degree of
longitude represents about 70 km or 44 miles, in northern Scotland it's
less than 60 km or about 35 miles.  Scaling everything down means that
the fifth decimal place of a degree of longitude represents about
60-70cm on the ground::

       Degrees                Minutes            Seconds * LONGITUDE *
             1 = 60-70 km         1 = 1.0-1.2 km      1 = 17-20 m
           0.1 = 6-7 km         0.1 = 100-120 m     0.1 = 2 m
          0.01 = 600-700 m     0.01 = 10-12 m      0.01 = 20 cm
         0.001 = 60-70 m      0.001 = 1 m         0.001 = 2 cm
        0.0001 = 6-7 m       0.0001 = 10 cm      0.0001 = 2 mm
       0.00001 = 60-70 cm   0.00001 = 1 cm
      0.000001 = 6-7 cm

How accurate are the conversions?
.................................

The OS supply test data with OSTN15 that comes from various fixed
stations around the country and that form part of the definition of the
transformation.  If you look in the test files you can see
how it is used for testing these modules.

In all cases translating from the WGS84 coordinates to the national grid and
vice versa is accurate to the millimetre, so these modules are at least as
accurate as the OSGB software that produced the test data.

The main difference between the OSTN02 transformation and OSTN15 is that the
model fits the whole grid area better.  With OSTN02 the conversions were (very
slightly) less accurate for places west of 7W.  Translating from the given grid
coordinates to WGS84 latitude and longitude coordinates was accurate to 1mm for
all of England, Wales, Scotland and the Isle of Man, but 'round trip' testing
(by generating random grid references, converting them to WGS84 latitude and
longitude and then converting them back to grid easting and northing), showed
that beyond of 6W (that is in the Scilly Isles and the Hebrides), the error
creeps up to about 4mm if you go as far as St Kilda (at about 8.57W).  The new
OSTN15 numbers are all very slightly different, so that converting any given
latitude and longitude in WGS84 gives a grid reference that may be a few mm
different.  But OSTN15 no longer shows greater round trip errors in the far
west. The accuracy of round trip conversions is less than 1mm for all of the
OSGB test points in both directions.

Outside the rectangle covered by OSTN15, this module uses the small Helmert
transformation recommended by the OS.  The OS state that, with the parameters
they provide, this transformation will be accurate up to about +/-5 metres, in
the vicinity of the British Isles.

How fast are the conversions?
.............................

In general the answer to this question is "probably faster than you need", but if
you have read this far you might be interested in the results of my benchmarking.
The bench marking script is included with the module tests.
On my old 2011 Mac Mini I get this::

    Grid banger bench mark running under CPython 3.7.3 on Darwin-16.7.0-x86_64-i386-64bit
    ll_to_grid: 49141/s 0.0203 ms per call
    grid_to_ll: 15357/s 0.0651 ms per call

On the newer 2019 Macbook Pro I get::

    Grid banger bench mark running under CPython 3.9.13 on macOS-12.4-x86_64-i386-64bit
    ll_to_grid: 135829/s 0.00736 ms per call
    grid_to_ll: 38655/s 0.0259 ms per call

Python 3.11 on the same machine gives a further boost::

    Grid banger bench mark running under CPython 3.11.1 on macOS-13.1-x86_64-i386-64bit
    ll_to_grid: 169020/s 0.00592 ms per call
    grid_to_ll: 43709/s 0.0229 ms per call

And the new 2023 Mac Mini M2 machine is faster still::

    Grid banger bench mark running under CPython 3.11.6 on macOS-14.1-arm64-arm-64bit
    ll_to_grid: 291009/s 0.00344 ms per call
    grid_to_ll: 81063/s 0.0123 ms per call


Maps
----

The map data is described in the API details above, so this section adds
a bit more background. The first three series included are OS maps:

  A
    OS Landranger maps at 1:50000 scale;
  B
    OS Explorer maps at 1:25000;
  C
    the old OS One-Inch maps at 1:63360.

Landranger sheet 47 appears in the list of keys as ``A:47``, Explorer
sheet 161 as ``B:161``, and so on.  As of 2015, the Explorer series of
incorporates the Outdoor Leisure maps, so (for example) the two sheets
that make up the map 'Outdoor Leisure 1' appear as ``B:OL1E`` and
``B:OL1W``.

Thanks to the marketing department at the OS and their ongoing
re-branding exercise several Explorer sheets have been promoted to
Outdoor Leisure status.  So (for example) Explorer sheet 364 has
recently become 'Explorer sheet Outdoor Leisure 39'.  Maps like this are
listed with a combined name, thus: ``B:395/OL54``.

Many of the Explorer sheets are printed on both sides.  In these cases
each side is treated as a separate sheet and distinguished with
suffixes.  The pair of suffixes used for a map will either be N and S,
or E and W.  So for example there is no Explorer sheet ``B:271``, but you
will find sheets ``B:271N`` and ``B:271S``.  The suffixes are determined
automatically from the layout of the sides, so in a very few cases it
might not match what is printed on the sheet but it should still be
obvious which side is which.  Where the map has a combined name the
suffix only appears at the end. For example: ``B:386/OL49E`` and
``B:386/OL49W``.

Several sheets also have insets, for islands, like Lundy or The Scilly
Isles, or for promontories like Selsey Bill or Spurn Head.  Like the
sides, these insets are also treated as additional sheets (albeit rather
smaller).  They are named with an alphabetic suffix so Spurn Head is on
an inset on Explorer sheet 292 and this is labelled ``B:292.a``.  Where
there is more than one inset on a sheet, they are sorted in descending
order of size and labelled ``.a``, ``.b`` etc.  On some sheets the insets
overlap the area of the main sheet, but they are still treated as
separate map sheets.

Some maps have marginal extensions to include local features - these are
simply included in the definition of the main sheets.  There are,
therefore, many sheets that are not regular rectangles.  Nevertheless,
the module is able to work out when a point is covered by one of these
extensions.

