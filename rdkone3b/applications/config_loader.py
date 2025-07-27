#
# Copyright (c) 2023 Salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
#
#
import os
import json
from dataclasses import dataclass

from rdkone3b.utils.config_util import Config
from rdkone3b.preprocess.data_loader import DataLoaderConfig
#from rdkone3b.preprocess.log_parser import PreprocessorConfig
from typing import List, Optional, Tuple, Dict, Any

@dataclass
class ConfigEntry:
    name: str
    supported_config: str
    supported_files: List[str]

@dataclass
class ConfigIndex:
    supported_files: List[ConfigEntry]

    @staticmethod
    def load_from_file(index_path: str) -> 'ConfigIndex':
        with open(index_path, 'r') as f:
            raw_data = json.load(f)
        entries = [ConfigEntry(**entry) for entry in raw_data.get("supported_files", [])]
        return ConfigIndex(supported_files=entries)

    def find_config_for_file(self, filename: str) -> str:
        filename_base = os.path.basename(filename)

        for entry in self.supported_files:
            for supported_name in entry.supported_files:
                if supported_name.lower() in filename_base.lower():
                    return entry.supported_config
        raise ValueError(f"No config found for file: {filename}")

@dataclass
class ConfigLoader(Config):
    """config class for end to end workflow.
    
    :param data_loader_config: A config object for data loader.
    :param preprocessor_config: A config object for log preprocessor.
    """
    data_loader_config: object = None
    preprocessor_config: object = None

    @classmethod
    def from_dict(cls, config_dict):
        config = super(ConfigLoader, cls).from_dict(config_dict)

        if config.data_loader_config:
            config.data_loader_config = DataLoaderConfig.from_dict(
                config.data_loader_config
            )

        return config
