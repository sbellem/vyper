mpc Prog:
    async def prog(ctx, msg_field_elem):
        msg_share = ctx.Share(msg_field_elem)
        opened_value = await msg_share.open()
        opened_value_bytes = opened_value.value.to_bytes(32, "big")
        msg = opened_value_bytes.decode().strip("\x00")
        return msg

storedData: public(int128)

@public
def __init__(_x: int128):
  self.storedData = _x


@mpc
async def prog(secret_msg: uint256):
    msg = await secret_msg.open()
    return msg
