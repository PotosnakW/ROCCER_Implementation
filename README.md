# ROCCER_Implementation

Recreation of ROCCER (2004) algorithm by R. C. Prati and P. A. Flach

Acknowledgements: R. C. Prati and P. A. Flach, “Roccer: an algorithm for rule learning based on roc analysis,” in Proc. of the 19th International Joint Conference on Artificial Intelligence, 2005, pp. 823–828.

Please cite the ROCCER paper referenced under 'Acknowledgements' and this code if results using the code are openly disseminated

Notes: This is a working protype code

Important information:
- python 3.8
- Packages to install:
  - pandas==1.2.4
  - numpy==1.20.1
- Data must be organized in a csv file with samples for rows and variables for columns
- A separate rule generation algorithm (or rule association algorithm) is needed to first generate rules before applying ROCCER to generate the decision list as ROCCER is a rule selection algorithm
- Generated rules should be saved in a json file named 'Association_Rules.json'
- Association_Rules.json must be in the form of list of a list of dictionaries (example below):
    - [[{str_feature: str_condition}, {str_feature: str_condition}, ...], [{str_feature: str_condition}, {str_feature: str_condition}, ...], ...]
    - [[{'age': 'x>60'}, {'gender': 'x=1'}], [{'height': 60<x<=70}, ...], ...]


How to run the ROCCER implementation and generate a decision list:
1. change 'config = ...' to correspond to class label in data
2. Import ROCCER_Algorithm.py file and use 'Get_ROCCER_Decision_List' command
3. Decision list file named 'Decision_List.json' will be saved under the specified decision list directory after code is run


Variable descriptions for 'Get_ROCCER_Decision_List' command:
- association_rules_dir = association rules json file directory
- dset_dir = dataset directory
- dlist_file_dir = directory for ROCCER generated decision list json file
