import asyncio
from xoa_driver import testers
from xoa_driver import modules
from xoa_driver import ports

async def my_awesome_script():
    tester = await testers.L23Tester(host="10.20.1.253", username="XOA", enable_logging=True)

    my_module = tester.modules.obtain(0)

    if isinstance(my_module, modules.ModuleChimera):
        return None # commands which used in this example are not supported by Chimera Module

    if my_module.is_reserved_by_me():
        await my_module.reservation.set_release()
    if not my_module.is_released():
        await my_module.reservation.set_relinquish()
    await my_module.reservation.set_reserve()

    my_port = my_module.ports.obtain(0)

    try:
        await my_port.eee.enable.set_off()
        await my_port.eee.mode.set_off()
    except Exception as e:
        print(e) # You decide how to handle the exception