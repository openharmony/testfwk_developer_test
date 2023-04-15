import os
import sys

current_path = os.path.abspath(os.path.dirname(__name__))
sys.path.append(os.path.join(current_path, ".."))
from localCoverage.resident_service.public_method import get_config_ip, get_sn_list
from localCoverage.utils import get_product_name, hdc_command, tree_find_file_endswith, json_parse, logger

root_path = current_path.split("/test/testfwk/developer_test")[0]
out_path = os.path.join(root_path, "out", get_product_name(root_path))
developer_path = os.path.join(root_path, "test", "testfwk", "developer_test")
device_ip, device_port, device_sn_strs = get_config_ip(os.path.join(developer_path, "config", "user_config.xml"))
if not device_port:
    device_port = "8710"
device_sn_list = device_sn_strs.split(";")
if not device_sn_list:
    device_sn_list = get_sn_list("hdc -s {}:{} list targets".format(device_ip, device_port))


def find_part_so_dest_path(testpart: str) -> str:
    parts_info_json = os.path.join(out_path, "build_configs", "parts_info", "parts_path_info.json")
    if not os.path.exists(parts_info_json):
        logger("{} not exists.".format(parts_info_json), "ERROR")
        return ""
    json_obj = json_parse(parts_info_json)
    if json_obj:
        if testpart not in json_obj:
            logger("{} part not exist in {}.".format(testpart, parts_info_json), "ERROR")
            return ""
        path = os.path.join(out_path, "obj", json_obj[testpart])
        return path

    return ""

def find_subsystem_so_dest_path(subsystem: str) -> list:
    subsystem_config_json = os.path.join(out_path, "build_configs", "subsystem_info", "subsystem_build_config.json")
    if not os.path.exists(subsystem_config_json):
        logger("{} not exists.".format(subsystem_config_json), "ERROR")
        return []

    json_obj = json_parse(subsystem_config_json)
    if json_obj:
        if subsystem not in json_obj["subsystem"]:
            logger("{} not exist in subsystem_build_config.json".format(subsystem), "ERROR")
            return []
        if "path" not in json_obj["subsystem"][subsystem]:
            logger("{} no path in subsystem_build_config.json".format(subsystem), "ERROR")
            return []

        path = list()
        for s in json_obj["subsystem"][subsystem]["path"]:
                path.append(os.path.join(out_path, "obj", s))
        return path

    return []


def find_so_source_dest(path: str) -> dict:
    so_dict = dict()
    json_list = list()
    if not path:
        return {}

    json_list = tree_find_file_endswith(path, "_module_info.json", json_list)

    for j in json_list:
        json_obj = json_parse(j)
        if "source" not in json_obj or "dest" not in json_obj:
            logger("{} json file error.".format(j), "ERROR")
            return {}

        if json_obj["source"].endswith(".so"):
            so_dict[json_obj["source"]] = json_obj["dest"]

    return so_dict


def push_coverage_so(so_dict: dict):
    if not so_dict:
        logger("No coverage so to push.", "INFO")
        return
    for device in device_sn_list:
        cmd = "shell mount -o rw,remount /"
        hdc_command(device_ip, device_port, device, cmd)
        for source_path, dest_paths in so_dict.items():
            full_source = os.path.join(out_path, source_path)
            if os.path.exists(full_source):
                for dest_path in dest_paths:
                    full_dest = os.path.join("/", dest_path)
                    command = "file send {} {}".format(full_source, full_dest)

                    hdc_command(device_ip, device_port, device, command)
            else:
                logger("{} not exist.".format(full_source), "ERROR")


if __name__ == "__main__":
    subsystem_list, testpart_list = [], []
    param = sys.argv[1]
    if param.split("=")[0] == "testpart":
        testpart_list = param.split("=")[1].lstrip("[").rstrip("]").split(",")
    else:
        subsystem_list = param.split("=")[1].lstrip("[").rstrip("]").split(",")

    if subsystem_list:
        for subsystem in subsystem_list:
            json_path_list = find_subsystem_so_dest_path(subsystem)
            for json_path in json_path_list:
                source_dest_dict = find_so_source_dest(json_path)
                push_coverage_so(source_dest_dict)
    elif testpart_list:
        for testpart in testpart_list:
            json_path_list = find_part_so_dest_path(testpart)
            source_dest_dict = find_so_source_dest(json_path_list)
            push_coverage_so(source_dest_dict)
    else:
        logger("No subsystem or partname input, no need to push coverage so.", "INFO")
        exit(0)
