# File: ROCCER_Algorithm.py
# Author(s): Willa Potosnak
# Created: July 30, 2020
# Description: Recreation of ROCCER (2004) algorithm by R.C. Prati and P. A. Flach
# Acknowledgements: R. C. Prati and P. A. Flach, “Roccer: an algorithm for rule learning based on roc analysis,” in Proc. of the 19th International Joint Conference on Artificial Intelligence, 2005, pp. 823–828
# Please cite the ROCCER paper referenced under 'Acknowledgements' and this code if the results from the code are openly disseminated 
# Notes: This is a working protype code



import pandas as pd
import numpy as np
import os
import re
import json


config = {'class_label': 'class'} # Change 'class' to data class label


def Find_IDs_in_Rules(Dataset, Rule_s):
    DSet = Dataset.copy()
    rule_s = Rule_s.copy() 
    IDX_fin = dict()
    
    for item_num, item in enumerate(rule_s):
        item_name = item_num+1
        
        if len(item) == 0:                                             # ROCCER initalizes decision list with an empty rule
            abstain_samples = sorted(DSet.index.values)
            IDX_fin['Rule {} IDs'.format(item_name)] = abstain_samples
                    
        else:
            rule_set_IDs = pd.Series(dtype='Int64')
            for rule in item: 
                IDX = pd.Series(dtype='Int64')
                
                for condition_feature, condition in rule.items():
                    first_val = re.findall('^[-9-9]*[0-9]+\.?[0-9]*[e]*[+]*[-]*[0-9]*[0-9]*', condition)
                    second_val = re.findall('[-9-9]*[0-9]+\.?[0-9]*[e]*[+]*[-]*[0-9]*[0-9]*$', condition)

                    if 'x=' in condition:
                        samples = DSet.loc[lambda x: DSet[condition_feature] == float(second_val[0])]
                        IDX = IDX.append(pd.Series(samples.index.values))

                    if '<=x' in condition:
                        samples = DSet.loc[lambda x: DSet[condition_feature] >= float(first_val[0])]
                        IDX = IDX.append(pd.Series(samples.index.values))

                    if ('<x' in condition) & ('<x<=' not in condition):
                        samples = DSet.loc[lambda x: DSet[condition_feature] > float(first_val[0])]
                        IDX = IDX.append(pd.Series(samples.index.values))

                    if ('x<=' in condition) & ('<x<=' not in condition):
                        samples = DSet.loc[lambda x: DSet[condition_feature] <= float(second_val[0])]
                        IDX = IDX.append(pd.Series(samples.index.values))

                    if '<x<=' in condition:
                        samples = DSet.loc[lambda x: (DSet[condition_feature] > float(first_val[0])) & (DSet[condition_feature] <= float(second_val[0]))]
                        IDX = IDX.append(pd.Series(samples.index.values))
                
                if IDX.empty == False: 
                    condition_IDs = IDX.value_counts() == len(rule)
                    rule_set_IDs = rule_set_IDs.append(pd.Series(condition_IDs[condition_IDs].index.values))

            if len(rule_set_IDs) != 0:
                item_IDs = sorted(rule_set_IDs.unique().tolist())
                IDX_fin['Rule {} IDs'.format(item_name)] = item_IDs
                
            else:
                item_IDs = []        #if no patients fall under item, add empty list  
                IDX_fin['Rule {} IDs'.format(item_name)] = item_IDs
    
            DSet.drop(index=rule_set_IDs, inplace=True) # Code works for finding individual rule IDs or Decision list item IDs. Individual rules must be presented in a list.
    return(IDX_fin)
    
    
    
    

def Sort_Rules_to_Present_to_ROCCER(Dataset, Rule_s):       # ROCCER sorts rules in Association rule set generated by RDP by Euclidean distance from the rule (FPR, TPR) to (0, 1) in the ROC space. Creates an initally ordered list
    DSet = Dataset.copy()
    Sorted_Rules = []
    Computed_E_Dist = dict()
    
    for rule in range(len(Rule_s)):    
        Covered_Samples = Find_IDs_in_Rules(DSet, [Rule_s[rule]])
        rule_fpr, rule_tpr = Get_Rule_FPR_TPR(DSet, Covered_Samples['Rule 1 IDs'])
        E_dist_from_0_1 = [np.sqrt((rule_fpr - 0)**2 + (rule_tpr - 1)**2)]
        Computed_E_Dist[rule] = E_dist_from_0_1

    Sort_Computed_E_Dist = dict(sorted(Computed_E_Dist.items(), key=lambda item: item[1])) # Sort dictionary items by increasing E-Distance. Top rules in initally ordered list should be closest to (0, 1).
    for key in Sort_Computed_E_Dist.keys():
        Sorted_Rules.append(Rule_s[key])
    return(Sorted_Rules)





