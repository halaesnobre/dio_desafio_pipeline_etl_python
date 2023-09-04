from file_processes import import_data_file
from order_nfe import get_nfe_process
from order_tracking_code import get_tracking_code_process
from order_tracking_status import get_tracking_status_process

import_data_file()

get_nfe_process()

get_tracking_code_process()

get_tracking_status_process()
