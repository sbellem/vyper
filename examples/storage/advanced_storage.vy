#mpc Prog:
#    async def prog(ctx, msg_field_elem):
#        msg_share = ctx.Share(msg_field_elem)
#        opened_value = await msg_share.open()
#        opened_value_bytes = opened_value.value.to_bytes(32, "big")
#        msg = opened_value_bytes.decode().strip("\x00")
#        return msg

DataChange: event({_setter: indexed(address), _value: int128})
storedData: public(int128)

@public
def __init__(_x: int128):
  self.storedData = _x

@public
def set(_x: int128):
  assert _x >= 0, "No negative values"
  assert self.storedData < 100, "Storage is locked when 100 or more is stored"
  self.storedData = _x
  log.DataChange(msg.sender, _x)

@public
def reset():
  self.storedData = 0

#@mpc
#async def _prog(ctx: Mpc, msg_field_elem):
#    msg_share = ctx.Share(msg_field_elem)
#    opened_value = await msg_share.open()
#    opened_value_bytes = opened_value.value.to_bytes(32, "big")
#    msg = opened_value_bytes.decode().strip("\x00")
#    return msg

#@mpc
#async def prog(secret_msg: uint256):
#    msg = await secret_msg.open()
#    return msg