def Get_Rule_FPR_TPR(Dataset, Covered_Samples):
    DSet = Dataset.copy()  
    pos_tot = len(DSet.loc[lambda x: DSet[config['class_label']] == 1])
    neg_tot = len(DSet.loc[lambda x: DSet[config['class_label']] == 0])
    
    CS_DSet = DSet.loc[Covered_Samples]
    FP = len(CS_DSet.loc[lambda CS_DSet: CS_DSet[config['class_label']] == 0])
    TP = len(CS_DSet.loc[lambda CS_DSet: CS_DSet[config['class_label']] == 1])
    FPR = FP/neg_tot
    TPR = TP/pos_tot
    return((FPR, TPR))




def Get_Line_Eqn(p1, p2):
    m = (p2[1]-p1[1])/(p2[0]-p1[0])
    b = p1[1] - m*(p1[0])
    return(m, b)




def ROCCER_Generate_Decision_List(Dataset, Rule_s):
    DSet = Dataset.copy()
    Decision_List = [[]]                                                                # Initalize decision list with default (empty) rule
    
    for rule in Rule_s:
        DSet_copy = DSet.copy()
        Point_Lower_Bound = (0, 0)                                                      # For each tested rule in the sorted rule list presented to ROCCER, start lower coordinate at (0, 0)
        
        DList_Top_Item = Decision_List[0]                                               # Start rule comparison with first item in the decision list and get upper FPR coordinate
        Top_Item_Covered_Samples = Find_IDs_in_Rules(DSet, [DList_Top_Item])
        Point_Upper_Bound = Get_Rule_FPR_TPR(DSet, Top_Item_Covered_Samples['Rule 1 IDs']) 
        
        rule_cover = Find_IDs_in_Rules(DSet, [rule])                                    # Iterate through sorted rule list presented to ROCCER 
        rule_point = Get_Rule_FPR_TPR(DSet, rule_cover['Rule 1 IDs'])
        
        Samples_Thus_Covered = []
        for item_idx in range(len(Decision_List)):
            if Point_Upper_Bound[0] - Point_Lower_Bound[0] == 0:                        # If FPR coordinate values are the same (vertical line), use higher TPR value as point upper bound
                TPR_point_compare = Point_Upper_Bound[1]
            else:
                m, b = Get_Line_Eqn(Point_Lower_Bound, Point_Upper_Bound)               # Generate line equation from lower bound point to upper bound point
                TPR_point_compare = m*rule_point[0] + b                                 # Find the upper bound TPR coordinate of this linear line at the tested rule FPR coordinate.
            
            if (rule_point[0] <= Point_Upper_Bound[0]) & (rule_point[1] > TPR_point_compare):       # If the tested rule FPR rate coordinate is below the upper bound FPR coordinate and the tested rule TPR rate coordinate is above the upper bound TPR coordinate,... 
                Decision_List.insert(item_idx, rule)                                                # ... then insert the rule into the deicison list at the specified decision list item index (before the compared dlist item)
                Decision_List = Check_for_Concavities_in_ROC_Hull(DSet, Decision_List, item_idx)    # If item inserted into decision list, check for concavities in ROC space
                break
            
            elif len(Decision_List[item_idx]) == 0:                                                 # If rule does NOT extend ROC convex hull when compared with the default (empty) rule, try next rule
                break
                
            elif item_idx == len(Decision_List)-1:                                                  # If there are NO upper bound coordinates beyond last (default) decision list item, test next rule in ordered list presented to ROCCER
                break
                
            else:
                Point_Lower_Bound = Point_Upper_Bound                                               # If tested rule does not extend ROC convex hull, remove samples covered by the decision list rule... 
                DList_samples_to_drop = Find_IDs_in_Rules(DSet_copy, [Decision_List[item_idx]])     # ...and re-test the rule against the next item in the decision list
                Samples_Covered = DList_samples_to_drop['Rule 1 IDs']
                Samples_Thus_Covered.extend(Samples_Covered)
                DSet_copy.drop(index=Samples_Covered, inplace=True)
                
                Next_Item_Covered_Samples = Find_IDs_in_Rules(DSet_copy, [Decision_List[item_idx+1]])    # Find next decision list item (FPR, TPR) coordinates
                Point_Upper_Bound = Get_Rule_FPR_TPR(DSet, Next_Item_Covered_Samples['Rule 1 IDs'] + Samples_Thus_Covered)
                
                updated_rule_cover = Find_IDs_in_Rules(DSet_copy, [rule])                                # Update the tested rule (FPR, TPR) coordinates
                if len(updated_rule_cover['Rule 1 IDs']) == 0: break                                     # If after updating the rule, it covers NO samples, than test the next rule in the ordered list presented to ROCCER
                rule_point = Get_Rule_FPR_TPR(DSet, updated_rule_cover['Rule 1 IDs'] + Samples_Thus_Covered)
    
    del Decision_List[-1]                                                                                # Remove default (empty) rule used to initialize the decision list
    return(Decision_List)





