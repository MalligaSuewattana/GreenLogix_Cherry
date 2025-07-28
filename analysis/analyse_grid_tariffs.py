import fluvius_captar

# check what the grid tariffs are for the zone which Kronos is in, and for the different connection levels they could be subject to

fluvius_captar.load_grid_tariffs(region="imewo", type_grid="26-36kV post")
fluvius_captar.load_grid_tariffs(region="halle-vilvoorde", type_grid="1-26kV net")
