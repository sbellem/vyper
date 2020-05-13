storedData: public(int128)

@public
def __init__(_x: int128):
  self.storedData = _x


@mpc
async def prog(secret_msg: uint256):
    msg = await secret_msg.open()
    return msg
