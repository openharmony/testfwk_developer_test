import datetime
import xml.etree.ElementTree as ET
from xdevice import platform_logger

LOG = platform_logger("arkts_tdd_report_generator")

class ResultConstruction(object):
    def __init__(self):
        self.testsuite_summary = {}
        self.start_time = None
        self.end_time = None
        self.suite_file_name = None

    # 美化 XML 格式 (可选)
    def indent(self, elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def node_construction(self, suite_result_file):
        # 创建根元素
        testsuites = ET.Element("testsuites")
        testsuites.set("name", self.suite_file_name)
        testsuites.set("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        testsuites.set("time", str(float(self.testsuite_summary['taskconsuming']) / 1000))
        testsuites.set("errors", self.testsuite_summary['Error'])
        testsuites.set("disabled", '0')  # ?
        testsuites.set("failures", self.testsuite_summary['Failure'])
        testsuites.set("tests", self.testsuite_summary['Tests run'])
        testsuites.set("ignored", self.testsuite_summary['Ignore'])
        testsuites.set("unavailable", "0")  # ?
        testsuites.set("starttime", self.start_time)
        testsuites.set("endtime", self.end_time)
        testsuites.set("repeat", "1")  # ?
        testsuites.set("round", "1")  # ?
        testsuites.set("test_type", "OHJSUnitTest")

        for key, value in self.testsuite_summary.items():
            if type(value) is dict:
                testsuite = ET.SubElement(testsuites, "testsuite")
                case_detail = value['case_detail']
                fail_count = 0
                for detail in case_detail:
                    if detail['testcaseResult'] == 'fail':
                        fail_count += 1

                testsuite.set("name", key)
                testsuite.set("time", str(float(value['testsuite_consuming']) / 1000))
                testsuite.set("errors", "0")
                testsuite.set("disabled", "0")
                testsuite.set("failures", str(fail_count))
                testsuite.set("ignored", "0")
                testsuite.set("tests", value['testsuiteCaseNum'])
                testsuite.set("report", "")

                case_detail = value['case_detail']
                for detail in case_detail:
                    testcase = ET.SubElement(testsuite, "testcase")
                    testcase.set("name", detail['case_name'])
                    testcase.set("status", "run")
                    testcase.set("time", str(float(detail['testcaseConsuming']) / 1000))
                    testcase.set("classname", key)

                    if detail['testcaseResult'] is not None:
                        testcase.set("result", "completed")

                    testcase.set("level", "1")

                    if detail['testcaseResult'] == 'fail':
                        failure = ET.SubElement(testcase, "failure")
                        failure.set("message", detail['testcaseFailDetail'])
                        failure.set("type", "")
                        failure.text = detail['testcaseFailDetail']
        self.indent(testsuites)

        # 将 ElementTree 写入 XML 文件
        tree = ET.ElementTree(testsuites)
        tree.write(suite_result_file, encoding="UTF-8",
                   xml_declaration=True,
                   short_empty_elements=True)
        LOG.info(f"XML 文件已生成: {suite_result_file}")