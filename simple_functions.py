def get_asset():
    """
    Function that repeadetly asks for an asset, where ETH or BTC is a valid option
    (case insensitive)
    """
    valid = False
    while not valid:
        asset = input('Asset: ').upper()
        if asset in ["ETH", "BTC"]:
            valid = True
    return asset