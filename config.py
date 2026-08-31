"""Tuning constants shared by main.py and precompute_deviations.py.
Changing a value here changes both the live path and the precomputed
browse verdicts, so they cannot drift apart."""

BAND_LO, BAND_HI = 0.15, 0.85   # percentiles defining the "usual range"
MARGIN = 0.05                   # how far outside the band before flagging
MIN_COMPS = 5                   # fewer than this and no verdict is given
MIN_BLOCK_COMPS = 10            # block pool must reach this or fall back to area
MAX_DEVIATION = 1.0             # >100% off is a price typo more often than an outlier
MIN_PRICE_RATIO = 0.35   # below this, a "bargain" is nearly always bad data