def Get_DList_ROC_Points(Dataset, Decision_List):                               # Find (FPR, TPR) coordinates for each item in the decision list
    DSet = Dataset.copy()
    DList_ROC_Points = []
    Samples_covered = Find_IDs_in_Rules(DSet, Decision_List) 
    Samples_Thus_Covered = []
    for num in range(1, len(Decision_List)+1): 
        Samples_Thus_Covered.extend(Samples_covered['Rule {} IDs'.format(num)])
        Points = Get_Rule_FPR_TPR(DSet, Samples_Thus_Covered)
        DList_ROC_Points.append(Points)
    return(DList_ROC_Points)





def Test_Concavity_Before_Item(Decision_List, DList_Points, Item_Insertion_Idx):     # Interpolate a line from the current inserted decision item  rule coordinate to the coordinate of the rule 2 prior to it.
    if Item_Insertion_Idx >= 1:                                                      # If the TPR coordinate a the rule prior to current inserted rule is less than the interpolated TPR coordinate, a concavity exists
        if Item_Insertion_Idx == 1:                                                  # If a concavity exists before the item insertion, create a disjoint rule of the current and prior items as one decision list item.
            Previous_2_Rule_Point = (0,0)
        else:
            Previous_2_Rule_Point = DList_Points[Item_Insertion_Idx-2]
        
        if DList_Points[Item_Insertion_Idx][0] - Previous_2_Rule_Point[0] == 0:
            TPR_point_compare = DList_Points[Item_Insertion_Idx][1]
        else:
            m, b = Get_Line_Eqn(Previous_2_Rule_Point, DList_Points[Item_Insertion_Idx])
            TPR_point_compare = m*DList_Points[Item_Insertion_Idx-1][0] + b
            
        if DList_Points[Item_Insertion_Idx-1][1] < TPR_point_compare:
            Decision_List[Item_Insertion_Idx-1] = Decision_List[Item_Insertion_Idx-1] + Decision_List[Item_Insertion_Idx]
            del Decision_List[Item_Insertion_Idx]
    return(Decision_List)





def Test_Concavity_After_Item(Decision_List, DList_Points, Item_Insertion_Idx):      # Interpolate a TPR coordinate from the current inserted decision item to the coordinate of 2 items after.
    if Item_Insertion_Idx <= len(Decision_List) - 3:                                 # If the TPR coordinate of the item directly after the inserted item coordinate is less that the interpolated TPR, remove the item directly after. 
        for j in range(Item_Insertion_Idx, len(Decision_List)):                      # Repeat interpolation for any other points following in the decision list to check for additional concavities
            if DList_Points[j+1] == (1, 1):                                          # Stop concavities check if either: 
                break                                                                # A concavity occurs and an item is removed OR...
            else:                                                                    # the next decision list item coordinate is the 2nd to last item coordinate in the decision list (item before default item)
                if DList_Points[j+2][0] - DList_Points[Item_Insertion_Idx][0] == 0:
                    TPR_point_compare = DList_Points[j+2][1]
                else:
                    m, b = Get_Line_Eqn(DList_Points[Item_Insertion_Idx], DList_Points[j+2])
                    TPR_point_compare = m*DList_Points[j+1][0] + b
                    
                if DList_Points[j+1][1] < TPR_point_compare:
                    del Decision_List[j+1]
                    break
    return(Decision_List)





def Check_for_Concavities_in_ROC_Hull(Dataset, Decision_List, Item_Insertion_Idx):
    if len(Decision_List) >= 3: 
        
        DList_ROC_Points = Get_DList_ROC_Points(Dataset, Decision_List)
        Decision_List = Test_Concavity_Before_Item(Decision_List, DList_ROC_Points, Item_Insertion_Idx)     # First, check concavities before rule item as updates to decision list based on this can affect concavities after rule item
        
        while 1:
            L_DList = len(Decision_List)  
            DList_ROC_Points = Get_DList_ROC_Points(Dataset, Decision_List)
            Decision_List = Test_Concavity_After_Item(Decision_List, DList_ROC_Points, Item_Insertion_Idx)  # Second, check concavities after rule item
            if L_DList == len(Decision_List):                                                               # Update ROC points if item deletion occurs and recheck for additional concavities after rule item
                break                                                                                       # Stop concavity check if all items after inserted items are check and no item or no more items are removed
    return(Decision_List)
    
    
    
    


# MAIN Command to run: 'Get_Roccer_Decision_List'. 
# Association_Rules.json must be a list of a list of dictionaries: [[str_feature: str_condition, str_feature: str_condition, ...], [str_feature: str_condition, str_feature: str_condition, ...], ...]

def Get_ROCCER_Decision_List(association_rules_dir, data_dir, dlist_file_dir):
    DSet = pd.read_csv(data_dir).copy()
    Association_Rules = json.load(open('{}/Association_Rules.json'.format(association_rules_dir), 'r'))
    
    Association_Rules_Ranked = Sort_Rules_to_Present_to_ROCCER(DSet, Association_Rules)
    Decision_List = ROCCER_Generate_Decision_List(DSet, Association_Rules_Ranked)
    
    JSON_DList_file = open('{}/Decision_List.json'.format(dlist_file_dir), 'w')
    json.dump(Decision_List, JSON_DList_file)
    JSON_DList_file.close()