################################################################
#
#                   RFC TEST SUITE USING GUI CONFIG
#
# This script shows you how to run Xena 2544/2889/3918 
# configurations using xoa-core
# 
# The latest 2544/2889/3918 plugins are already included in rfc_lib/

# 1. The script first convert the Xena test suite GUI configuration 
# files (.v2544, .v2889, .v3918, .x2544, .x2889, .x3918) into .json, 
# which is used by the xoa-core.
# 
# 2. Then run the test configuration on the specified chassis given 
# by CHASSIS_IP.
# 
# 3. The script prints out the test data
# 
#
################################################################
from __future__ import annotations
import sys
from xoa_core import controller, types
import asyncio
import json
import csv
from pathlib import Path

# XOA Converter is an independent module and it needs to be installed via `pip install xoa-converter`
try:
    from xoa_converter.entry import converter
    from xoa_converter.types import TestSuiteType
except ImportError:
    print("XOA Converter is an independent module and it needs to be installed via `pip install -U xoa-converter`")
    sys.exit()

PROJECT_PATH = Path(__file__).parent
PLUGINS_PATH = PROJECT_PATH / "rfc_lib"

#---------------------------
# Global parameters
#---------------------------
GUI_CONFIG = PROJECT_PATH / "demo.v2544"
XOA_CONFIG = PROJECT_PATH / "demo.json"
# DATA_FILE = PROJECT_PATH / "demo.csv"
CHASSIS_IP = "10.165.136.70"


#---------------------------
# internal functions
#---------------------------
def normalize_json(data: dict) -> dict: 
    new_data = dict() 
    for key, value in data.items(): 
        if not isinstance(value, dict): 
            new_data[key] = value 
        else: 
            for k, v in value.items(): 
                new_data[key + "_" + k] = v 
    return new_data

def read_rfc_type(gui_config: Path) -> TestSuiteType:
    file_extension = Path(gui_config).suffix
    if file_extension == ".v2544" or file_extension == ".x2544":
        return TestSuiteType.RFC2544
    elif file_extension == ".v2889" or file_extension == ".x2889":
        return TestSuiteType.RFC2889
    else:
        return TestSuiteType.RFC3918
        

#---------------------------
# run_xoa_rfc
#---------------------------
async def run_xoa_rfc(chassis: str, plugin_path: Path, gui_config: Path) -> None:
    # Define your tester login credentials
    my_tester_credential = types.Credentials(
        product=types.EProductType.VALKYRIE,
        host=chassis
    )

    # Create a default instance of the controller class.
    ctrl = await controller.MainController()

    # Register the plugins folder.
    ctrl.register_lib(str(plugin_path))

    # Add tester credentials into teh controller. If already added, it will be ignored.
    # If you want to add a list of testers, you need to iterate through the list.
    await ctrl.add_tester(my_tester_credential)

    # Convert GUI config into XOA config and run.
    with open(gui_config, "r") as f:
        
        # get the rfc type from the filename
        rfc_type = read_rfc_type(gui_config)

        # get test suite information from the core's registration
        info = ctrl.get_test_suite_info(rfc_type.value)
        if not info:
            print("Test suite is not recognized.")
            return None

        # convert the GUI config file into XOA config file
        xoa_config = converter(rfc_type, f.read())

        # save new data in xoa json
        with open(XOA_CONFIG, "w") as f:
            f.write(xoa_config)

        # you can use the config file below to start the test
        xoa_config_json = json.loads(xoa_config)

        # Test suite name is received from call of c.get_available_test_suites()
        execution_id = ctrl.start_test_suite(rfc_type.value, xoa_config_json)

        # The example here only shows a print of test result data.
        async for msg in ctrl.listen_changes(execution_id, _filter={types.EMsgType.STATISTICS}):
            result_data = json.loads(msg.payload.json())
            print(result_data)
            # It is up to the user to decide how to process and store the test result data.
            # Different RFC test suite plugin has different test result data structure.
                        
    # By the next line, we prevent the script from being immediately
    # terminated as the test execution and subscription are non blockable, and they ran asynchronously,
    # await asyncio.Event().wait()

async def main():
    stop_event =asyncio.Event()
    try:
        await run_xoa_rfc(
            chassis=CHASSIS_IP,
            plugin_path=PLUGINS_PATH,
            gui_config=GUI_CONFIG,
        )
    except KeyboardInterrupt:
        stop_event.set()


if __name__=="__main__":
    asyncio.run(main())