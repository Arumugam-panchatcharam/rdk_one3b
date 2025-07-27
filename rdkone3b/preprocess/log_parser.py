from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

import os

import logging
import json
import pandas as pd
import numpy as np

from rdkone3b.applications.config_loader import ConfigIndex, ConfigLoader

from rdkone3b.utils.constants import UPLOAD_DIRECTORY
from rdkone3b.utils import constants
from rdkone3b.preprocess.data_loader import FileDataLoader, DataLoaderConfig
from rdkone3b.preprocess.preprocessor import Preprocessor, PreprocessorConfig
from rdkone3b.preprocess.data_model import LogRecordObject

"""
config = TemplateMinerConfig()
config.load_default()
miner = TemplateMiner(config=config)

log_lines = [
    "INFO 2025-07-26 10:01:12 User login successful for user=alice",
    "INFO 2025-07-26 10:01:15 Fetching data for user=alice",
    "ERROR 2025-07-26 10:01:18 Cache miss, backend timeout"
]

parsed_logs = []
for line in log_lines:
    result = miner.add_log_message(line)
    parsed_logs.append(result["template_mined"])
"""

class LogParser():
    def __init__(self):
        self.drain_config = TemplateMinerConfig()
        #self.drain_config.load(config_filename=None)

        self.path = UPLOAD_DIRECTORY
        self.merged_logs_path = os.path.join(self.path, "merged_logs")

        self.config = None

        self._parsing_results = pd.DataFrame()
        self._attributes = None
        self._timestamp = None

    @property
    def parsing_results(self):
        return self._parsing_results

    @property
    def attributes(self):
        return self._attributes

    @property
    def log_patterns(self):
        if self._parsing_results.empty:
            return None
        return self._parsing_results[constants.PARSED_LOGLINE_NAME].unique()
    
    @property
    def result_table(self):
        return self.parsing_results
    
    def get_dynamic_parameter_list(self, log_pattern):
        """
        For a given log pattern, return the dynamic parameters.
        
        :param log_pattern: The input log pattern.
        :return: The parameter list with Values, valuecounts and position.
        """
        para_list = pd.DataFrame(None, columns=["position", "value_counts", "values"])
        if self._parsing_results.empty or not log_pattern:
            return para_list

        res = self._parsing_results
        parameters = res.loc[res[constants.PARSED_LOGLINE_NAME] == log_pattern][
            constants.PARAMETER_LIST_NAME
        ]

        para_list["values"] = pd.Series(
            pd.DataFrame(parameters.tolist()).T.values.tolist()
        )
        para_list["position"] = [
            "POSITION_{}".format(v) for v in para_list.index.values
        ]
        para_list["value_counts"] = [
            len(list(filter(None, v))) for v in para_list["values"]
        ]
        return para_list

    def recognize_parameter_entity(self, para_list):
        """
        Placeholder for log parameter entity recognization
        """
        pass

    def summarize_numeric_paramters(self, paras: list):
        """
        Placeholder for numeric parameter summarization
        """
        pass

    def find_log_pattern(self, logline: str, return_para_list: bool = True):
        """
        Find the log pattern for a given logline, return all dynamic parameters in this log pattern if needed.
        """
        log_pattern = None
        para_list = None
        if not self._parsing_results.empty:
            res = self._parsing_results.loc[
                self._parsing_results[constants.LOGLINE_NAME] == logline
            ]
            log_patterns = res[constants.PARSED_LOGLINE_NAME]
            if len(log_patterns) == 0:
                return None
            if len(log_patterns) == 1:
                log_pattern_index = log_patterns.index[0]
                log_pattern = log_patterns.iloc[log_pattern_index]
            else:
                logging.warning("multiple log pa†terns are found!")
                log_pattern_index = log_patterns.index[0]
                log_pattern = log_patterns.iloc[log_pattern_index]
            if return_para_list:
                para_list = self.get_parameter_list(log_pattern)

        return log_pattern, para_list
    
    def get_log_lines(self, log_pattern):
        """
        Give a log pattern, find all loglines with this pattern in parsed_results
        :param log_pattern: str: log pattern
        :return: pd.Series of loglines
        """
        df = self.result_table
        res = df[df["parsed_logline"] == log_pattern].drop(
            ["parameter_list", "parsed_logline"], axis=1
        )

        return res
    
    def summary_graph_df(self, attributes=[]):
        parsed_df = self.result_table

        if len(attributes) > 0:
            for attr in attributes:
                for k, v in attr.items():
                    parsed_df = parsed_df[parsed_df[k] == v]

        count_table = parsed_df["parsed_logline"].value_counts()

        scatter_df = pd.DataFrame(count_table)

        scatter_df.columns = ["counts"]

        scatter_df["ratio"] = scatter_df["counts"] * 1.0 / sum(scatter_df["counts"])
        scatter_df["order"] = np.array(range(scatter_df.shape[0]))

        return scatter_df
        
    def _load_config(self, filename):

        root_dir = os.path.dirname(os.path.abspath(__file__))
        config_list_path = os.path.join(root_dir, "../configs", "config_list.json")

        if os.path.exists(config_list_path):
            print(f"Loading config from {config_list_path}")
            self.config_index = ConfigIndex.load_from_file(config_list_path)
            if self.config_index:
                self.config_path = self.config_index.find_config_for_file(filename)
                if os.path.exists(self.config_path):
                    try:
                         with open(self.config_path, 'r') as f:
                            raw_data = json.load(f)
                    except FileNotFoundError:
                        print("Error: config.yaml not found.")
                    
                    self.config = ConfigLoader.from_dict(raw_data)
                    if self.config.data_loader_config:
                        self.config.data_loader_config = DataLoaderConfig.from_dict(
                            self.config.data_loader_config
                        )
                    if self.config.preprocessor_config:
                        self.config.preprocessor_config = PreprocessorConfig.from_dict(
                            self.config.preprocessor_config
                        )
                    print(f"Configuration loaded successfully from {self.config_path}")

    def _load_data(self, filename):
        if self.config is not None and self.config.data_loader_config is not None:
            data_loader_config = self.config.data_loader_config = DataLoaderConfig.from_dict(
                            self.config.data_loader_config
                        )
            fpath = os.path.join(self.merged_logs_path, filename)
            if os.path.exists(fpath):
                data_loader = FileDataLoader(self.path, data_loader_config)
                log_record_object = data_loader.load_data()
                return log_record_object
    
    def _preprocess(self, logrecord: LogRecordObject):
        logline = logrecord.body[constants.LOGLINE_NAME]

        # Preprocessor cleans the loglines
        preprocessor = Preprocessor(self.config.preprocessor_config)
        preprocessed_loglines, _ = preprocessor.clean_log(logline)

        return preprocessed_loglines
    
    def _parse(self, log_lines: pd.Series):
        """Parse log lines using TemplateMiner."""
        self.miner = TemplateMiner(config=self.drain_config)
        parsed_results = []

        for line in log_lines:
            result = self.miner.add_log_message(line)
            parsed_results.append(result["template_mined"])

        _parsing_results = pd.Series(parsed_results, index=log_lines.index)

        return _parsing_results
    
    @staticmethod
    def get_parameter_list(row):
        """
        Returns parameter list of the loglines.

        :param row: The row in dataframe as function input containing ['logline', 'parsed_logline'].
        :return: The list of dynamic parameters.
        """
        parameter_list = []
        if not isinstance(row.logline, str) or not isinstance(row.parsed_logline, str):
            return parameter_list
        ll = row.logline.split()
        for t in ll:
            t = t.strip()
            if not t or t in row.parsed_logline:
                continue
            parameter_list.append(t)
        return parameter_list
    
    def parse_logs(self, filename: str):
        
        """ Load configuration for specific logs"""
        self._load_config(filename)
        
        """ Load and preprocess log data """
        log_record_object = self._load_data(filename)
        if log_record_object is not None:
            """ extract loglines and attributes from LogRecordObject """
            preprocessed_loglines = self._preprocess(log_record_object)
        
        """ DRAIN3 input loglines"""
        parsed_loglines = self._parse(preprocessed_loglines.dropna())

        if preprocessed_loglines.name is not constants.LOGLINE_NAME:
            preprocessed_loglines.name = constants.LOGLINE_NAME
        parsed_loglines.name = constants.PARSED_LOGLINE_NAME
        parsed_results = pd.concat([preprocessed_loglines, parsed_loglines], axis=1)

        parsed_results[constants.PARAMETER_LIST_NAME] = parsed_results.apply(
            self.get_parameter_list, axis=1
        )
        self._parsing_results = parsed_results[
            [constants.PARSED_LOGLINE_NAME, constants.PARAMETER_LIST_NAME]
        ]

        self._parsing_results = self._parsing_results.join(log_record_object.body)

        if self._attributes is not None:
            self._parsing_results = self._parsing_results.join(self._attributes)

        if self._timestamp is not None:
            self._parsing_results = self._parsing_results.join(self._timestamp)

        return

    def get_attributes(self):
        return self._attributes

    def get_templates(self):
        return self.miner.get_templates()