storedData: public(int128)

@public
def __init__(_x: int128):
  self.storedData = _x


#@mpc
#async def prog():
#    msg = await secret_msg.open()
#    return msg

#@mpc
#async def prog(ctx, *, field_element):
#    msg_share = ctx.Share(field_element)
#    opened_value = await msg_share.open()
#    opened_value_bytes = opened_value.value.to_bytes(32, "big")
#    msg = opened_value_bytes.decode().strip("\x00")
#    return msg

@mpc
def multiply(x, y):
    return x*y
